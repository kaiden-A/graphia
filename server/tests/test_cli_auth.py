from __future__ import annotations

import secrets
from datetime import timedelta

from sqlalchemy import select

from app.services.cli_services import challenge_for
from core.config import settings
from core.models.cli_auth import CliAuthRequest
from core.models.session import UserSession
from core.models.user import User
from core.security import hash_token
from core.utils import utcnow
from tests.conftest import (
    TestDatabase,
    authenticate,
    create_session_for_user,
    create_user,
)


def start_request(client, *, name: str = "test-laptop"):
    verifier = secrets.token_urlsafe(48)
    response = client.post(
        "/api/cli/requests",
        json={"name": name, "challenge": challenge_for(verifier)},
    )
    assert response.status_code == 201, response.text
    return response.json(), verifier


def test_config_endpoint_is_public_and_has_no_secrets(api_client):
    response = api_client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["appName"] == "Graphia"
    assert data["webUrl"] == "http://testserver"
    assert data["auth"]["mode"] == "browser-approval"
    assert data["limits"]["maxUploadMb"] == settings.max_upload_mb
    assert data["limits"]["maxActiveJobs"] == settings.max_active_jobs_per_user
    assert data["limits"]["uploadsPerHour"] == settings.uploads_per_hour_per_member
    assert "database" not in response.text.lower()
    assert "secret" not in response.text.lower()


def test_cli_request_reports_pending_until_approved(api_client, db: TestDatabase):
    created, verifier = start_request(api_client)
    code = created["code"]
    assert created["loginUrl"].startswith("http://testserver/cli?code=")

    status = api_client.get(f"/api/cli/requests/{code}")
    assert status.status_code == 200
    assert status.json()["name"] == "test-laptop"
    assert status.json()["status"] == "pending"

    pending = api_client.post("/api/cli/token", json={"code": code, "verifier": verifier})
    assert pending.status_code == 202
    assert pending.json() == {"status": "pending"}


def test_cli_approve_then_exchange_creates_member_session(api_client, db: TestDatabase):
    created, verifier = start_request(api_client)
    code = created["code"]
    user = authenticate(api_client, db, email="member@example.com", name="Member")

    approved = api_client.post(f"/api/cli/requests/{code}/approve")
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    exchanged = api_client.post(
        "/api/cli/token",
        json={"code": code, "verifier": verifier},
    )
    assert exchanged.status_code == 200, exchanged.text
    data = exchanged.json()
    assert data["user"]["email"] == "member@example.com"
    assert data["user"]["isGuest"] is False
    assert data["token"]

    api_client.headers.pop("Cookie", None)
    api_client.headers["Authorization"] = f"Bearer {data['token']}"
    me = api_client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "member@example.com"

    session = db.session_factory()
    try:
        row = session.scalar(
            select(UserSession).where(UserSession.user_id == user.id, UserSession.client == "cli")
        )
        assert row is not None
        assert row.label == "test-laptop"
    finally:
        session.close()


def test_cli_token_is_single_use(api_client, db: TestDatabase):
    created, verifier = start_request(api_client)
    code = created["code"]
    authenticate(api_client, db)
    api_client.post(f"/api/cli/requests/{code}/approve")

    first = api_client.post("/api/cli/token", json={"code": code, "verifier": verifier})
    assert first.status_code == 200
    second = api_client.post("/api/cli/token", json={"code": code, "verifier": verifier})
    assert second.status_code == 410


def test_cli_token_rejects_wrong_verifier(api_client, db: TestDatabase):
    created, _ = start_request(api_client)
    authenticate(api_client, db)
    api_client.post(f"/api/cli/requests/{created['code']}/approve")

    response = api_client.post(
        "/api/cli/token",
        json={"code": created["code"], "verifier": secrets.token_urlsafe(48)},
    )
    assert response.status_code == 401


def test_cli_request_can_be_denied(api_client, db: TestDatabase):
    created, verifier = start_request(api_client)
    authenticate(api_client, db)

    denied = api_client.post(f"/api/cli/requests/{created['code']}/deny")
    assert denied.status_code == 200
    assert denied.json()["status"] == "denied"

    response = api_client.post(
        "/api/cli/token",
        json={"code": created["code"], "verifier": verifier},
    )
    assert response.status_code == 403


def test_cli_request_expiry_is_enforced(api_client, db: TestDatabase):
    created, verifier = start_request(api_client)
    authenticate(api_client, db)
    api_client.post(f"/api/cli/requests/{created['code']}/approve")

    session = db.session_factory()
    try:
        row = session.scalar(
            select(CliAuthRequest).where(
                CliAuthRequest.code_hash == hash_token(created["code"])
            )
        )
        assert row is not None
        row.expires_at = utcnow() - timedelta(seconds=1)
        session.commit()
    finally:
        session.close()

    response = api_client.post(
        "/api/cli/token",
        json={"code": created["code"], "verifier": verifier},
    )
    assert response.status_code == 410


def test_guest_cannot_approve_cli_access(api_client):
    created, _ = start_request(api_client)
    guest = api_client.post("/api/auth/guest", follow_redirects=False)
    assert guest.status_code == 303

    response = api_client.post(f"/api/cli/requests/{created['code']}/approve")
    assert response.status_code == 403
    assert "member" in response.json()["error"].lower()


def test_guest_bearer_is_rejected(api_client, db: TestDatabase):
    user = create_user(db, email="guest@example.com")
    session = db.session_factory()
    try:
        row = session.get(User, user.id)
        row.is_guest = True
        session.commit()
    finally:
        session.close()

    api_client.headers["Authorization"] = f"Bearer {create_session_for_user(db, user)}"
    response = api_client.get("/api/auth/me")
    assert response.status_code == 403
    assert "member" in response.json()["error"].lower()


def test_bearer_member_can_create_a_conversion(api_client, db, fake_storage, monkeypatch):
    monkeypatch.setattr("app.routers.conversions_router.get_storage", lambda: fake_storage)
    user = create_user(db)
    api_client.headers["Authorization"] = f"Bearer {create_session_for_user(db, user)}"

    response = api_client.post(
        "/api/conversions",
        json={
            "operation": "txt_to_markdown",
            "originalFilename": "notes.txt",
            "fileSize": 12,
            "contentType": "text/plain",
        },
    )
    assert response.status_code == 201, response.text
