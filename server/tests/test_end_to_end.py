from __future__ import annotations

import time

from processor.runner import run_job
from tests.conftest import signup


def test_full_txt_conversion_lifecycle(
    api_client,
    processor_client,
    db,
    fake_storage,
    monkeypatch,
):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)

    def runner(job_id):
        run_job(job_id, session_factory=db.session_factory, storage=fake_storage)

    def trigger(job_id):
        response = processor_client.post(
            "/internal/process",
            json={"jobId": str(job_id)},
            headers={"X-Internal-Token": "test-internal-token"},
        )
        if response.status_code in {200, 202}:
            return True, None
        return False, response.json().get("error", "Trigger failed.")

    monkeypatch.setattr("processor.router.run_job", runner)
    monkeypatch.setattr("app.services.processor_client.trigger", trigger)

    signup(api_client)
    created = api_client.post(
        "/api/conversions",
        json={
            "operation": "txt_to_markdown",
            "originalFilename": "notes.txt",
            "fileSize": 26,
            "contentType": "text/plain",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    job_id = body["job"]["id"]
    key = body["upload"]["url"].split("?")[0].removeprefix("https://fake-r2.test/")
    fake_storage.seed(key, b"Hello from the end-to-end test.\n", "text/plain")

    completed_upload = api_client.post(f"/api/conversions/{job_id}/complete-upload")
    assert completed_upload.status_code == 200, completed_upload.text

    current = completed_upload.json()
    for _ in range(60):
        if current["status"] in {"COMPLETED", "FAILED"}:
            break
        time.sleep(0.1)
        current = api_client.get(f"/api/conversions/{job_id}").json()

    assert current["status"] == "COMPLETED", current
    assert current["downloadAvailable"] is True
    assert current["outputFilename"] == "notes.md"

    download = api_client.get(f"/api/conversions/{job_id}/download")
    assert download.status_code == 200, download.text
    assert download.json()["url"].startswith("https://fake-r2.test/")
