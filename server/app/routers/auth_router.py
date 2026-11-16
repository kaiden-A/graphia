from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.dependencies import client_ip, require_user
from app.schemas.auth import AuthConfig, LoginIn, SignupIn, UserPublic
from app.services import auth_services
from app.services.rate_limit import login_limiter, signup_limiter
from app.services.session_cookie import clear_session_cookie, set_session_cookie
from core.config import settings
from core.database import get_db
from core.errors import AppError
from core.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/config", response_model=AuthConfig)
def auth_config() -> AuthConfig:
    return AuthConfig(
        signupEnabled=settings.signup_enabled,
        signupRequiresCode=settings.signup_requires_code,
    )


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> UserPublic:
    if not signup_limiter.hit(f"signup:{client_ip(request)}", limit=5, window_seconds=3600):
        raise AppError(429, "Too many signup attempts. Try again later.")

    user, raw_token = auth_services.signup(
        db,
        email=str(payload.email),
        password=payload.password,
        name=payload.name,
        invite_code=payload.inviteCode,
    )
    set_session_cookie(response, raw_token)
    return UserPublic.from_user(user)


@router.post("/login", response_model=UserPublic)
def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> UserPublic:
    key = f"login:{client_ip(request)}:{str(payload.email).lower()}"
    if not login_limiter.hit(key, limit=10, window_seconds=900):
        raise AppError(429, "Too many sign-in attempts. Try again in a few minutes.")

    user, raw_token = auth_services.login(
        db,
        email=str(payload.email),
        password=payload.password,
    )
    set_session_cookie(response, raw_token)
    return UserPublic.from_user(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if raw_token:
        session = auth_services.session_by_token(db, raw_token)
        if session is not None:
            auth_services.revoke_session(db, session)

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookie(response)
    return response


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(require_user)) -> UserPublic:
    return UserPublic.from_user(user)
