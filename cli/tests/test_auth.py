from __future__ import annotations

import time

import httpx
import pytest
import respx

from graphia_cli import auth
from graphia_cli.config import Runtime
from graphia_cli.errors import AuthError

CONFIG = {
    "appName": "Graphia",
    "version": "0.1.0",
    "webUrl": "https://graphia.test",
    "auth": {"mode": "browser-approval"},
    "limits": {
        "maxUploadMb": 25,
        "maxActiveJobs": 3,
        "uploadsPerHour": 120,
        "jobExpiryHours": 24,
    },
}

CODE = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"
LOGIN_URL = f"https://graphia.test/cli?code={CODE}"


def _create_response() -> httpx.Response:
    return httpx.Response(
        201,
        json={
            "code": CODE,
            "loginUrl": LOGIN_URL,
            "expiresAt": int(time.time() * 1000) + 60_000,
        },
    )


def _token_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "token": "session-token",
            "expiresAt": int(time.time() * 1000) + 60_000,
            "user": {
                "id": "user-1",
                "email": "ada@example.com",
                "name": "Ada",
                "isGuest": False,
                "createdAt": None,
            },
        },
    )


def test_challenge_is_url_safe_and_verifier_bound():
    first = auth.challenge_for(auth.create_verifier())
    second = auth.challenge_for(auth.create_verifier())
    assert len(first) == 43
    assert first != second
    assert set(first) <= set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    )


def test_file_token_store_round_trip(runtime: Runtime):
    assert auth.load_token(runtime) is None
    assert auth.store_token(runtime, "file-token") == "file"
    stored = auth.load_token(runtime)
    assert stored is not None
    assert stored.token == "file-token"
    assert stored.source == "file"
    auth.delete_token(runtime)
    assert auth.load_token(runtime) is None


def test_keyring_store_round_trip(runtime: Runtime, monkeypatch):
    monkeypatch.delenv("GRAPHIA_NO_KEYRING")
    values: dict[tuple[str, str], str] = {}
    monkeypatch.setattr(
        auth.keyring,
        "set_password",
        lambda service, key, value: values.__setitem__((service, key), value),
    )
    monkeypatch.setattr(
        auth.keyring,
        "get_password",
        lambda service, key: values.get((service, key)),
    )
    monkeypatch.setattr(
        auth.keyring,
        "delete_password",
        lambda service, key: values.pop((service, key), None),
    )

    assert auth.store_token(runtime, "keyring-token") == "keyring"
    stored = auth.load_token(runtime)
    assert stored is not None
    assert stored.token == "keyring-token"
    assert stored.source == "keyring"
    auth.delete_token(runtime)
    assert auth.load_token(runtime) is None


def test_login_waits_for_approval_and_stores_token(runtime: Runtime):
    echoed: list[str] = []
    opened: list[str] = []

    with respx.mock(assert_all_called=True) as router:
        router.get("https://graphia.test/api/config").mock(
            return_value=httpx.Response(200, json=CONFIG)
        )
        router.post("https://graphia.test/api/cli/requests").mock(
            return_value=_create_response()
        )
        router.post("https://graphia.test/api/cli/token").mock(
            side_effect=[
                httpx.Response(202, json={"status": "pending"}),
                _token_response(),
            ]
        )

        stored, user = auth.login(
            runtime,
            no_browser=False,
            open_browser=opened.append,
            sleep=lambda _seconds: None,
            echo=echoed.append,
        )

    assert stored.token == "session-token"
    assert stored.source == "file"
    assert user.email == "ada@example.com"
    assert opened == [LOGIN_URL]
    assert any(LOGIN_URL in line for line in echoed)
    assert auth.load_token(runtime).token == "session-token"


def test_login_rejects_a_local_approval_page_on_a_remote_api(runtime: Runtime):
    local_config = {**CONFIG, "webUrl": "http://localhost:3000"}

    with respx.mock(assert_all_called=True) as router:
        router.get("https://graphia.test/api/config").mock(
            return_value=httpx.Response(200, json=local_config)
        )

        with pytest.raises(AuthError, match="PUBLIC_BASE_URL"):
            auth.login(
                runtime,
                no_browser=True,
                sleep=lambda _seconds: None,
                echo=lambda _line: None,
            )


def test_login_allows_local_approval_with_opt_in(runtime: Runtime):
    echoed: list[str] = []
    local_config = {**CONFIG, "webUrl": "http://localhost:3000"}

    with respx.mock(assert_all_called=True) as router:
        router.get("https://graphia.test/api/config").mock(
            return_value=httpx.Response(200, json=local_config)
        )
        router.post("https://graphia.test/api/cli/requests").mock(
            return_value=_create_response()
        )
        router.post("https://graphia.test/api/cli/token").mock(
            return_value=_token_response()
        )

        stored, _user = auth.login(
            runtime,
            no_browser=True,
            allow_local_approval=True,
            sleep=lambda _seconds: None,
            echo=echoed.append,
        )

    assert stored.token == "session-token"
    assert any("Using the local approval page" in line for line in echoed)


def test_login_can_skip_the_browser(runtime: Runtime):
    opened: list[str] = []
    with respx.mock(assert_all_called=True) as router:
        router.get("https://graphia.test/api/config").mock(
            return_value=httpx.Response(200, json=CONFIG)
        )
        router.post("https://graphia.test/api/cli/requests").mock(
            return_value=_create_response()
        )
        router.post("https://graphia.test/api/cli/token").mock(
            return_value=_token_response()
        )

        auth.login(
            runtime,
            no_browser=True,
            open_browser=opened.append,
            sleep=lambda _seconds: None,
            echo=lambda _line: None,
        )

    assert opened == []


def test_login_surfaces_denial(runtime: Runtime):
    with respx.mock(assert_all_called=True) as router:
        router.get("https://graphia.test/api/config").mock(
            return_value=httpx.Response(200, json=CONFIG)
        )
        router.post("https://graphia.test/api/cli/requests").mock(
            return_value=_create_response()
        )
        router.post("https://graphia.test/api/cli/token").mock(
            return_value=httpx.Response(403, json={"error": "Denied in the browser."})
        )

        with pytest.raises(AuthError, match="Denied"):
            auth.login(
                runtime,
                no_browser=True,
                sleep=lambda _seconds: None,
                echo=lambda _line: None,
            )


def test_login_rejects_an_old_server(runtime: Runtime):
    with respx.mock(assert_all_called=True) as router:
        router.get("https://graphia.test/api/config").mock(
            return_value=httpx.Response(
                200,
                json={**CONFIG, "auth": {"mode": "none"}},
            )
        )
        with pytest.raises(AuthError, match="does not support"):
            auth.login(
                runtime,
                no_browser=True,
                sleep=lambda _seconds: None,
                echo=lambda _line: None,
            )


def test_logout_revokes_and_removes_the_token(runtime: Runtime):
    auth.store_token(runtime, "session-token")
    with respx.mock(assert_all_called=True) as router:
        route = router.post("https://graphia.test/api/cli/logout").mock(
            return_value=httpx.Response(200, json={"status": "signed_out"})
        )
        assert auth.logout(runtime) is True
        assert route.called

    assert auth.load_token(runtime) is None


def test_logout_without_a_token(runtime: Runtime):
    assert auth.logout(runtime) is False
