"""
test_health.py — health probes + dashboard aggregation.
"""

from tests.conftest import PROFILE_PAYLOAD


def test_health_liveness(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["environment"] == "test"


def test_health_db(client):
    r = client.get("/api/health/db")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_storage(client):
    r = client.get("/api/health/storage")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_requires_auth_401(client):
    assert client.get("/api/dashboard").status_code == 401


def test_dashboard_empty_state(client, user):
    headers, user_dict = user
    r = client.get("/api/dashboard", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["email"] == user_dict["email"]
    assert body["profile"] is None
    assert body["latest_plan"] is None
    assert body["total_plans"] == 0
    assert body["total_files"] == 0


def test_dashboard_after_activity(client, user_with_profile):
    headers, _, _ = user_with_profile
    client.post("/api/diet/generate-plan", json={}, headers=headers)
    preview = client.post("/api/diet/generate-plan", json={}, headers=headers).json()
    client.post("/api/plans", json={"plan": preview}, headers=headers)
    client.post(
        "/api/files/upload",
        files={"file": ("meal.png", b"\x89PNG\r\n\x1a\nimage", "image/png")},
        headers=headers,
    )

    body = client.get("/api/dashboard", headers=headers).json()
    assert body["profile"]["goal"] == "weight_loss"
    assert body["total_plans"] == 1
    assert body["total_files"] == 1
    assert body["latest_plan"]["title"]
    assert len(body["recent_plans"]) == 1
    assert body["profile"]["bmi_display"].startswith("BMI")
