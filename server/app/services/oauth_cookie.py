from __future__ import annotations

from typing import Any

from fastapi import Request, Response

from core.config import settings
from core.security import OAUTH_COOKIE, OAUTH_COOKIE_MAX_AGE, sign_payload, unsign_payload


def set_oauth_cookie(response: Response, payload: dict[str, Any]) -> None:
    response.set_cookie(
        key=OAUTH_COOKIE,
        value=sign_payload(payload, settings.app_secret),
        max_age=OAUTH_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def read_oauth_payload(request: Request) -> dict[str, Any] | None:
    return unsign_payload(
        request.cookies.get(OAUTH_COOKIE),
        settings.app_secret,
        max_age=OAUTH_COOKIE_MAX_AGE,
    )


def clear_oauth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=OAUTH_COOKIE,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
