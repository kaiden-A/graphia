from __future__ import annotations

import itertools
import time
from pathlib import Path

import httpx
import respx

from graphia_cli.client import GraphiaClient
from graphia_cli.errors import AuthError, RateLimitError
from graphia_cli.operations import Catalog
from graphia_cli.output import Reporter
from graphia_cli.planner import build_plan
from graphia_cli.runner import run_plan


def _job(
    job_id: str,
    *,
    status: str = "PENDING",
    filename: str = "a.pptx",
    error: str | None = None,
) -> dict:
    completed = status == "COMPLETED"
    return {
        "id": job_id,
        "operation": "pptx_to_pdf",
        "operationLabel": "PPTX to PDF",
        "originalFilename": filename,
        "status": status,
        "errorMessage": error,
        "fileSize": 1,
        "outputSize": 8 if completed else None,
        "outputFilename": "a.pdf" if completed else None,
        "uploadCompleted": status != "PENDING",
        "downloadAvailable": completed,
        "downloadRequiresAccount": False,
        "attempts": 0 if status == "PENDING" else 1,
        "createdAt": int(time.time() * 1000),
        "startedAt": None,
        "completedAt": None,
        "expiresAt": int(time.time() * 1000) + 86_400_000,
    }


def _ticket(job_id: str) -> dict:
    return {
        "url": f"https://r2.test/upload/{job_id}",
        "method": "PUT",
        "headers": {"Content-Type": "application/octet-stream"},
        "expiresAt": int(time.time() * 1000) + 600_000,
    }


def _plan(tmp_path: Path, catalog: Catalog, names: tuple[str, ...] = ("a.pptx",)):
    root = tmp_path / "decks"
    root.mkdir(parents=True, exist_ok=True)
    for name in names:
        (root / name).write_bytes(b"deck")
    out = tmp_path / "out"
    return build_plan(
        [root],
        target="pdf",
        operation=None,
        out=out,
        recursive=True,
        include_hidden=False,
        overwrite=False,
        max_upload_bytes=25 * 1024 * 1024,
        catalog=catalog,
    )


def _client() -> GraphiaClient:
    return GraphiaClient("https://graphia.test", token="session-token")


def test_single_file_conversion_downloads_output(tmp_path: Path, catalog: Catalog):
    plan = _plan(tmp_path, catalog)
    job_id = "job-1"

    with respx.mock(assert_all_called=True) as router:
        router.post("https://graphia.test/api/conversions").mock(
            return_value=httpx.Response(
                201,
                json={"job": _job(job_id), "upload": _ticket(job_id)},
            )
        )
        router.put(f"https://r2.test/upload/{job_id}").mock(
            return_value=httpx.Response(200)
        )
        router.post(
            f"https://graphia.test/api/conversions/{job_id}/complete-upload"
        ).mock(return_value=httpx.Response(200, json=_job(job_id)))
        router.get(f"https://graphia.test/api/conversions/{job_id}").mock(
            side_effect=[
                httpx.Response(200, json=_job(job_id, status="PROCESSING")),
                httpx.Response(
                    200,
                    json=_job(job_id, status="COMPLETED"),
                ),
            ]
        )
        router.get(
            f"https://graphia.test/api/conversions/{job_id}/download"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "url": f"https://r2.test/file/{job_id}",
                    "expiresAt": int(time.time() * 1000) + 300_000,
                },
            )
        )
        router.get(f"https://r2.test/file/{job_id}").mock(
            return_value=httpx.Response(200, content=b"%PDF-1.4")
        )

        with _client() as client:
            outcome = run_plan(plan, client, jobs=1, reporter=Reporter(quiet=True))

    assert outcome.fatal is None
    assert len(outcome.results) == 1
    assert outcome.results[0].state == "converted"
    assert outcome.results[0].job_id == job_id
    assert (plan.output_root / "a.pdf").read_bytes() == b"%PDF-1.4"


def test_failed_conversion_is_reported(tmp_path: Path, catalog: Catalog):
    plan = _plan(tmp_path, catalog)
    job_id = "job-2"

    with respx.mock(assert_all_called=True) as router:
        router.post("https://graphia.test/api/conversions").mock(
            return_value=httpx.Response(
                201,
                json={"job": _job(job_id), "upload": _ticket(job_id)},
            )
        )
        router.put(f"https://r2.test/upload/{job_id}").mock(
            return_value=httpx.Response(200)
        )
        router.post(
            f"https://graphia.test/api/conversions/{job_id}/complete-upload"
        ).mock(return_value=httpx.Response(200, json=_job(job_id)))
        router.get(f"https://graphia.test/api/conversions/{job_id}").mock(
            return_value=httpx.Response(
                200,
                json=_job(
                    job_id,
                    status="FAILED",
                    error="The slide deck could not be read.",
                ),
            )
        )

        with _client() as client:
            outcome = run_plan(plan, client, jobs=1, reporter=Reporter(quiet=True))

    assert outcome.fatal is None
    assert outcome.results[0].state == "failed"
    assert "could not be read" in (outcome.results[0].error or "")


