"""
test_auth.py — registration, login, logout and protected-route access.
"""

import uuid

from tests.conftest import PASSWORD, auth_headers, login, register, unique_email


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
def test_register_new_user_201(client):
    r = register(client, email=unique_email())
    assert r.status_code == 201
    body = r.json()
    assert body["email"].endswith("@test.com")
    assert "password" not in body and "password_hash" not in body  # never leak hashes


def test_register_duplicate_email_409(client):
    email = unique_email()
    assert register(client, email=email).status_code == 201
    r = register(client, email=email)
    assert r.status_code == 409


def test_register_weak_password_422(client):
    r = client.post(
        "/api/auth/register",
        json={"email": unique_email(), "password": "short", "name": "Weak PW"},
    )
    assert r.status_code == 422


def test_register_invalid_email_422(client):
    r = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": PASSWORD, "name": "Bad Email"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
def test_login_valid_credentials_200(client):
    email = unique_email()
    register(client, email=email)
    r = login(client, email)
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["token_type"] == "bearer"
    assert body["user"]["email"] == email


def test_login_wrong_password_401(client):
    email = unique_email()
    register(client, email=email)
    r = login(client, email, password="WrongPassword1")
    assert r.status_code == 401


def test_login_unknown_email_401(client):
    r = login(client, f"ghost-{uuid.uuid4().hex[:6]}@test.com")
    assert r.status_code == 401
    # same message as wrong-password -> no user enumeration
    assert r.json()["detail"] == "Invalid email or password"


# ---------------------------------------------------------------------------
# Token-protected access
# ---------------------------------------------------------------------------
def test_me_requires_token_401(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_valid_token_200(client):
    email = unique_email()
    register(client, email=email)
    token = login(client, email).json()["access_token"]
    r = client.get("/api/auth/me", headers=auth_headers(token))
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_me_with_garbage_token_401(client):
    r = client.get("/api/auth/me", headers=auth_headers("not.a.jwt"))
    assert r.status_code == 401


def test_logout_validates_token(client):
    email = unique_email()
    register(client, email=email)
    token = login(client, email).json()["access_token"]
    assert client.post("/api/auth/logout", headers=auth_headers(token)).status_code == 200
    # logout is stateless: the token itself is still technically valid,
    # the client must discard it (documented behaviour).
    assert client.post("/api/auth/logout", headers=auth_headers(token)).status_code == 200
