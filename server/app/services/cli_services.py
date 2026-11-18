from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.services import auth_services
from core.config import settings
from core.errors import AppError
from core.models.cli_auth import CliAuthRequest
from core.models.user import User
from core.security import hash_token
from core.utils import ensure_utc, to_ms, utcnow

CLI_CLIENT = "cli"


def challenge_for(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def _status(request: CliAuthRequest) -> str:
    now = utcnow()
    expires_at = ensure_utc(request.expires_at)
    if expires_at is None or expires_at <= now:
        return "expired"
    if request.claimed_at is not None:
        return "claimed"
    if request.denied_at is not None:
        return "denied"
    if request.approved_at is not None:
        return "approved"
    return "pending"


def _by_code(db: Session, code: str) -> CliAuthRequest | None:
    return db.execute(
        select(CliAuthRequest).where(CliAuthRequest.code_hash == hash_token(code))
    ).scalar_one_or_none()


def _load_for_page(db: Session, code: str) -> CliAuthRequest:
    request = _by_code(db, code)
    if request is None:
        raise AppError(404, "This sign-in request is not valid.")
    return request


def create_request(
    db: Session,
    *,
    name: str,
    challenge: str,
) -> tuple[CliAuthRequest, str]:
    code = secrets.token_urlsafe(32)
    now = utcnow()
    request = CliAuthRequest(
        code_hash=hash_token(code),
        challenge=challenge,
        name=name.strip()[:64] or "Graphia CLI",
        created_at=now,
        expires_at=now + timedelta(seconds=settings.cli_auth_request_ttl_seconds),
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request, code


def request_status(db: Session, *, code: str) -> tuple[CliAuthRequest, str]:
    request = _load_for_page(db, code)
    return request, _status(request)


def approve(db: Session, *, code: str, user: User) -> CliAuthRequest:
    request = _load_for_page(db, code)
    status = _status(request)
    if status == "expired":
        raise AppError(410, "This sign-in request has expired. Run `graphia login` again.")
    if status in {"denied", "claimed"}:
        raise AppError(409, "This sign-in request is no longer available.")
    if request.approved_at is not None:
        if request.user_id != user.id:
            raise AppError(409, "This sign-in request belongs to another account.")
        return request

    request.user_id = user.id
    request.approved_at = utcnow()
    db.commit()
    db.refresh(request)
    return request


def deny(db: Session, *, code: str, user: User) -> CliAuthRequest:
    request = _load_for_page(db, code)
    status = _status(request)
    if status == "expired":
        raise AppError(410, "This sign-in request has expired. Run `graphia login` again.")
    if status == "claimed":
        raise AppError(409, "This sign-in request has already been used.")
    if request.user_id is not None and request.user_id != user.id:
        raise AppError(409, "This sign-in request belongs to another account.")
    request.user_id = user.id
    request.denied_at = utcnow()
    db.commit()
    db.refresh(request)
    return request


def exchange(
    db: Session,
    *,
    code: str,
    verifier: str,
) -> tuple[str, int, User] | None:
    """Return (raw_token, expires_at_ms, user), or None while approval is pending."""
    request = _by_code(db, code)
    if request is None:
        raise AppError(401, "This sign-in request is not valid.")

    expected = request.challenge
    actual = challenge_for(verifier)
    if not hmac.compare_digest(expected, actual):
        raise AppError(401, "This sign-in request is not valid.")

    status = _status(request)
    if status == "expired":
        raise AppError(410, "This sign-in request has expired. Run `graphia login` again.")
    if status == "denied":
        raise AppError(403, "This sign-in request was denied in the browser.")
    if status == "claimed":
        raise AppError(410, "This sign-in request was already used. Run `graphia login` again.")
    if status != "approved" or request.user_id is None:
        return None

    user = db.get(User, request.user_id)
    if user is None:
        raise AppError(410, "This account no longer exists.")
    if user.is_guest:
        raise AppError(403, "The CLI requires a member account.")

    now = utcnow()
    claimed = db.execute(
        update(CliAuthRequest)
        .where(
            CliAuthRequest.id == request.id,
            CliAuthRequest.claimed_at.is_(None),
            CliAuthRequest.denied_at.is_(None),
            CliAuthRequest.approved_at.is_not(None),
            CliAuthRequest.expires_at > now,
        )
        .values(claimed_at=now)
        .execution_options(synchronize_session=False)
    )
    if claimed.rowcount == 0:
        db.rollback()
        current = _by_code(db, code)
        if current is not None and _status(current) == "denied":
            raise AppError(403, "This sign-in request was denied in the browser.")
        raise AppError(410, "This sign-in request was already used. Run `graphia login` again.")

    raw_token = auth_services.create_session(
        db,
        user,
        client=CLI_CLIENT,
        label=request.name,
    )
    db.commit()
    db.refresh(user)

    expires_at = now + timedelta(days=settings.session_ttl_days)
    return raw_token, to_ms(expires_at) or 0, user
