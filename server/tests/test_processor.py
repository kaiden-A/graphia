from __future__ import annotations

import threading

from core.models.conversion_job import ConversionJob
from core.models.enums import ConversionOperation, JobStatus
from processor.runner import run_job
from tests.conftest import create_user, make_job


def test_processor_claims_pending_job(processor_client, db, monkeypatch):
    user = create_user(db)
    job = make_job(db, owner=user, operation=ConversionOperation.TXT_TO_MARKDOWN)
    seen: list[str] = []
    submitted = threading.Event()

    def fake_run(job_id):
        seen.append(str(job_id))
        submitted.set()

    monkeypatch.setattr("processor.router.run_job", fake_run)

    response = processor_client.post(
        "/internal/process",
        json={"jobId": str(job.id)},
        headers={"X-Internal-Token": "test-internal-token"},
    )
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "accepted"
    assert submitted.wait(2)
    assert seen == [str(job.id)]

    session = db.session_factory()
    try:
        refreshed = session.get(ConversionJob, job.id)
        assert refreshed.status is JobStatus.PROCESSING
        assert refreshed.attempts == 1
    finally:
        session.close()


def test_processor_rejects_bad_token(processor_client, db):
    user = create_user(db)
    job = make_job(db, owner=user)
    response = processor_client.post(
        "/internal/process",
        json={"jobId": str(job.id)},
        headers={"X-Internal-Token": "wrong"},
    )
    assert response.status_code == 401


def test_processor_ignores_duplicate_trigger(processor_client, db, monkeypatch):
    user = create_user(db)
    job = make_job(db, owner=user, status=JobStatus.PROCESSING)
    monkeypatch.setattr("processor.router.run_job", lambda _job_id: None)
    response = processor_client.post(
        "/internal/process",
        json={"jobId": str(job.id)},
        headers={"X-Internal-Token": "test-internal-token"},
    )
    assert response.status_code == 202
    assert response.json()["status"] == "ignored"


def test_processor_requires_completed_upload(processor_client, db):
    user = create_user(db)
    job = make_job(db, owner=user, upload_completed=False)
    response = processor_client.post(
        "/internal/process",
        json={"jobId": str(job.id)},
        headers={"X-Internal-Token": "test-internal-token"},
    )
    assert response.status_code == 409


def test_runner_completes_txt_job(db, fake_storage):
    user = create_user(db)
    job = make_job(
        db,
        owner=user,
        operation=ConversionOperation.TXT_TO_MARKDOWN,
        status=JobStatus.PROCESSING,
    )
    fake_storage.seed(job.input_key, b"First paragraph.\n\nSecond paragraph.\n", "text/plain")

    run_job(job.id, session_factory=db.session_factory, storage=fake_storage)

    session = db.session_factory()
    try:
        refreshed = session.get(ConversionJob, job.id)
        assert refreshed.status is JobStatus.COMPLETED
        assert refreshed.output_key
        assert refreshed.output_key in fake_storage.objects
        data, content_type = fake_storage.objects[refreshed.output_key]
        assert b"First paragraph." in data
        assert content_type == "text/markdown"
    finally:
        session.close()


def test_runner_marks_invalid_docx_failed(db, fake_storage):
    user = create_user(db)
    job = make_job(
        db,
        owner=user,
        operation=ConversionOperation.DOCX_TO_PDF,
        status=JobStatus.PROCESSING,
    )
    fake_storage.seed(
        job.input_key,
        b"not a docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    run_job(job.id, session_factory=db.session_factory, storage=fake_storage)

    session = db.session_factory()
    try:
        refreshed = session.get(ConversionJob, job.id)
        assert refreshed.status is JobStatus.FAILED
        assert "valid DOCX" in refreshed.error_message
    finally:
        session.close()


def test_runner_ignores_completed_job(db, fake_storage):
    user = create_user(db)
    job = make_job(db, owner=user, status=JobStatus.COMPLETED, with_output=True)
    fake_storage.seed(job.input_key, b"hello", "text/plain")
    run_job(job.id, session_factory=db.session_factory, storage=fake_storage)

    session = db.session_factory()
    try:
        refreshed = session.get(ConversionJob, job.id)
        assert refreshed.status is JobStatus.COMPLETED
        assert refreshed.output_key == job.output_key
    finally:
        session.close()
