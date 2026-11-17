from __future__ import annotations

import hmac
import logging
import time
from datetime import timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import client_ip, get_zitadel, require_user
from app.schemas.auth import LogoutResponse, UserPublic
from app.services import auth_services, oauth_cookie
from app.services.rate_limit import guest_limiter, login_limiter
from app.services.session_cookie import clear_session_cookie, set_session_cookie
from app.services.zitadel import ZitadelClient, ZitadelError
from core.config import settings
from core.database import get_db
from core.errors import AppError
from core.models.user import User
from core.security import create_pkce_pair, new_state_nonce
from core.utils import local_path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

ALLOWED_PROMPTS = {"login", "create", "select_account"}


def _login_url(error: str | None = None) -> str:
    base = f"{settings.public_base_url.rstrip('/')}/login"
    if not error:
        return base
    return f"{base}?{urlencode({'error': error})}"


def _start_login(
    request: Request,
    *,
    zitadel: ZitadelClient,
    prompt_override: str | None = None,
) -> RedirectResponse:
    if not settings.zitadel_configured:
        return RedirectResponse(
            _login_url("Single sign-on is not configured yet."),
            status_code=302,
        )

    if not login_limiter.hit(
        f"oauth:{client_ip(request)}",
        limit=30,
        window_seconds=900,
    ):
        return RedirectResponse(
            _login_url("Too many sign-in attempts. Try again in a few minutes."),
            status_code=302,
        )

    verifier, challenge = create_pkce_pair()
    state, nonce = new_state_nonce()
    payload = {
        "state": state,
        "nonce": nonce,
        "code_verifier": verifier,
        "next": local_path(request.query_params.get("next")),
        "iat": int(time.time()),
    }

    login_hint = (request.query_params.get("login_hint") or "").strip()[:320] or None
    requested_prompt = (request.query_params.get("prompt") or "").strip().lower()
    prompt = prompt_override or (requested_prompt if requested_prompt in ALLOWED_PROMPTS else None)

    try:
        authorize_url = zitadel.authorize_url(
            state=state,
            nonce=nonce,
            code_challenge=challenge,
            redirect_uri=settings.zitadel_redirect_uri,
            login_hint=login_hint,
            prompt=prompt,
        )
    except (ZitadelError, httpx.HTTPError, KeyError):
        logger.exception("Could not start the Zitadel login")
        return RedirectResponse(
            _login_url("Sign-in is temporarily unavailable. Try again in a moment."),
            status_code=302,
        )

    response = RedirectResponse(authorize_url, status_code=302)
    oauth_cookie.set_oauth_cookie(response, payload)
    return response


@router.get("/login")
def login_get(
    request: Request,
    zitadel: ZitadelClient = Depends(get_zitadel),
) -> RedirectResponse:
    return _start_login(request, zitadel=zitadel)


@router.post("/login")
def login_post(
    request: Request,
    zitadel: ZitadelClient = Depends(get_zitadel),
) -> RedirectResponse:
    return _start_login(request, zitadel=zitadel)


@router.get("/signup")
def signup_get(
    request: Request,
    zitadel: ZitadelClient = Depends(get_zitadel),
) -> RedirectResponse:
    return _start_login(request, zitadel=zitadel, prompt_override="create")


