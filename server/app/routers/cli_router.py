from __future__ import annotations

from typing import cast
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.dependencies import (
    AuthContext,
    client_ip,
    require_auth,
    require_web_member,
)
from app.schemas.auth import UserPublic
from app.schemas.cli import (
    CliAuthRequestIn,
    CliAuthRequestOut,
    CliAuthStatus,
    CliAuthStatusOut,
    CliLogoutOut,
    CliPendingOut,
    CliTokenIn,
    CliTokenOut,
)
from app.services import auth_services, cli_services
from app.services.rate_limit import cli_limiter
from core.config import settings
from core.database import get_db
from core.errors import AppError
from core.models.user import User
from core.utils import to_ms

router = APIRouter(prefix="/api/cli", tags=["cli"])


def _check_origin(request: Request) -> None:
    origin = (request.headers.get("origin") or "").strip().rstrip("/").lower()
    expected = settings.public_base_url.strip().rstrip("/").lower()
    if origin and origin != expected:
        raise AppError(403, "This request did not come from Graphia.")


@router.post(
    "/requests",
    response_model=CliAuthRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    payload: CliAuthRequestIn,
    request: Request,
    db: Session = Depends(get_db),
) -> CliAuthRequestOut:
    if not settings.zitadel_configured:
        raise AppError(
            503,
            "Single sign-on is not configured on this server, so the CLI cannot sign in.",
        )
    if not cli_limiter.hit(
        f"cli-create:{client_ip(request)}",
        limit=30,
        window_seconds=3600,
    ):
        raise AppError(429, "Too many CLI sign-in requests. Try again later.")

    auth_request, code = cli_services.create_request(
        db,
        name=payload.name,
        challenge=payload.challenge,
    )
    login_url = f"{settings.public_base_url.rstrip('/')}/cli?{urlencode({'code': code})}"
    return CliAuthRequestOut(
        code=code,
        loginUrl=login_url,
        expiresAt=to_ms(auth_request.expires_at) or 0,
    )


@router.get("/requests/{code}", response_model=CliAuthStatusOut)
def get_request(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
) -> CliAuthStatusOut:
    if not cli_limiter.hit(
        f"cli-status:{client_ip(request)}",
        limit=120,
        window_seconds=60,
    ):
        raise AppError(429, "Too many requests. Try again in a moment.")

    auth_request, status_value = cli_services.request_status(db, code=code)
    return CliAuthStatusOut(
        name=auth_request.name,
        status=cast(CliAuthStatus, status_value),
        expiresAt=to_ms(auth_request.expires_at) or 0,
    )


@router.post("/requests/{code}/approve", response_model=CliAuthStatusOut)
def approve_request(
    code: str,
    request: Request,
    user: User = Depends(require_web_member),
    db: Session = Depends(get_db),
) -> CliAuthStatusOut:
    _check_origin(request)
    if not cli_limiter.hit(f"cli-approve:{user.id}", limit=20, window_seconds=3600):
        raise AppError(429, "Too many approval attempts. Try again later.")

    auth_request = cli_services.approve(db, code=code, user=user)
    return CliAuthStatusOut(
        name=auth_request.name,
        status="approved",
        expiresAt=to_ms(auth_request.expires_at) or 0,
    )


@router.post("/requests/{code}/deny", response_model=CliAuthStatusOut)
def deny_request(
    code: str,
    request: Request,
    user: User = Depends(require_web_member),
    db: Session = Depends(get_db),
) -> CliAuthStatusOut:
    _check_origin(request)
    auth_request = cli_services.deny(db, code=code, user=user)
    return CliAuthStatusOut(
        name=auth_request.name,
        status="denied",
        expiresAt=to_ms(auth_request.expires_at) or 0,
    )


@router.post("/token", response_model=CliTokenOut | CliPendingOut)
def exchange_token(
    payload: CliTokenIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> CliTokenOut | CliPendingOut:
    if not cli_limiter.hit(
        f"cli-token:{client_ip(request)}",
        limit=120,
        window_seconds=60,
    ):
        raise AppError(429, "Too many token requests. Try again in a moment.")

    result = cli_services.exchange(db, code=payload.code, verifier=payload.verifier)
    if result is None:
        response.status_code = status.HTTP_202_ACCEPTED
        return CliPendingOut()

    raw_token, expires_at, user = result
    return CliTokenOut(
        token=raw_token,
        expiresAt=expires_at,
        user=UserPublic.from_user(user),
    )


@router.post("/logout", response_model=CliLogoutOut)
def logout(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> CliLogoutOut:
    auth_services.revoke_session(db, auth.session)
    return CliLogoutOut()
