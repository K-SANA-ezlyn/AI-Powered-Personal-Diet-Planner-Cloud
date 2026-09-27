"""
test_profile.py — profile upsert, validation and ownership.
"""

from tests.conftest import PROFILE_PAYLOAD, auth_headers, login, register, unique_email


def _make_user(client):
    email = unique_email()
    register(client, email=email)
    token = login(client, email).json()["access_token"]
    return auth_headers(token)


def test_get_profile_before_creation_404(client, user):
    headers, _ = user
    assert client.get("/api/profile", headers=headers).status_code == 404


def test_create_profile_200(client, user):
    headers, _ = user
    r = client.put("/api/profile", json=PROFILE_PAYLOAD, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["dietary_preference"] == "vegan"
    assert body["goal"] == "maintenance"


def test_update_profile_partial_fields(client, user_with_profile):
    headers, _, profile = user_with_profile
    r = client.put("/api/profile", json={"goal": "fitness"}, headers=headers)
    assert r.status_code == 422  # PUT requires the full payload (documented contract)


def test_update_profile_full_payload_200(client, user_with_profile):
    headers, _, profile = user_with_profile
    payload = {**PROFILE_PAYLOAD, "dietary_preference": "non_vegetarian", "goal": "weight_gain"}
    r = client.put("/api/profile", json=payload, headers=headers)
    assert r.status_code == 200
    assert r.json()["dietary_preference"] == "non_vegetarian"


def test_profile_age_out_of_range_422(client, user):
    headers, _ = user
    r = client.put("/api/profile", json={**PROFILE_PAYLOAD, "age": 5}, headers=headers)
    assert r.status_code == 422


def test_profile_unknown_allergy_422(client, user):
    headers, _ = user
    r = client.put("/api/profile", json={**PROFILE_PAYLOAD, "allergies": "pineapple"}, headers=headers)
    assert r.status_code == 422


def test_profile_requires_auth_401(client):
    assert client.put("/api/profile", json=PROFILE_PAYLOAD).status_code == 401
