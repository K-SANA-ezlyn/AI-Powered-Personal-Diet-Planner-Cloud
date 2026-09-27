"""
smoke_test.py — END-TO-END SMOKE TEST against a LIVE server.

Start the API, then run:
    python scripts/smoke_test.py            (defaults to http://localhost:8000)
    python scripts/smoke_test.py http://localhost:8765

It walks the complete user story over real HTTP:
  health -> register -> login -> profile -> generate plan -> save plan ->
  list/get/delete -> upload file -> download -> isolation checks ->
  dashboard -> logout.

Exit code 0 = all steps passed.
"""

import sys
import uuid

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
client = httpx.Client(base_url=BASE, timeout=30)

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -> {detail}" if detail and not ok else ""))


run = uuid.uuid4().hex[:6]
USER_A = {"email": f"smoke.a.{run}@demo.com", "password": "Demo@12345", "name": "Smoke A"}
USER_B = {"email": f"smoke.b.{run}@demo.com", "password": "Demo@12345", "name": "Smoke B"}

PROFILE = {
    "age": 29, "height_cm": 170, "weight_kg": 69,
    "activity_level": "moderate", "dietary_preference": "vegetarian",
    "goal": "weight_loss", "allergies": "nuts", "meals_per_day": 3,
}


def main() -> None:
    # 0. liveness
    r = client.get("/api/health")
    check("health endpoint", r.status_code == 200, f"{r.status_code} {r.text[:120]}")

    # 1. register + login two users
    for u in (USER_A, USER_B):
        r = client.post("/api/auth/register", json=u)
        check(f"register {u['email']}", r.status_code == 201, f"{r.status_code} {r.text[:150]}")
    tok_a = client.post("/api/auth/login", json={"email": USER_A["email"], "password": USER_A["password"]}).json()["access_token"]
    tok_b = client.post("/api/auth/login", json={"email": USER_B["email"], "password": USER_B["password"]}).json()["access_token"]
    a = {"Authorization": f"Bearer {tok_a}"}
    b = {"Authorization": f"Bearer {tok_b}"}
    check("login issues JWTs", bool(tok_a) and bool(tok_b))

    # 2. profile
    r = client.put("/api/profile", json=PROFILE, headers=a)
    check("profile upsert", r.status_code == 200 and r.json()["goal"] == "weight_loss", f"{r.status_code}")
    r = client.get("/api/profile", headers=a)
    check("profile read-back", r.status_code == 200 and r.json()["allergies"] == "nuts")

    # 3. generate plan (AI or rule-based)
    r = client.post("/api/diet/generate-plan", json={}, headers=a)
    preview = r.json()
    check("generate plan (engine used: %s)" % preview.get("engine_used"),
          r.status_code == 200 and preview.get("breakfast"), f"{r.status_code} {r.text[:150]}")
    check("plan carries disclaimer", "not medical" in preview.get("disclaimer", ""))

    # 4. save + list + get
    r = client.post("/api/plans", json={"plan": preview, "title": "Smoke plan"}, headers=a)
    plan = r.json()
    check("save plan (201)", r.status_code == 201, f"{r.status_code} {r.text[:150]}")
    check("list plans has 1 row", len(client.get("/api/plans", headers=a).json()) == 1)
    check("get plan by id", client.get(f"/api/plans/{plan['id']}", headers=a).status_code == 200)

    # 5. USER ISOLATION — user B cannot touch A's plan
    check("user B cannot read A's plan (404)",
          client.get(f"/api/plans/{plan['id']}", headers=b).status_code == 404)
    check("user B cannot delete A's plan (404)",
          client.delete(f"/api/plans/{plan['id']}", headers=b).status_code == 404)

    # 6. file upload (real PNG magic bytes)
    png = b"\x89PNG\r\n\x1a\n" + b"smoke-test-image-body"
    r = client.post("/api/files/upload", files={"file": ("smoke_meal.png", png, "image/png")}, headers=a)
    meta = r.json()
    check("file upload (201)", r.status_code == 201 and meta.get("storage_path", "").startswith("meals/"),
          f"{r.status_code} {r.text[:150]}")

    # 7. download round-trip
    r = client.get(f"/api/files/{meta['id']}/download", headers=a)
    check("download round-trip (bytes match)", r.status_code == 200 and r.content == png, f"{r.status_code}")
    check("user B cannot download A's file (404)",
          client.get(f"/api/files/{meta['id']}/download", headers=b).status_code == 404)

    # 8. invalid upload rejected
    r = client.post("/api/files/upload", files={"file": ("virus.exe", b"MZ\x90\x00", "application/octet-stream")}, headers=a)
    check("upload .exe rejected (415)", r.status_code == 415, str(r.status_code))

    # 9. dashboard aggregate
    r = client.get("/api/dashboard", headers=a)
    body = r.json()
    check("dashboard aggregates", r.status_code == 200 and body.get("total_plans") == 1 and body.get("total_files") == 1,
          f"{r.status_code} {r.text[:200]}")

    # 10. delete plan + logout
    check("delete plan", client.delete(f"/api/plans/{plan['id']}", headers=a).status_code == 200)
    check("logout", client.post("/api/auth/logout", headers=a).status_code == 200)

    # 11. unauthenticated access blocked
    check("anonymous plans list blocked (401)", client.get("/api/plans").status_code == 401)

    print()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"{passed}/{len(results)} smoke checks passed")
    if passed != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
