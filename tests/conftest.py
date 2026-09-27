"""
conftest.py — pytest fixtures for the diet planner test suite.

Test environment strategy:
  * ENVIRONMENT=test        -> rate limiting disabled
  * temp SQLite database    -> same code path as cloud Postgres
  * temp uploads folder     -> same code path as cloud object storage
  * fresh schema per test   -> full isolation between tests
"""

import os
import tempfile
import uuid

# ---------------------------------------------------------------------------
# Configure environment BEFORE any backend import (settings are cached).
# ---------------------------------------------------------------------------
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/test_diet_{os.getpid()}.db"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="diet_uploads_")
os.environ["STORAGE_PROVIDER"] = "local"
os.environ["SECRET_KEY"] = "test-only-secret-key"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
os.environ["AI_PROVIDER"] = "rule_based"
os.environ["AI_API_KEY"] = ""
os.environ["AI_API_URL"] = ""

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.database import Base, engine


@pytest.fixture()
def client():
    """Fresh database + TestClient for every test (full isolation)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Helper functions shared by tests
# ---------------------------------------------------------------------------
PASSWORD = "Demo@12345"


def register(client, email, name="Test User", password=PASSWORD):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": name},
    )


def login(client, email, password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def unique_email(base="user"):
    return f"{base}-{uuid.uuid4().hex[:8]}@test.com"


@pytest.fixture()
def user(client):
    """Registered + logged-in user. Returns (headers, user_dict)."""
    email = unique_email()
    r = register(client, email=email, name="Testy Planner")
    assert r.status_code == 201, r.text
    token = login(client, email).json()["access_token"]
    return auth_headers(token), r.json()


@pytest.fixture()
def user_with_profile(client, user):
    """User with a completed profile. Returns (headers, user_dict, profile)."""
    headers, user_dict = user
    payload = {
        "age": 27, "height_cm": 168, "weight_kg": 66,
        "activity_level": "moderate", "dietary_preference": "vegetarian",
        "goal": "weight_loss", "allergies": "nuts", "meals_per_day": 3,
    }
    r = client.put("/api/profile", json=payload, headers=headers)
    assert r.status_code == 200, r.text
    return headers, user_dict, r.json()


def make_png(bytes_extra: bytes = b"") -> bytes:
    """Minimal byte sequence that passes PNG magic-byte validation."""
    return b"\x89PNG\r\n\x1a\n" + bytes_extra


PROFILE_PAYLOAD = {
    "age": 30, "height_cm": 172, "weight_kg": 70,
    "activity_level": "light", "dietary_preference": "vegan",
    "goal": "maintenance", "allergies": "", "meals_per_day": 3,
}
