"""
test_files.py — object-storage uploads: validation, download, isolation.
"""

from tests.conftest import auth_headers, login, make_png, register, unique_email


def _second_user(client):
    email = unique_email("other")
    register(client, email=email)
    token = login(client, email).json()["access_token"]
    return auth_headers(token)


def _upload(client, headers, name="meal.png", content=None):
    body = make_png() if content is None else content
    return client.post(
        "/api/files/upload",
        files={"file": (name, body, "image/png")},
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Upload validation
# ---------------------------------------------------------------------------
def test_upload_valid_png_201(client, user):
    headers, _ = user
    r = _upload(client, headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["filename"] == "meal.png"
    assert body["storage_path"].startswith("meals/")
    assert body["size_bytes"] > 0


def test_upload_rejects_disallowed_extension_415(client, user):
    headers, _ = user
    r = client.post(
        "/api/files/upload",
        files={"file": ("program.exe", b"MZ\x90\x00", "application/octet-stream")},
        headers=headers,
    )
    assert r.status_code == 415


def test_upload_rejects_disguised_content_415(client, user):
    """virus.exe renamed to photo.jpg must fail magic-byte sniffing."""
    headers, _ = user
    r = _upload(client, headers, name="photo.jpg", content=b"MZ\x90\x00not-really-jpeg")
    assert r.status_code == 415


def test_upload_rejects_empty_file_415(client, user):
    headers, _ = user
    r = _upload(client, headers, name="empty.png", content=b"")
    assert r.status_code == 415


def test_upload_requires_auth_401(client):
    r = client.post(
        "/api/files/upload",
        files={"file": ("meal.png", make_png(), "image/png")},
    )
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Download / list / delete
# ---------------------------------------------------------------------------
def test_download_roundtrip_bytes_match(client, user):
    headers, _ = user
    payload = b"custom png body bytes 123"
    meta = _upload(client, headers, content=make_png(payload)).json()
    r = client.get(f"/api/files/{meta['id']}/download", headers=headers)
    assert r.status_code == 200
    assert r.content == make_png(payload)


def test_download_requires_auth_401(client, user):
    headers, _ = user
    meta = _upload(client, headers).json()
    assert client.get(f"/api/files/{meta['id']}/download").status_code == 401


def test_delete_file_removes_metadata(client, user):
    headers, _ = user
    meta = _upload(client, headers).json()
    assert client.delete(f"/api/files/{meta['id']}", headers=headers).status_code == 200
    rows = client.get("/api/files", headers=headers).json()
    assert rows == []


def test_list_files_only_mine(client, user):
    headers, _ = user
    _upload(client, headers)
    other = _second_user(client)
    assert client.get("/api/files", headers=other).json() == []


# ---------------------------------------------------------------------------
# USER ISOLATION on stored objects
# ---------------------------------------------------------------------------
def test_user_cannot_download_other_users_file(client, user):
    headers, _ = user
    meta = _upload(client, headers).json()
    other = _second_user(client)
    assert client.get(f"/api/files/{meta['id']}/download", headers=other).status_code == 404


def test_user_cannot_delete_other_users_file(client, user):
    headers, _ = user
    meta = _upload(client, headers).json()
    other = _second_user(client)
    assert client.delete(f"/api/files/{meta['id']}", headers=other).status_code == 404
    # Owner can still download it — the file was untouched.
    assert client.get(f"/api/files/{meta['id']}/download", headers=headers).status_code == 200
