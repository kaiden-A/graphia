from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import secrets
import socket
import time
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import keyring

from graphia_cli import api
from graphia_cli.api import UserInfo
from graphia_cli.client import GraphiaClient
from graphia_cli.config import Runtime
from graphia_cli.errors import ApiError, AuthError, NetworkError

KEYRING_SERVICE = "graphia"


@dataclass(frozen=True)
class StoredToken:
    token: str
    source: str


def create_verifier() -> str:
    return secrets.token_urlsafe(64)


def challenge_for(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def is_localhost(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return host in {"localhost", "127.0.0.1", "::1"}


def device_name() -> str:
    host = socket.gethostname().strip() or "graphia-cli"
    system = platform.system().strip()
    name = f"{host} ({system})" if system else host
    return " ".join(name.split())[:64]


def clean_name(value: str | None) -> str:
    name = " ".join((value or "").split())[:64]
    return name or device_name()


def _keyring_enabled() -> bool:
    value = (os.environ.get("GRAPHIA_NO_KEYRING") or "").strip().lower()
    return value not in {"1", "true", "yes", "on"}


def _read_credentials(path: Path) -> dict[str, str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): str(value)
        for key, value in raw.items()
        if isinstance(value, str) and value
    }


def _write_credentials(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(values, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def store_token(runtime: Runtime, token: str) -> str:
    if _keyring_enabled():
        try:
            keyring.set_password(KEYRING_SERVICE, runtime.token_key, token)
        except Exception:
            pass
        else:
            # Do not leave a stale fallback token behind.
            values = _read_credentials(runtime.credentials_path)
            if runtime.token_key in values:
                values.pop(runtime.token_key, None)
                if values:
                    _write_credentials(runtime.credentials_path, values)
                else:
                    try:
                        runtime.credentials_path.unlink()
                    except OSError:
                        pass
            return "keyring"

    values = _read_credentials(runtime.credentials_path)
    values[runtime.token_key] = token
    _write_credentials(runtime.credentials_path, values)
    return "file"


def load_token(runtime: Runtime) -> StoredToken | None:
    if runtime.token_override:
        return StoredToken(runtime.token_override, "GRAPHIA_TOKEN")

    if _keyring_enabled():
        try:
            value = keyring.get_password(KEYRING_SERVICE, runtime.token_key)
        except Exception:
            value = None
        if value:
            return StoredToken(value, "keyring")

    value = _read_credentials(runtime.credentials_path).get(runtime.token_key)
    if value:
        return StoredToken(value, "file")
    return None


def delete_token(runtime: Runtime) -> None:
    if _keyring_enabled():
        try:
            keyring.delete_password(KEYRING_SERVICE, runtime.token_key)
        except Exception:
            pass

    values = _read_credentials(runtime.credentials_path)
    if runtime.token_key in values:
        values.pop(runtime.token_key, None)
        if values:
            _write_credentials(runtime.credentials_path, values)
        else:
            try:
                runtime.credentials_path.unlink()
            except OSError:
                pass


def login(
    runtime: Runtime,
    *,
    name: str | None = None,
    no_browser: bool = False,
    allow_local_approval: bool = False,
    open_browser: Callable[[str], object] = webbrowser.open,
    sleep: Callable[[float], None] = time.sleep,
    poll_seconds: float = 2.0,
    echo: Callable[[str], None] = print,
) -> tuple[StoredToken, UserInfo]:
    device = clean_name(name)

    with GraphiaClient(runtime.server, verbose=False) as public:
        try:
            config = api.get_config(public)
        except ApiError as exc:
            if exc.status == 404:
                raise AuthError(
                    "This server does not expose the CLI configuration. "
                    "Update the Graphia API and try again."
                ) from exc
            raise
        if config.auth_mode != "browser-approval":
            raise AuthError("This server does not support `graphia login` yet.")

        if is_localhost(config.web_url) and not is_localhost(runtime.server):
            if not allow_local_approval:
                raise AuthError(
                    "The API reports its approval page as "
                    f"{config.web_url}. Set PUBLIC_BASE_URL on the API to the "
                    "deployed client origin, or pass --allow-local-approval if "
                    "the client is running locally against this API."
                )
            echo(
                "Using the local approval page reported by the API: "
                f"{config.web_url}"
            )

        verifier = create_verifier()
        created = public.json(
            "POST",
            "/api/cli/requests",
            json={"name": device, "challenge": challenge_for(verifier)},
        )
        if not isinstance(created, dict):
            raise NetworkError("The server returned an unexpected response.")
        code = created.get("code")
        login_url = created.get("loginUrl")
        expires_at = created.get("expiresAt")
        if not isinstance(code, str) or not isinstance(login_url, str):
            raise NetworkError("The server did not return a sign-in link.")

        short = f"{code[:4]}-{code[4:8]}" if len(code) >= 8 else code
        echo(f"Open this URL to approve the terminal:\n  {login_url}")
        echo(f"Code: {short}")
        if not no_browser:
            try:
                open_browser(login_url)
            except Exception:
                pass
        echo("Waiting for approval in the browser…")

        deadline_seconds = (
            max(0.0, (expires_at / 1000) - time.time()) + 5.0
            if isinstance(expires_at, (int, float))
            else 10 * 60
        )
        deadline = time.monotonic() + deadline_seconds

        while time.monotonic() < deadline:
            response = public.request(
                "POST",
                "/api/cli/token",
                json={"code": code, "verifier": verifier},
            )
            if response.status_code == 202:
                sleep(poll_seconds)
                continue
            try:
                data = public.parse(response)
            except ApiError as exc:
                raise AuthError(str(exc)) from exc
            if not isinstance(data, dict):
                raise NetworkError("The server returned an unexpected response.")
            token = data.get("token")
            user = data.get("user")
            if not isinstance(token, str) or not isinstance(user, dict):
                raise NetworkError("The server did not return a session token.")
            stored_source = store_token(runtime, token)
            return (
                StoredToken(token, stored_source),
                UserInfo(
                    id=str(user.get("id") or ""),
                    email=str(user.get("email") or ""),
                    name=user.get("name") if isinstance(user.get("name"), str) else None,
                    is_guest=bool(user.get("isGuest")),
                ),
            )

    raise AuthError("The sign-in request expired. Run `graphia login` again.")


def logout(runtime: Runtime) -> bool:
    stored = load_token(runtime)
    if stored is None:
        return False

    with GraphiaClient(runtime.server, token=stored.token) as client:
        try:
            api.logout(client)
        except (ApiError, NetworkError):
            pass
    delete_token(runtime)
    return True
