from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from core.config import settings
from core.database import get_db
from core.errors import AppError
from core.models.session import UserSession
from core.models.user import User
from core.security import hash_token
from core.utils import ensure_utc, utcnow


@dataclass
class AuthContext:
    user: User
    session: UserSession


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def require_auth(
    request: Request,
    db: Session = Depends(get_db),
) -> AuthContext:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        raise AppError(401, "Not signed in.")

    session = db.execute(
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(UserSession.token_hash == hash_token(raw_token))
    ).scalar_one_or_none()

    now = utcnow()
    if session is None or session.revoked_at is not None:
        raise AppError(401, "Your session has expired. Please sign in again.")
    expires_at = ensure_utc(session.expires_at)
    if expires_at is None or expires_at <= now:
        raise AppError(401, "Your session has expired. Please sign in again.")
    if session.user is None:
        raise AppError(401, "Not signed in.")

    last_seen = ensure_utc(session.last_seen_at)
    if last_seen is None or now - last_seen > timedelta(minutes=5):
        session.last_seen_at = now
        db.commit()

    return AuthContext(user=session.user, session=session)


def require_user(auth: AuthContext = Depends(require_auth)) -> User:
    return auth.user
