from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

OAUTH_COOKIE = "graphia_oauth"
OAUTH_COOKIE_MAX_AGE = 600


def new_session_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign_payload(payload: dict[str, Any], secret: str) -> str:
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64e(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def unsign_payload(value: str | None, secret: str, *, max_age: int) -> dict[str, Any] | None:
    if not value or "." not in value:
        return None
    body, _, signature = value.partition(".")
    expected = _b64e(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(_b64d(body))
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    issued = payload.get("iat")
    if not isinstance(issued, int) or time.time() - issued > max_age:
        return None
    return payload


def create_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) per RFC 7636 S256."""
    verifier = secrets.token_urlsafe(64)
    challenge = _b64e(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


def new_state_nonce() -> tuple[str, str]:
    return secrets.token_urlsafe(32), secrets.token_urlsafe(32)
