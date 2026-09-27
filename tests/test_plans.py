"""
test_plans.py — plan generation preview, saving and user isolation.
"""

from tests.conftest import PROFILE_PAYLOAD, auth_headers, login, register, unique_email


def _second_user(client):
    """Register + login a different user; return their auth headers."""
    email = unique_email("other")
    register(client, email=email)
    token = login(client, email).json()["access_token"]
    return auth_headers(token)


# ---------------------------------------------------------------------------
# Generation preview (not persisted)
# ---------------------------------------------------------------------------
def test_generate_plan_uses_profile(client, user_with_profile):
    headers, _, profile = user_with_profile
    r = client.post("/api/diet/generate-plan", json={}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["goal"] == profile["goal"]
    assert body["dietary_preference"] == profile["dietary_preference"]
    assert body["engine_used"] in {"rule_based", "ai_api"}
    assert "not medical" in body["disclaimer"]


def test_generate_plan_with_overrides(client, user_with_profile):
    headers, _, _ = user_with_profile
    r = client.post(
        "/api/diet/generate-plan",
        json={"goal": "weight_gain", "dietary_preference": "non_vegetarian"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["goal"] == "weight_gain"
    assert body["dietary_preference"] == "non_vegetarian"


def test_generate_plan_without_profile_uses_defaults(client, user):
    headers, _ = user
    r = client.post("/api/diet/generate-plan", json={}, headers=headers)
    assert r.status_code == 200


def test_generate_plan_requires_auth_401(client):
    assert client.post("/api/diet/generate-plan", json={}).status_code == 401


# ---------------------------------------------------------------------------
# Save / list / get / delete
# ---------------------------------------------------------------------------
def _generate_and_save(client, headers, title=None):
    preview = client.post("/api/diet/generate-plan", json={}, headers=headers).json()
    payload = {"plan": preview}
    if title:
        payload["title"] = title
    return client.post("/api/plans", json=payload, headers=headers)


def test_save_plan_201(client, user):
    headers, _ = user
    r = _generate_and_save(client, headers, title="Monday plan")
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Monday plan"
    assert body["nutrition_summary"]["calories_kcal"] > 0


def test_list_plans_newest_first(client, user):
    headers, _ = user
    _generate_and_save(client, headers, title="Plan 1")
    _generate_and_save(client, headers, title="Plan 2")
    rows = client.get("/api/plans", headers=headers).json()
    assert len(rows) == 2
    assert rows[0]["created_at"] >= rows[1]["created_at"]


def test_get_plan_by_id(client, user):
    headers, _ = user
    plan = _generate_and_save(client, headers).json()
    r = client.get(f"/api/plans/{plan['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == plan["id"]


def test_delete_plan(client, user):
    headers, _ = user
    plan = _generate_and_save(client, headers).json()
    assert client.delete(f"/api/plans/{plan['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/plans/{plan['id']}", headers=headers).status_code == 404


# ---------------------------------------------------------------------------
# USER ISOLATION — the security heart of the suite
# ---------------------------------------------------------------------------
def test_user_cannot_read_other_users_plan(client, user):
    headers, _ = user
    plan = _generate_and_save(client, headers).json()

    other = _second_user(client)
    # 404 (not 403) — never confirm another user's data exists.
    assert client.get(f"/api/plans/{plan['id']}", headers=other).status_code == 404


def test_user_cannot_delete_other_users_plan(client, user):
    headers, _ = user
    plan = _generate_and_save(client, headers).json()
    other = _second_user(client)
    assert client.delete(f"/api/plans/{plan['id']}", headers=other).status_code == 404
    # The owner's plan is untouched.
    assert client.get(f"/api/plans/{plan['id']}", headers=headers).status_code == 200


def test_plan_lists_never_leak_across_users(client, user):
    headers, _ = user
    _generate_and_save(client, headers)
    other = _second_user(client)
    assert client.get("/api/plans", headers=other).json() == []
