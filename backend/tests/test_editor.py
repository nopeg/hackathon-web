import asyncio
import pytest
from datetime import datetime, timedelta, timezone

@pytest.mark.asyncio
async def test_upload_image_success(client, test_user):
    token = test_user["token"]
    files = {"file": ("test.jpg", b"fake image content", "image/jpeg")}
    resp = await client.post("/editor/upload-image", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert data["url"].startswith("/static/uploads/")

@pytest.mark.asyncio
async def test_upload_image_invalid_type(client, test_user):
    token = test_user["token"]
    files = {"file": ("test.txt", b"fake text", "text/plain")}
    resp = await client.post("/editor/upload-image", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert "Only image files are allowed" in resp.text

@pytest.mark.asyncio
async def test_upload_image_unauthenticated(client):
    files = {"file": ("test.jpg", b"fake image content", "image/jpeg")}
    resp = await client.post("/editor/upload-image", files=files)
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_create_hackathon_via_editor(client, test_user):
    token = test_user["token"]
    start = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    reg_start = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    payload = {
        "title": "Editor Hackathon",
        "description": "Created via editor",
        "location": "Online",
        "startDate": start,
        "endDate": end,
        "registrationStart": reg_start,
        "maxParticipants": 100,
        "imageUrl": "http://example.com/img.png"
    }
    resp = await client.post("/editor/hackathons", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == payload["title"]
    assert data["organizerId"] == test_user["id"]

@pytest.mark.asyncio
async def test_update_hackathon_via_editor(client, test_user, test_hackathon):
    token = test_user["token"]
    hackathon_id = test_hackathon["id"]
    update_data = {"title": "Updated via Editor", "description": "New description"}
    resp = await client.put(
        f"/editor/hackathons/{hackathon_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated via Editor"
    assert data["description"] == "New description"

@pytest.mark.asyncio
async def test_update_hackathon_via_editor_as_non_organizer(client, db_session, test_hackathon):
    user2_data = {"username": "editoruser", "email": "editor@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user2_data)
    await asyncio.sleep(0.1)
    from app.models.userModel import User
    user2 = db_session.query(User).filter(User.username == "editoruser").first()
    assert user2 is not None
    user2.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "editoruser", "password": "pass1234"})
    other_token = login_resp.json()["access_token"]
    hackathon_id = test_hackathon["id"]
    resp = await client.put(
        f"/editor/hackathons/{hackathon_id}",
        json={"title": "Hacked"},
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_delete_hackathon_via_editor(client, test_user, test_hackathon):
    token = test_user["token"]
    hackathon_id = test_hackathon["id"]
    resp = await client.delete(f"/editor/hackathons/{hackathon_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204
    get_resp = await client.get(f"/hackathons/{hackathon_id}")
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_delete_hackathon_via_editor_as_non_organizer(client, db_session, test_hackathon):
    user2_data = {"username": "editoruser2", "email": "editor2@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user2_data)
    await asyncio.sleep(0.1)
    from app.models.userModel import User
    user2 = db_session.query(User).filter(User.username == "editoruser2").first()
    assert user2 is not None
    user2.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "editoruser2", "password": "pass1234"})
    other_token = login_resp.json()["access_token"]
    hackathon_id = test_hackathon["id"]
    resp = await client.delete(f"/editor/hackathons/{hackathon_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 403