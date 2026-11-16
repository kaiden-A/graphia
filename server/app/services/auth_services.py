from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import settings
from core.errors import AppError
from core.models.session import UserSession
from core.models.user import User
from core.security import hash_token, new_session_token
from core.utils import utcnow


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
