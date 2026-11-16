from __future__ import annotations

from tests.conftest import create_user, login, signup


def test_signup_requires_invite_code(api_client):
    response = api_client.post(
        "/api/auth/signup",
        json={
            "email": "new@example.com",
            "password": "correct-horse",
            "name": "New",
            "inviteCode": "wrong",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"] == "The invite code is not valid."


def test_signup_login_me_logout(api_client):
    signup(api_client, email="ada@example.com", name="Ada Lovelace")

    me = api_client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "ada@example.com"
    assert me.json()["name"] == "Ada Lovelace"

    assert api_client.post("/api/auth/logout").status_code == 204
    assert api_client.get("/api/auth/me").status_code == 401

    login(api_client, "ada@example.com", "correct-horse")
    assert api_client.get("/api/auth/me").status_code == 200


def test_login_rejects_wrong_password(api_client, db):
    create_user(db, email="ada@example.com", password="correct-horse")
    response = api_client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == "Email or password is incorrect."


def test_duplicate_signup_is_rejected(api_client):
    signup(api_client, email="ada@example.com")
    response = api_client.post(
        "/api/auth/signup",
        json={
            "email": "ada@example.com",
            "password": "correct-horse",
            "inviteCode": "test-invite",
        },
    )
    assert response.status_code == 409


def test_me_requires_session(api_client):
    response = api_client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"] == "Not signed in."
