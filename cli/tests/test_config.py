from __future__ import annotations

from pathlib import Path

import pytest

from graphia_cli.config import (
    DEFAULT_SERVER,
    Runtime,
    load_saved_server,
    normalize_server,
    resolve_runtime,
    save_server,
)
from graphia_cli.errors import UsageError


def test_normalize_adds_https_for_public_hosts():
    assert normalize_server("graphia.app") == "https://graphia.app"
    assert normalize_server("https://graphia.app/") == "https://graphia.app"


def test_normalize_uses_http_for_localhost():
    assert normalize_server("localhost:3000") == "http://localhost:3000"
    assert normalize_server("127.0.0.1:8000") == "http://127.0.0.1:8000"


def test_normalize_rejects_paths_and_bad_schemes():
    with pytest.raises(UsageError):
        normalize_server("https://graphia.app/convert")
    with pytest.raises(UsageError):
        normalize_server("ftp://graphia.app")
    with pytest.raises(UsageError):
        normalize_server("")


def test_resolution_order(tmp_path: Path):
    env = {"GRAPHIA_CONFIG_DIR": str(tmp_path)}

    assert resolve_runtime(env=env).server == DEFAULT_SERVER
    assert resolve_runtime(env=env).server_source == "default"

    save_server(tmp_path / "config.toml", "https://saved.test")
    saved = resolve_runtime(env=env)
    assert saved.server == "https://saved.test"
    assert saved.server_source.endswith("config.toml")

    from_env = resolve_runtime(env={**env, "GRAPHIA_SERVER": "https://env.test"})
    assert from_env.server == "https://env.test"
    assert from_env.server_source == "GRAPHIA_SERVER"

    from_flag = resolve_runtime("https://flag.test", env=env)
    assert from_flag.server == "https://flag.test"
    assert from_flag.server_source == "--server"


def test_token_key_includes_port(tmp_path: Path):
    runtime = Runtime(
        server="http://localhost:3000",
        server_source="test",
        config_dir=tmp_path,
        config_path=tmp_path / "config.toml",
    )
    assert runtime.token_key == "localhost:3000"


def test_token_env_override(tmp_path: Path):
    runtime = resolve_runtime(
        env={
            "GRAPHIA_CONFIG_DIR": str(tmp_path),
            "GRAPHIA_TOKEN": "secret-token",
        }
    )
    assert runtime.token_override == "secret-token"


def test_corrupt_config_is_ignored(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text("not toml [", encoding="utf-8")
    assert load_saved_server(path) is None
    assert resolve_runtime(env={"GRAPHIA_CONFIG_DIR": str(tmp_path)}).server == DEFAULT_SERVER