def test_upload_failure_deletes_the_pending_job(tmp_path: Path, catalog: Catalog):
    plan = _plan(tmp_path, catalog)
    job_id = "job-3"

    with respx.mock(assert_all_called=True) as router:
        router.post("https://graphia.test/api/conversions").mock(
            return_value=httpx.Response(
                201,
                json={"job": _job(job_id), "upload": _ticket(job_id)},
            )
        )
        router.put(f"https://r2.test/upload/{job_id}").mock(
            return_value=httpx.Response(500)
        )
        delete = router.delete(
            f"https://graphia.test/api/conversions/{job_id}"
        ).mock(return_value=httpx.Response(204))

        with _client() as client:
            outcome = run_plan(plan, client, jobs=1, reporter=Reporter(quiet=True))

    assert delete.called
    assert outcome.results[0].state == "failed"
    assert "upload" in (outcome.results[0].error or "").lower()


def test_auth_error_stops_the_batch(tmp_path: Path, catalog: Catalog):
    plan = _plan(tmp_path, catalog, names=("a.pptx", "b.pptx"))

    with respx.mock(assert_all_called=True) as router:
        router.post("https://graphia.test/api/conversions").mock(
            return_value=httpx.Response(
                401,
                json={"error": "Your session has expired. Please sign in again."},
            )
        )

        with _client() as client:
            outcome = run_plan(plan, client, jobs=2, reporter=Reporter(quiet=True))

    assert isinstance(outcome.fatal, AuthError)
    assert all(result.state == "cancelled" for result in outcome.results)


def test_rate_limit_stops_the_batch(tmp_path: Path, catalog: Catalog):
    plan = _plan(tmp_path, catalog)

    with respx.mock(assert_all_called=True) as router:
        router.post("https://graphia.test/api/conversions").mock(
            return_value=httpx.Response(
                429,
                json={"error": "Too many uploads from this network. Try again later."},
            )
        )

        with _client() as client:
            outcome = run_plan(plan, client, jobs=1, reporter=Reporter(quiet=True))

    assert isinstance(outcome.fatal, RateLimitError)
    assert outcome.results[0].state == "cancelled"


def test_two_files_are_converted_with_dynamic_routes(tmp_path: Path, catalog: Catalog):
    plan = _plan(tmp_path, catalog, names=("a.pptx", "b.pptx"))
    counter = itertools.count(1)
    created: list[str] = []

    def create(_request: httpx.Request) -> httpx.Response:
        job_id = f"job-{next(counter)}"
        created.append(job_id)
        return httpx.Response(
            201,
            json={"job": _job(job_id), "upload": _ticket(job_id)},
        )

    def complete(request: httpx.Request) -> httpx.Response:
        job_id = request.url.path.split("/")[3]
        return httpx.Response(200, json=_job(job_id))

    def status(request: httpx.Request) -> httpx.Response:
        job_id = request.url.path.split("/")[3]
        return httpx.Response(200, json=_job(job_id, status="COMPLETED"))

    def download(request: httpx.Request) -> httpx.Response:
        job_id = request.url.path.split("/")[3]
        return httpx.Response(
            200,
            json={
                "url": f"https://r2.test/file/{job_id}",
                "expiresAt": int(time.time() * 1000) + 300_000,
            },
        )

    with respx.mock(assert_all_called=True) as router:
        router.post("https://graphia.test/api/conversions").mock(side_effect=create)
        router.put(url__regex=r"https://r2\.test/upload/job-\d+").mock(
            return_value=httpx.Response(200)
        )
        router.post(
            url__regex=r"https://graphia\.test/api/conversions/job-\d+/complete-upload"
        ).mock(side_effect=complete)
        router.get(
            url__regex=r"https://graphia\.test/api/conversions/job-\d+$"
        ).mock(side_effect=status)
        router.get(
            url__regex=r"https://graphia\.test/api/conversions/job-\d+/download"
        ).mock(side_effect=download)
        router.get(url__regex=r"https://r2\.test/file/job-\d+").mock(
            return_value=httpx.Response(200, content=b"%PDF-1.4")
        )

        with _client() as client:
            outcome = run_plan(plan, client, jobs=2, reporter=Reporter(quiet=True))

    assert len(created) == 2
    assert sorted(result.state for result in outcome.results) == ["converted", "converted"]
    assert (plan.output_root / "a.pdf").exists()
    assert (plan.output_root / "b.pdf").exists()
