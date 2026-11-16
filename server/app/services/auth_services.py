from __future__ import annotations

import hmac
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import settings
from core.errors import AppError
from core.models.session import UserSession
from core.models.user import User
from core.security import hash_password, hash_token, new_session_token, verify_password
from core.utils import utcnow


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == normalize_email(email))).scalar_one_or_none()


def signup(
    db: Session,
    *,
    email: str,
    password: str,
    name: str | None,
    invite_code: str | None,
) -> tuple[User, str]:
    if not settings.signup_enabled:
        raise AppError(403, "Signup is currently closed.")

    if settings.signup_requires_code:
        expected = settings.signup_invite_code.strip()
        provided = (invite_code or "").strip()
        if not hmac.compare_digest(provided, expected):
            raise AppError(403, "The invite code is not valid.")

    normalized = normalize_email(email)
    if get_user_by_email(db, normalized) is not None:
        raise AppError(409, "An account with that email already exists.")

    user = User(
        email=normalized,
        name=name,
        password_hash=hash_password(password),
    )
    try:
        db.add(user)
        db.flush()
        raw_token = create_session(db, user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "An account with that email already exists.") from exc
    return user, raw_token


def login(db: Session, *, email: str, password: str) -> tuple[User, str]:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise AppError(401, "Email or password is incorrect.")
    raw_token = create_session(db, user)
    db.commit()
    return user, raw_token


def create_session(db: Session, user: User) -> str:
    raw_token, token_hash = new_session_token()
    now = utcnow()
    session = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(days=settings.session_ttl_days),
    )
    db.add(session)
    return raw_token


def revoke_session(db: Session, session: UserSession) -> None:
    if session.revoked_at is None:
        session.revoked_at = utcnow()
        db.commit()


def session_by_token(db: Session, raw_token: str) -> UserSession | None:
    return db.execute(
        select(UserSession).where(UserSession.token_hash == hash_token(raw_token))
    ).scalar_one_or_none()
