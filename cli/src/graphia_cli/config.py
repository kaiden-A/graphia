from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import platformdirs
import tomli_w

from graphia_cli.errors import UsageError

DEFAULT_SERVER = "http://localhost:3000"
CONFIG_FILENAME = "config.toml"


@dataclass(frozen=True)
class Runtime:
    server: str
    server_source: str
    config_dir: Path
    config_path: Path
    token_override: str | None = None

    @property
    def token_key(self) -> str:
        return urlsplit(self.server).netloc.lower()

    @property
    def credentials_path(self) -> Path:
        return self.config_dir / "credentials.json"


def normalize_server(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise UsageError("A server URL is required, for example https://graphia.app")

    if "://" not in raw:
        host = raw.split("/", 1)[0].split(":", 1)[0].lower()
        scheme = "http" if host in {"localhost", "127.0.0.1", "::1"} else "https"
        raw = f"{scheme}://{raw}"

    parsed = urlsplit(raw)
    if parsed.scheme not in {"http", "https"}:
        raise UsageError("The server must use http:// or https://.")
    if not parsed.netloc:
        raise UsageError("The server URL has no host.")
    if parsed.query or parsed.fragment:
        raise UsageError("Use the site origin only, without a query or fragment.")
    if parsed.path not in {"", "/"}:
        raise UsageError("Use the site origin only, for example https://graphia.app")

    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def default_config_dir(env: Mapping[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    override = (values.get("GRAPHIA_CONFIG_DIR") or "").strip()
    if override:
        return Path(override).expanduser()
    return Path(platformdirs.user_config_dir("graphia"))


def load_saved_server(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError:
        return None
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    server = data.get("server")
    return server.strip() if isinstance(server, str) and server.strip() else None


def save_server(path: Path, server: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(tomli_w.dumps({"server": server}), encoding="utf-8")
    os.replace(temp, path)


def resolve_runtime(
    server_flag: str | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Runtime:
    values = os.environ if env is None else env
    config_dir = default_config_dir(values)
    config_path = config_dir / CONFIG_FILENAME

    if server_flag:
        server = normalize_server(server_flag)
        source = "--server"
    else:
        from_env = (values.get("GRAPHIA_SERVER") or "").strip()
        if from_env:
            server = normalize_server(from_env)
            source = "GRAPHIA_SERVER"
        else:
            saved = load_saved_server(config_path)
            if saved:
                server = normalize_server(saved)
                source = str(config_path)
            else:
                server = DEFAULT_SERVER
                source = "default"

    token_override = (values.get("GRAPHIA_TOKEN") or "").strip() or None
    return Runtime(
        server=server,
        server_source=source,
        config_dir=config_dir,
        config_path=config_path,
        token_override=token_override,
    )
