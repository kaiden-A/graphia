from __future__ import annotations

import json
import time
import tomllib
from pathlib import Path

import httpx
import respx
from typer.testing import CliRunner

from graphia_cli import __version__
from graphia_cli.main import app

RUNNER = CliRunner()

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

OPERATIONS = [
    {
        "id": "pptx_to_pdf",
        "label": "PPTX to PDF",
        "description": "",
        "group": "Make a PDF",
        "inputExtensions": ["pptx"],
        "outputExtension": "pdf",
        "outputSuffix": "",
    }
]

ME = {
    "id": "user-1",
    "email": "ada@example.com",
    "name": "Ada",
    "isGuest": False,
    "createdAt": None,
}


def _job(status: str = "PENDING") -> dict:
    completed = status == "COMPLETED"
    return {
        "id": "job-1",
        "operation": "pptx_to_pdf",
        "operationLabel": "PPTX to PDF",
        "originalFilename": "deck.pptx",
        "status": status,
        "errorMessage": None,
        "fileSize": 4,
        "outputSize": 8 if completed else None,
        "outputFilename": "deck.pdf" if completed else None,
        "uploadCompleted": status != "PENDING",
        "downloadAvailable": completed,
        "downloadRequiresAccount": False,
        "attempts": 0 if status == "PENDING" else 1,
        "createdAt": int(time.time() * 1000),
        "startedAt": None,
        "completedAt": None,
        "expiresAt": int(time.time() * 1000) + 86_400_000,
    }


def _mock_public(router: respx.Router, *, me: bool = True) -> None:
    router.get("https://graphia.test/api/config").mock(
        return_value=httpx.Response(200, json=CONFIG)
    )
    router.get("https://graphia.test/api/operations").mock(
        return_value=httpx.Response(200, json=OPERATIONS)
    )
    if me:
        router.get("https://graphia.test/api/auth/me").mock(
            return_value=httpx.Response(200, json=ME)
        )


def test_version_matches_pyproject():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert data["project"]["version"] == __version__


def _env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GRAPHIA_SERVER", "https://graphia.test")
    monkeypatch.setenv("GRAPHIA_TOKEN", "session-token")
    monkeypatch.setenv("GRAPHIA_CONFIG_DIR", str(tmp_path))


def test_operations_json(monkeypatch, tmp_path: Path):
    _env(monkeypatch, tmp_path)
    with respx.mock(assert_all_called=True) as router:
        router.get("https://graphia.test/api/operations").mock(
            return_value=httpx.Response(200, json=OPERATIONS)
        )
        result = RUNNER.invoke(app, ["operations", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data[0]["id"] == "pptx_to_pdf"


def test_whoami(monkeypatch, tmp_path: Path):
    _env(monkeypatch, tmp_path)
    with respx.mock(assert_all_called=True) as router:
        router.get("https://graphia.test/api/auth/me").mock(
            return_value=httpx.Response(200, json=ME)
        )
        result = RUNNER.invoke(app, ["whoami"])

    assert result.exit_code == 0, result.output
    assert "ada@example.com" in result.output
    assert "GRAPHIA_TOKEN" in result.output


def test_doctor_reports_limits(monkeypatch, tmp_path: Path):
    _env(monkeypatch, tmp_path)
    with respx.mock(assert_all_called=True) as router:
        _mock_public(router)
        result = RUNNER.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    assert "Graphia 0.1.0" in result.output
    assert "120 uploads/hour" in result.output
    assert "ada@example.com (member)" in result.output


def test_doctor_without_a_token(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("GRAPHIA_SERVER", "https://graphia.test")
    monkeypatch.setenv("GRAPHIA_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("GRAPHIA_TOKEN", raising=False)
    with respx.mock(assert_all_called=True) as router:
        _mock_public(router, me=False)
        result = RUNNER.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    assert "not signed in" in result.output


def test_convert_dry_run_lists_without_uploading(monkeypatch, tmp_path: Path):
    _env(monkeypatch, tmp_path)
    source = tmp_path / "deck.pptx"
    source.write_bytes(b"deck")
    out = tmp_path / "out"

    with respx.mock(assert_all_called=True) as router:
        _mock_public(router)
        result = RUNNER.invoke(
            app,
            ["convert", str(source), "--to", "pdf", "--out", str(out), "--dry-run", "--json"],
        )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["dryRun"] is True
    assert data["ready"] == 1
    assert data["files"][0]["operation"] == "pptx_to_pdf"


def test_convert_prints_a_json_report(monkeypatch, tmp_path: Path):
    _env(monkeypatch, tmp_path)
    source = tmp_path / "deck.pptx"
    source.write_bytes(b"deck")
    out = tmp_path / "out"

    with respx.mock(assert_all_called=True) as router:
        _mock_public(router)
        router.post("https://graphia.test/api/conversions").mock(
            return_value=httpx.Response(
                201,
                json={
                    "job": _job(),
                    "upload": {
                        "url": "https://r2.test/upload/job-1",
                        "method": "PUT",
                        "headers": {"Content-Type": "application/octet-stream"},
                        "expiresAt": int(time.time() * 1000) + 600_000,
                    },
                },
            )
        )
        router.put("https://r2.test/upload/job-1").mock(
            return_value=httpx.Response(200)
        )
        router.post(
            "https://graphia.test/api/conversions/job-1/complete-upload"
        ).mock(return_value=httpx.Response(200, json=_job()))
        router.get("https://graphia.test/api/conversions/job-1").mock(
            return_value=httpx.Response(200, json=_job("COMPLETED"))
        )
        router.get(
            "https://graphia.test/api/conversions/job-1/download"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "url": "https://r2.test/file/job-1",
                    "expiresAt": int(time.time() * 1000) + 300_000,
                },
            )
        )
        router.get("https://r2.test/file/job-1").mock(
            return_value=httpx.Response(200, content=b"%PDF-1.4")
        )

        result = RUNNER.invoke(
            app,
            ["convert", str(source), "--to", "pdf", "--out", str(out), "--json"],
        )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["converted"] == 1
    assert data["failed"] == 0
    assert (out / "deck.pdf").read_bytes() == b"%PDF-1.4"


def test_convert_requires_login(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("GRAPHIA_SERVER", "https://graphia.test")
    monkeypatch.setenv("GRAPHIA_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("GRAPHIA_TOKEN", raising=False)
    source = tmp_path / "deck.pptx"
    source.write_bytes(b"deck")

    result = RUNNER.invoke(app, ["convert", str(source), "--to", "pdf"])

    assert result.exit_code == 2
    assert "graphia login" in (result.output + getattr(result, "stderr", ""))
