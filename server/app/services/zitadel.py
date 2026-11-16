"""Explicit Zitadel OIDC client.

Authorization Code + PKCE, no client secret. The code exchange happens on the
server; the browser only carries state, nonce, and the verifier in a signed
HttpOnly cookie.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlencode

import httpx
import jwt

SCOPE = "openid profile email"
CLOCK_SKEW_SECONDS = 60


class ZitadelError(RuntimeError):
    pass


@dataclass
class ZitadelClient:
    issuer: str
    client_id: str
    http: httpx.Client
    jwks: dict | None = None  # test seam
    _discovery: dict | None = field(default=None, init=False, repr=False)

    @property
    def normalized_issuer(self) -> str:
        return self.issuer.rstrip("/")

    def discovery(self) -> dict:
        if self._discovery is None:
            response = self.http.get(
                f"{self.normalized_issuer}/.well-known/openid-configuration"
            )
            response.raise_for_status()
            self._discovery = dict(response.json())
        return self._discovery

    def authorize_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
        redirect_uri: str,
        login_hint: str | None = None,
        prompt: str | None = None,
    ) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": SCOPE,
            "redirect_uri": redirect_uri,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if login_hint:
            params["login_hint"] = login_hint
        if prompt:
            params["prompt"] = prompt
        return f"{self.discovery()['authorization_endpoint']}?{urlencode(params)}"

    def exchange_code(self, *, code: str, code_verifier: str, redirect_uri: str) -> dict:
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "code_verifier": code_verifier,
        }
        response = self.http.post(self.discovery()["token_endpoint"], data=payload)
        if response.status_code >= 400:
            raise ZitadelError(
                f"token exchange failed ({response.status_code}): {response.text[:300]}"
            )
        return response.json()

    def verify_id_token(self, id_token: str, *, nonce: str) -> dict:
        key_set = self.jwks if self.jwks is not None else self._fetch_jwks()
        try:
            kid = jwt.get_unverified_header(id_token).get("kid")
        except jwt.PyJWTError as exc:
            raise ZitadelError(f"malformed id_token: {exc}") from exc

        try:
            parsed = jwt.PyJWKSet.from_dict(key_set)
            key = parsed[kid] if kid else parsed.keys[0]
        except (jwt.PyJWTError, KeyError, IndexError) as exc:
            raise ZitadelError(f"unknown signing key: {exc}") from exc

        algorithms = self.discovery().get("id_token_signing_alg_values_supported") or ["RS256"]
        try:
            claims = jwt.decode(
                id_token,
                key.key,
                algorithms=[alg for alg in algorithms if alg != "none"],
                audience=self.client_id,
                issuer=self.normalized_issuer,
                options={"require": ["exp", "iat", "sub", "aud", "iss"]},
                leeway=CLOCK_SKEW_SECONDS,
            )
        except jwt.PyJWTError as exc:
            raise ZitadelError(f"id_token rejected: {exc}") from exc

        if claims.get("nonce") != nonce:
            raise ZitadelError("nonce mismatch")
        return claims

    def end_session_url(
        self,
        *,
        post_logout_redirect_uri: str | None = None,
    ) -> str:
        endpoint = self.discovery()["end_session_endpoint"]
        params = {"client_id": self.client_id}
        if post_logout_redirect_uri:
            params["post_logout_redirect_uri"] = post_logout_redirect_uri
        return f"{endpoint}?{urlencode(params)}"

    def _fetch_jwks(self) -> dict:
        response = self.http.get(self.discovery()["jwks_uri"])
        response.raise_for_status()
        return response.json()
