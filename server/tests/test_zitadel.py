from __future__ import annotations

import json
import time

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from app.services.zitadel import ZitadelClient, ZitadelError


def _client_and_key():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": "test-kid", "alg": "RS256", "use": "sig"})
    client = ZitadelClient(
        issuer="https://zitadel.test",
        client_id="test-client",
        http=httpx.Client(timeout=5),
        jwks={"keys": [jwk]},
    )
    client._discovery = {"id_token_signing_alg_values_supported": ["RS256"]}
    return client, private_key


def _token(private_key, *, nonce: str = "test-nonce", **overrides):
    now = int(time.time())
    claims = {
        "iss": "https://zitadel.test",
        "aud": "test-client",
        "sub": "zitadel-sub-1",
        "email": "ada@example.com",
        "email_verified": True,
        "nonce": nonce,
        "iat": now,
        "exp": now + 60,
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test-kid"})


def test_verify_id_token_accepts_valid_nonce_and_claims():
    client, key = _client_and_key()
    try:
        claims = client.verify_id_token(_token(key), nonce="test-nonce")
        assert claims["sub"] == "zitadel-sub-1"
        assert claims["email"] == "ada@example.com"
    finally:
        client.http.close()


def test_verify_id_token_rejects_wrong_nonce():
    client, key = _client_and_key()
    try:
        with pytest.raises(ZitadelError, match="nonce mismatch"):
            client.verify_id_token(_token(key), nonce="different-nonce")
    finally:
        client.http.close()


def test_verify_id_token_rejects_wrong_audience():
    client, key = _client_and_key()
    try:
        with pytest.raises(ZitadelError, match="id_token rejected"):
            client.verify_id_token(_token(key, aud="another-client"), nonce="test-nonce")
    finally:
        client.http.close()
