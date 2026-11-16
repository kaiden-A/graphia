from __future__ import annotations

from core.models.enums import ConversionOperation, JobStatus
from tests.conftest import create_user, login, make_job, signup


def _metadata(**overrides):
    payload = {
        "operation": "txt_to_markdown",
        "originalFilename": "notes.txt",
        "fileSize": 12,
        "contentType": "text/plain",
    }
    payload.update(overrides)
    return payload


def test_operations_endpoint(api_client):
    response = api_client.get("/api/operations")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert ids == {
        "docx_to_pdf",
        "pdf_to_markdown",
        "txt_to_markdown",
        "markdown_to_pdf",
        "images_to_pdf",
    }


def test_create_conversion_returns_presigned_upload(api_client, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    signup(api_client)

    response = api_client.post("/api/conversions", json=_metadata())
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["job"]["status"] == "PENDING"
    assert data["job"]["uploadCompleted"] is False
    assert data["upload"]["url"].startswith("https://fake-r2.test/")
    assert data["upload"]["headers"]["Content-Type"] == "text/plain"


def test_create_markdown_accepts_text_plain(api_client, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    signup(api_client)
    response = api_client.post(
        "/api/conversions",
        json=_metadata(
            operation="markdown_to_pdf",
            originalFilename="notes.md",
            contentType="text/plain",
        ),
    )
    assert response.status_code == 201, response.text
    assert response.json()["upload"]["headers"]["Content-Type"] == "text/markdown"


def test_create_rejects_wrong_extension(api_client, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    signup(api_client)
    response = api_client.post(
        "/api/conversions",
        json=_metadata(operation="docx_to_pdf", originalFilename="notes.txt"),
    )
    assert response.status_code == 415


def test_create_rejects_oversize(api_client, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    signup(api_client)
    response = api_client.post(
        "/api/conversions",
        json=_metadata(fileSize=26 * 1024 * 1024),
    )
    assert response.status_code == 413


def test_complete_upload_triggers_processor(api_client, db, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    calls: list[str] = []

    def fake_trigger(job_id):
        calls.append(str(job_id))
        return True, None

    monkeypatch.setattr("app.services.processor_client.trigger", fake_trigger)
    signup(api_client)

    created = api_client.post("/api/conversions", json=_metadata()).json()
    job_id = created["job"]["id"]
    key = created["upload"]["url"].split("?")[0].removeprefix("https://fake-r2.test/")
    fake_storage.seed(key, b"Hello\n\nWorld\n", "text/plain")

    response = api_client.post(f"/api/conversions/{job_id}/complete-upload")
    assert response.status_code == 200, response.text
    assert response.json()["uploadCompleted"] is True
    assert calls == [job_id]


def test_trigger_failure_marks_job_failed(api_client, db, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    monkeypatch.setattr(
        "app.services.processor_client.trigger",
        lambda _job_id: (False, "The conversion service is unavailable. Please try again."),
    )
    signup(api_client)

    created = api_client.post("/api/conversions", json=_metadata()).json()
    job_id = created["job"]["id"]
    key = created["upload"]["url"].split("?")[0].removeprefix("https://fake-r2.test/")
    fake_storage.seed(key, b"Hello\n\nWorld\n", "text/plain")

    response = api_client.post(f"/api/conversions/{job_id}/complete-upload")
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
    assert "unavailable" in response.json()["errorMessage"]


def test_ownership_is_enforced(api_client, db, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    monkeypatch.setattr("app.services.processor_client.trigger", lambda _job_id: (True, None))
    owner = create_user(db, email="owner@example.com")
    other = create_user(db, email="other@example.com")
    job = make_job(db, owner=owner, upload_completed=True)
    fake_storage.seed(job.input_key, b"Hello\n", "text/plain")

    login(api_client, other.email, "correct-horse")
    response = api_client.get(f"/api/conversions/{job.id}")
    assert response.status_code == 404


def test_download_returns_signed_url(api_client, db, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    user = create_user(db)
    job = make_job(
        db,
        owner=user,
        operation=ConversionOperation.IMAGES_TO_PDF,
        status=JobStatus.COMPLETED,
        with_output=True,
    )
    login(api_client, user.email, "correct-horse")

    response = api_client.get(f"/api/conversions/{job.id}/download")
    assert response.status_code == 200
    assert response.json()["url"].startswith("https://fake-r2.test/")


def test_download_expired_job_is_gone(api_client, db, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    user = create_user(db)
    job = make_job(
        db,
        owner=user,
        operation=ConversionOperation.IMAGES_TO_PDF,
        status=JobStatus.COMPLETED,
        with_output=True,
        expires_in_hours=-1,
    )
    login(api_client, user.email, "correct-horse")

    response = api_client.get(f"/api/conversions/{job.id}/download")
    assert response.status_code == 410


def test_delete_removes_job_and_objects(api_client, db, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    user = create_user(db)
    job = make_job(db, owner=user, operation=ConversionOperation.TXT_TO_MARKDOWN)
    fake_storage.seed(job.input_key, b"hello", "text/plain")
    login(api_client, user.email, "correct-horse")

    response = api_client.delete(f"/api/conversions/{job.id}")
    assert response.status_code == 204
    assert job.input_key not in fake_storage.objects

    check = api_client.get(f"/api/conversions/{job.id}")
    assert check.status_code == 404


def test_delete_processing_job_is_conflict(api_client, db, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    user = create_user(db)
    job = make_job(db, owner=user, status=JobStatus.PROCESSING)
    login(api_client, user.email, "correct-horse")

    response = api_client.delete(f"/api/conversions/{job.id}")
    assert response.status_code == 409


def test_active_job_limit(api_client, db, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    signup(api_client)
    for _ in range(3):
        response = api_client.post("/api/conversions", json=_metadata())
        assert response.status_code == 201

    response = api_client.post("/api/conversions", json=_metadata())
    assert response.status_code == 429
