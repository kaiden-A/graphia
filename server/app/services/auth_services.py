from __future__ import annotations

import logging
import uuid
from datetime import timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from core.config import settings
from core.errors import AppError
from core.models.conversion_job import ConversionJob
from core.models.session import UserSession
from core.models.user import User
from core.security import hash_token, new_session_token
from core.utils import ensure_utc, utcnow

logger = logging.getLogger(__name__)

GUEST_EMAIL_DOMAIN = "guest.graphia.local"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == normalize_email(email))).scalar_one_or_none()


def find_zitadel_user(db: Session, *, issuer: str, subject: str) -> User | None:
    return db.execute(
        select(User).where(
            User.idp_issuer == issuer,
            User.zitadel_sub == subject,
        )
    ).scalar_one_or_none()


def find_or_create_zitadel_user(
    db: Session,
    *,
    issuer: str,
    subject: str,
    email: str,
    name: str | None,
) -> User:
    """JIT-provision the local projection of a Zitadel identity.

    Existing local users are adopted by email so their conversion jobs survive
    the switch from password auth to Zitadel.
    """
    issuer = issuer.strip().rstrip("/")
    subject = subject.strip()
    email = normalize_email(email)
    clean_name = (name or "").strip()[:120] or None

    if not issuer or not subject:
        raise AppError(403, "The identity provider returned an incomplete identity.")
    if not email:
        raise AppError(403, "Your Zitadel account has no email address.")

    user = find_zitadel_user(db, issuer=issuer, subject=subject)
    if user is not None:
        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if clean_name and user.name != clean_name:
            user.name = clean_name
            changed = True
        if changed:
            try:
                db.commit()
            except IntegrityError as exc:
                db.rollback()
                raise AppError(
                    409,
                    "That email is already linked to another account.",
                ) from exc
        return user

    existing = get_user_by_email(db, email)
    if existing is not None:
        if existing.zitadel_sub is not None:
            raise AppError(409, "That email is already linked to another Zitadel identity.")
        existing.idp_issuer = issuer
        existing.zitadel_sub = subject
        if clean_name:
            existing.name = clean_name
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise AppError(409, "That email is already linked to another account.") from exc
        db.refresh(existing)
        return existing

    user = User(
        email=email,
        name=clean_name,
        password_hash=None,
        idp_issuer=issuer,
        zitadel_sub=subject,
    )
    try:
        db.add(user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "That email is already linked to another account.") from exc
    db.refresh(user)
    return user


def create_session(
    db: Session,
    user: User,
    *,
    ttl: timedelta | None = None,
) -> str:
    raw_token, token_hash = new_session_token()
    now = utcnow()
    session = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        created_at=now,
        last_seen_at=now,
        expires_at=now + (ttl or timedelta(days=settings.session_ttl_days)),
    )
    db.add(session)
    return raw_token


def create_guest_user(
    db: Session,
    *,
    ttl: timedelta | None = None,
) -> tuple[User, str]:
    """Create a disposable account so a visitor can run one or more jobs."""
    suffix = uuid.uuid4().hex
    user = User(
        email=f"guest+{suffix}@{GUEST_EMAIL_DOMAIN}",
        name="Guest",
        is_guest=True,
    )
    db.add(user)
    db.flush()
    raw_token = create_session(db, user, ttl=ttl)
    db.commit()
    db.refresh(user)
    return user, raw_token


def find_active_session(db: Session, raw_token: str | None) -> UserSession | None:
    if not raw_token:
        return None
    session = db.execute(
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(UserSession.token_hash == hash_token(raw_token))
    ).scalar_one_or_none()
    now = utcnow()
    if session is None or session.revoked_at is not None:
        return None
    expires_at = ensure_utc(session.expires_at)
    if expires_at is None or expires_at <= now:
        return None
    return session


def claim_guest_conversions(
    db: Session,
    *,
    raw_token: str | None,
    user: User,
) -> int:
    """Move a guest's jobs to the account that just signed in.

    R2 keys keep the guest prefix from upload time. The job row stores both
    keys, so ownership and downloads follow the row, not the key prefix.
    """
    session = find_active_session(db, raw_token)
    if (
        session is None
        or session.user is None
        or not session.user.is_guest
        or session.user_id == user.id
    ):
        return 0

    guest_id = session.user_id
    try:
        moved = db.execute(
            update(ConversionJob)
            .where(ConversionJob.owner_id == guest_id)
            .values(owner_id=user.id)
            .execution_options(synchronize_session=False)
        )
        db.execute(
            delete(UserSession)
            .where(UserSession.user_id == guest_id)
            .execution_options(synchronize_session=False)
        )
        db.execute(
            delete(User)
            .where(User.id == guest_id, User.is_guest.is_(True))
            .execution_options(synchronize_session=False)
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not transfer guest conversions")
        return 0
    return int(moved.rowcount or 0)


def revoke_session(db: Session, session: UserSession) -> None:
    if session.revoked_at is None:
        session.revoked_at = utcnow()
        db.commit()


def session_by_token(db: Session, raw_token: str) -> UserSession | None:
    return db.execute(
        select(UserSession).where(UserSession.token_hash == hash_token(raw_token))
    ).scalar_one_or_none()