@router.post("/guest")
def guest(
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    next_path = local_path(request.query_params.get("next"))

    origin = (request.headers.get("origin") or "").strip().rstrip("/")
    expected = settings.public_base_url.strip().rstrip("/")
    if origin and origin != expected:
        return RedirectResponse(
            _login_url("This guest request did not come from Graphia."),
            status_code=303,
        )

    if not guest_limiter.hit(
        f"guest:{client_ip(request)}",
        limit=settings.guest_sessions_per_hour_per_ip,
        window_seconds=3600,
    ):
        return RedirectResponse(
            _login_url("Too many guest sessions from this network. Try again later."),
            status_code=303,
        )

    raw_token: str | None = None
    existing = auth_services.find_active_session(
        db, request.cookies.get(settings.session_cookie_name)
    )
    if existing is None:
        _, raw_token = auth_services.create_guest_user(
            db,
            ttl=timedelta(hours=settings.guest_session_ttl_hours),
        )

    response = RedirectResponse(next_path, status_code=303)
    if raw_token:
        set_session_cookie(
            response,
            raw_token,
            max_age_seconds=settings.guest_session_ttl_seconds,
        )
    return response


@router.get("/callback")
def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
    zitadel: ZitadelClient = Depends(get_zitadel),
) -> RedirectResponse:
    payload = oauth_cookie.read_oauth_payload(request)

    if error:
        response = RedirectResponse(_login_url("Signing in was cancelled."), status_code=302)
        oauth_cookie.clear_oauth_cookie(response)
        return response

    if (
        payload is None
        or not code
        or not state
        or not hmac.compare_digest(str(payload.get("state", "")), state)
    ):
        response = RedirectResponse(
            _login_url("Could not finish signing in. Please try again."),
            status_code=302,
        )
        oauth_cookie.clear_oauth_cookie(response)
        return response

    try:
        tokens = zitadel.exchange_code(
            code=code,
            code_verifier=str(payload["code_verifier"]),
            redirect_uri=settings.zitadel_redirect_uri,
        )
        id_token = tokens.get("id_token")
        if not id_token:
            raise ZitadelError("token response had no id_token")
        claims = zitadel.verify_id_token(id_token, nonce=str(payload["nonce"]))
    except (ZitadelError, httpx.HTTPError, KeyError, ValueError):
        logger.exception("Zitadel token exchange or ID token verification failed")
        response = RedirectResponse(
            _login_url("Sign-in is temporarily unavailable. Try again in a moment."),
            status_code=302,
        )
        oauth_cookie.clear_oauth_cookie(response)
        return response

    subject = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip().lower()
    if not subject or not email:
        response = RedirectResponse(
            _login_url("Your Zitadel account does not expose an email address."),
            status_code=302,
        )
        oauth_cookie.clear_oauth_cookie(response)
        return response
    if claims.get("email_verified") is False:
        response = RedirectResponse(
            _login_url("Your Zitadel email address is not verified."),
            status_code=302,
        )
        oauth_cookie.clear_oauth_cookie(response)
        return response

    name = claims.get("name") or claims.get("preferred_username") or email
    try:
        user = auth_services.find_or_create_zitadel_user(
            db,
            issuer=settings.zitadel_issuer_url,
            subject=subject,
            email=email,
            name=str(name),
        )
    except AppError as exc:
        response = RedirectResponse(_login_url(exc.message), status_code=302)
        oauth_cookie.clear_oauth_cookie(response)
        return response

    raw_token = auth_services.create_session(db, user)
    db.commit()
    auth_services.claim_guest_conversions(
        db,
        raw_token=request.cookies.get(settings.session_cookie_name),
        user=user,
    )

    response = RedirectResponse(local_path(str(payload.get("next"))), status_code=302)
    set_session_cookie(response, raw_token)
    oauth_cookie.clear_oauth_cookie(response)
    return response


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    zitadel: ZitadelClient = Depends(get_zitadel),
) -> JSONResponse:
    raw_token = request.cookies.get(settings.session_cookie_name)
    is_guest = False
    if raw_token:
        session = auth_services.session_by_token(db, raw_token)
        if session is not None:
            is_guest = bool(session.user and session.user.is_guest)
            auth_services.revoke_session(db, session)

    logout_url: str | None = None
    if settings.zitadel_configured and not is_guest:
        try:
            logout_url = zitadel.end_session_url(
                post_logout_redirect_uri=settings.zitadel_post_logout_uri
            )
        except (ZitadelError, httpx.HTTPError, KeyError):
            # Never trap someone in the app because discovery is down.
            logger.exception("Could not build the Zitadel end-session URL")

    response = JSONResponse(LogoutResponse(logoutUrl=logout_url).model_dump())
    clear_session_cookie(response)
    oauth_cookie.clear_oauth_cookie(response)
    return response


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(require_user)) -> UserPublic:
    return UserPublic.from_user(user)
