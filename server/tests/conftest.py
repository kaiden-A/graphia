from __future__ import annotations

import os

os.environ["APP_ENV"] = "test"
os.environ["APP_SECRET"] = "test-secret"
os.environ["DB_SCHEMA"] = "public"
os.environ["INTERNAL_TOKEN"] = "test-internal-token"
os.environ["SIGNUP_INVITE_CODE"] = "test-invite"
os.environ["SIGNUP_ENABLED"] = "true"
os.environ["COOKIE_SECURE"] = "false"
os.environ["PROCESSOR_URL"] = "http://processor.test"
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"
if os.getenv("RUN_INTEGRATION") != "1":
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["R2_BUCKET"] = "test-bucket"

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as api_app
from app.services.rate_limit import login_limiter, signup_limiter, upload_limiter
from core.database import get_db
from core.models import Base
from core.models.conversion_job import ConversionJob
from core.models.enums import ConversionOperation, JobStatus
from core.models.user import User
from core.security import hash_password
from core.utils import utcnow
from processor.main import app as processor_app


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def seed(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = (data, content_type)

    def put_file(self, key: str, path: Path, content_type: str) -> None:
        self.objects[key] = (path.read_bytes(), content_type)

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = (data, content_type)

    def download_to(self, key: str, path: Path) -> None:
        data, _ = self.objects[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def head(self, key: str):
        if key not in self.objects:
            return None
        data, content_type = self.objects[key]
        from core.storage import ObjectInfo

        return ObjectInfo(size=len(data), content_type=content_type, etag='"fake"')

    def read_range(self, key: str, start: int, end: int) -> bytes:
        data, _ = self.objects[key]
        return data[start : end + 1]

    def presign_put(self, key: str, content_type: str, expires_in: int) -> str:
        return f"https://fake-r2.test/{key}?signature=put&expires={expires_in}"

    def presign_get(self, key: str, filename: str, expires_in: int) -> str:
        return f"https://fake-r2.test/{key}?signature=get&filename={filename}&expires={expires_in}"

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)


@dataclass
class TestDatabase:
    engine: object
    session_factory: sessionmaker


@pytest.fixture()
def db(tmp_path) -> TestDatabase:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def attach_public_schema(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("ATTACH DATABASE ':memory:' AS public")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield TestDatabase(engine=engine, session_factory=factory)
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def reset_limiters():
    login_limiter.reset()
    signup_limiter.reset()
    upload_limiter.reset()
    yield


@pytest.fixture()
def fake_storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture()
def api_client(db: TestDatabase):
    def override_get_db():
        session = db.session_factory()
        try:
            yield session
        finally:
            session.close()

    api_app.dependency_overrides[get_db] = override_get_db
    with TestClient(api_app, base_url="http://testserver") as client:
        yield client
    api_app.dependency_overrides.clear()


@pytest.fixture()
def processor_client(db: TestDatabase):
    def override_get_db():
        session = db.session_factory()
        try:
            yield session
        finally:
            session.close()

    processor_app.dependency_overrides[get_db] = override_get_db
    with TestClient(processor_app, base_url="http://processor.test") as client:
        yield client
    processor_app.dependency_overrides.clear()


def create_user(
    db: TestDatabase,
    *,
    email: str = "ada@example.com",
    password: str = "correct-horse",
    name: str = "Ada",
) -> User:
    session = db.session_factory()
    try:
        user = User(email=email, name=name, password_hash=hash_password(password))
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def login(client: TestClient, email: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text


def signup(
    client: TestClient,
    *,
    email: str = "ada@example.com",
    password: str = "correct-horse",
    name: str = "Ada",
) -> None:
    response = client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "password": password,
            "name": name,
            "inviteCode": "test-invite",
        },
    )
    assert response.status_code == 201, response.text


def make_job(
    db: TestDatabase,
    *,
    owner: User,
    operation: ConversionOperation = ConversionOperation.TXT_TO_MARKDOWN,
    status: JobStatus = JobStatus.PENDING,
    upload_completed: bool = True,
    with_output: bool = False,
    expires_in_hours: int = 1,
) -> ConversionJob:
    session = db.session_factory()
    try:
        job_id = __import__("uuid").uuid4()
        ext = {
            ConversionOperation.DOCX_TO_PDF: "docx",
            ConversionOperation.PDF_TO_MARKDOWN: "pdf",
            ConversionOperation.TXT_TO_MARKDOWN: "txt",
            ConversionOperation.MARKDOWN_TO_PDF: "md",
            ConversionOperation.IMAGES_TO_PDF: "png",
        }[operation]
        now = utcnow()
        job = ConversionJob(
            id=job_id,
            owner_id=owner.id,
            operation=operation,
            original_filename=f"sample.{ext}",
            input_key=f"conversions/{owner.id}/{job_id}/input/source.{ext}",
            output_key=(
                f"conversions/{owner.id}/{job_id}/output/result.pdf" if with_output else None
            ),
            status=status,
            file_size=10,
            content_type="text/plain",
            upload_completed_at=now if upload_completed else None,
            created_at=now,
            expires_at=now + timedelta(hours=expires_in_hours),
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job
    finally:
        session.close()
