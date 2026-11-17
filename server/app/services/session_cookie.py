from __future__ import annotations

from fastapi import Response

from core.config import settings


def set_session_cookie(
    response: Response,
    raw_token: str,
    *,
    max_age_seconds: int | None = None,
) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        max_age=max_age_seconds or settings.session_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
