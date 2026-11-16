from __future__ import annotations

from sqlalchemy import select

from core.config import settings
from core.models.conversion_job import ConversionJob
from core.models.enums import ConversionOperation
from core.models.user import User
from tests.conftest import (
    FakeZitadel,
    TestDatabase,
    authenticate,
    create_user,
    make_job,
)


def begin_login(
    client,
    fake: FakeZitadel,
    *,
    path: str = "/api/auth/login?next=/",
) -> str:
    response = client.get(path, follow_redirects=False)
    assert response.status_code == 302, response.text
    assert response.headers["location"].startswith("https://zitadel.test/authorize?")
    assert fake.state
    return fake.state


def complete_login(client, fake: FakeZitadel, *, state: str | None = None):
    return client.get(
        f"/api/auth/callback?code=test-code&state={state or fake.state}",
        follow_redirects=False,
    )


def test_login_redirects_to_zitadel_and_callback_creates_session(
    api_client,
    fake_zitadel: FakeZitadel,
    db: TestDatabase,
):
    state = begin_login(api_client, fake_zitadel, path="/api/auth/login?next=/conversions/abc")
    assert fake_zitadel.last_authorize is not None
    assert fake_zitadel.last_authorize["prompt"] is None
    assert api_client.cookies.get("graphia_oauth")

    response = complete_login(api_client, fake_zitadel, state=state)
    assert response.status_code == 302
    assert response.headers["location"] == "/conversions/abc"
    assert api_client.cookies.get(settings.session_cookie_name)

    me = api_client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "ada@example.com"

    session = db.session_factory()
    try:
        user = session.scalar(select(User).where(User.email == "ada@example.com"))
        assert user is not None
        assert user.zitadel_sub == "zitadel-sub-1"
        assert user.idp_issuer == "https://zitadel.test"
    finally:
        session.close()


def test_signup_uses_zitadel_create_prompt(api_client, fake_zitadel: FakeZitadel):
    response = api_client.get("/api/auth/signup?next=/", follow_redirects=False)
    assert response.status_code == 302
    assert fake_zitadel.last_authorize is not None
    assert fake_zitadel.last_authorize["prompt"] == "create"


def test_callback_rejects_bad_state(api_client, fake_zitadel: FakeZitadel):
    begin_login(api_client, fake_zitadel)
    response = complete_login(api_client, fake_zitadel, state="wrong-state")
    assert response.status_code == 302
    assert "/login?error=" in response.headers["location"]
    assert api_client.get("/api/auth/me").status_code == 401


def test_existing_user_is_adopted_by_email(
    api_client,
    fake_zitadel: FakeZitadel,
    db: TestDatabase,
):
    existing = create_user(db, email="ada@example.com", name="Local Ada")
    job = make_job(db, owner=existing, operation=ConversionOperation.TXT_TO_MARKDOWN)

    begin_login(api_client, fake_zitadel)
    response = complete_login(api_client, fake_zitadel)
    assert response.status_code == 302

    session = db.session_factory()
    try:
        refreshed = session.get(User, existing.id)
        assert refreshed is not None
        assert refreshed.zitadel_sub == "zitadel-sub-1"
        assert refreshed.idp_issuer == "https://zitadel.test"
        adopted_job = session.get(ConversionJob, job.id)
        assert adopted_job is not None
        assert adopted_job.owner_id == existing.id
    finally:
        session.close()


def test_email_linked_to_another_subject_is_rejected(
    api_client,
    fake_zitadel: FakeZitadel,
    db: TestDatabase,
):
    existing = create_user(db, email="ada@example.com")
    session = db.session_factory()
    try:
        row = session.get(User, existing.id)
        row.idp_issuer = "https://zitadel.test"
        row.zitadel_sub = "another-subject"
        session.commit()
    finally:
        session.close()

    begin_login(api_client, fake_zitadel)
    response = complete_login(api_client, fake_zitadel)
    assert response.status_code == 302
    assert "/login?error=" in response.headers["location"]
    assert api_client.get("/api/auth/me").status_code == 401


def test_missing_email_is_rejected(api_client, fake_zitadel: FakeZitadel):
    fake_zitadel.claims.pop("email")
    begin_login(api_client, fake_zitadel)
    response = complete_login(api_client, fake_zitadel)
    assert response.status_code == 302
    assert "/login?error=" in response.headers["location"]


def test_unverified_email_is_rejected(api_client, fake_zitadel: FakeZitadel):
    fake_zitadel.claims["email_verified"] = False
    begin_login(api_client, fake_zitadel)
    response = complete_login(api_client, fake_zitadel)
    assert response.status_code == 302
    assert "/login?error=" in response.headers["location"]


def test_logout_returns_zitadel_end_session_url(
    api_client,
    fake_zitadel: FakeZitadel,
    db: TestDatabase,
):
    authenticate(api_client, db)
    response = api_client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["logoutUrl"].startswith("https://zitadel.test/logout")
    assert api_client.get("/api/auth/me").status_code == 401


def test_me_requires_session(api_client):
    response = api_client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"] == "Not signed in."
