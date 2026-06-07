import asyncio
import pytest
from datetime import datetime, timedelta, timezone

@pytest.mark.asyncio
async def test_create_hackathon_success(client, test_user):
    token = test_user["token"]
    start = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    reg_start = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    payload = {
        "title": "Test Hackathon",
        "description": "Description",
        "location": "Online",
        "startDate": start,
        "endDate": end,
        "registrationStart": reg_start,
        "maxParticipants": 100,
        "imageUrl": "http://example.com/img.png"
    }
    resp = await client.post("/hackathons", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == payload["title"]
    assert data["organizerId"] == test_user["id"]
    assert "id" in data

@pytest.mark.asyncio
async def test_create_hackathon_invalid_dates(client, test_user):
    token = test_user["token"]
    start = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    reg_start = (datetime.now(timezone.utc) + timedelta(days=12)).isoformat()
    payload = {
        "title": "Invalid",
        "description": "Desc",
        "location": "Online",
        "startDate": start,
        "endDate": end,
        "registrationStart": reg_start,
        "maxParticipants": 100
    }
    resp = await client.post("/hackathons", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_create_hackathon_min_team_size_greater_than_max(client, test_user):
    token = test_user["token"]
    start = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    reg_start = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    payload = {
        "title": "Test",
        "description": "Desc",
        "location": "Online",
        "startDate": start,
        "endDate": end,
        "registrationStart": reg_start,
        "maxParticipants": 100,
        "minTeamSize": 5,
        "maxTeamSize": 3
    }
    resp = await client.post("/hackathons", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert "minTeamSize cannot be greater than maxTeamSize" in resp.text

@pytest.mark.asyncio
async def test_get_hackathons(client, test_hackathon):
    resp = await client.get("/hackathons")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1

@pytest.mark.asyncio
async def test_get_hackathon_by_id(client, test_hackathon):
    hackathon_id = test_hackathon["id"]
    resp = await client.get(f"/hackathons/{hackathon_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == hackathon_id
    assert data["title"] == test_hackathon["title"]

@pytest.mark.asyncio
async def test_get_hackathon_not_found(client):
    resp = await client.get("/hackathons/99999")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_update_hackathon_as_organizer(client, test_user, test_hackathon):
    token = test_user["token"]
    hackathon_id = test_hackathon["id"]
    update_data = {"title": "Updated Title", "description": "Updated Description"}
    resp = await client.put(
        f"/hackathons/{hackathon_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Description"

@pytest.mark.asyncio
async def test_update_hackathon_as_non_organizer(client, db_session, test_hackathon):
    user2_data = {"username": "otheruser", "email": "other@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user2_data)
    await asyncio.sleep(0.1)
    from app.models.userModel import User
    user2 = db_session.query(User).filter(User.username == "otheruser").first()
    assert user2 is not None
    user2.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "otheruser", "password": "pass1234"})
    other_token = login_resp.json()["access_token"]
    hackathon_id = test_hackathon["id"]
    resp = await client.put(
        f"/hackathons/{hackathon_id}",
        json={"title": "Hacked"},
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_delete_hackathon_as_organizer(client, test_user, test_hackathon):
    token = test_user["token"]
    hackathon_id = test_hackathon["id"]
    resp = await client.delete(f"/hackathons/{hackathon_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204
    get_resp = await client.get(f"/hackathons/{hackathon_id}")
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_delete_hackathon_as_non_organizer(client, db_session, test_hackathon):
    user2_data = {"username": "otheruser2", "email": "other2@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user2_data)
    await asyncio.sleep(0.1)
    from app.models.userModel import User
    user2 = db_session.query(User).filter(User.username == "otheruser2").first()
    assert user2 is not None
    user2.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "otheruser2", "password": "pass1234"})
    other_token = login_resp.json()["access_token"]
    hackathon_id = test_hackathon["id"]
    resp = await client.delete(f"/hackathons/{hackathon_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_join_hackathon_success(client, db_session, test_hackathon):
    from app.models.hackathonModel import Hackathon
    hackathon_id = test_hackathon["id"]
    
    hackathon = db_session.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    hackathon.registrationStart = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()
    
    user2_data = {"username": "participant", "email": "participant@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user2_data)
    await asyncio.sleep(0.1)
    from app.models.userModel import User
    user2 = db_session.query(User).filter(User.username == "participant").first()
    assert user2 is not None
    user2.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "participant", "password": "pass1234"})
    participant_token = login_resp.json()["access_token"]
    resp = await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {participant_token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["userId"] == user2.id
    assert data["hackathonId"] == hackathon_id

@pytest.mark.asyncio
async def test_join_hackathon_already_registered(client, db_session, test_hackathon):
    from app.models.hackathonModel import Hackathon
    hackathon_id = test_hackathon["id"]
    
    hackathon = db_session.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    hackathon.registrationStart = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()
    
    user2_data = {"username": "alreadyparticipant", "email": "already@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user2_data)
    await asyncio.sleep(0.1)
    from app.models.userModel import User
    user2 = db_session.query(User).filter(User.username == "alreadyparticipant").first()
    assert user2 is not None
    user2.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "alreadyparticipant", "password": "pass1234"})
    participant_token = login_resp.json()["access_token"]
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {participant_token}"})
    resp = await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {participant_token}"})
    assert resp.status_code == 400
    assert "already registered" in resp.text

@pytest.mark.asyncio
async def test_join_hackathon_full(client, db_session, test_hackathon):
    from app.models.hackathonModel import Hackathon
    hackathon_id = test_hackathon["id"]
    
    hackathon = db_session.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    hackathon.registrationStart = datetime.now(timezone.utc) - timedelta(days=1)
    hackathon.maxParticipants = 1
    hackathon.currentParticipants = 1
    db_session.commit()
    
    user2_data = {"username": "fulluser", "email": "full@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user2_data)
    await asyncio.sleep(0.1)
    from app.models.userModel import User
    user2 = db_session.query(User).filter(User.username == "fulluser").first()
    assert user2 is not None
    user2.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "fulluser", "password": "pass1234"})
    token = login_resp.json()["access_token"]
    resp = await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert "full" in resp.text

@pytest.mark.asyncio
async def test_join_hackathon_registration_not_started(client, db_session, test_hackathon):
    from app.models.hackathonModel import Hackathon
    hackathon_id = test_hackathon["id"]
    
    hackathon = db_session.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    hackathon.registrationStart = datetime.now(timezone.utc) + timedelta(days=1)
    db_session.commit()
    
    user2_data = {"username": "early", "email": "early@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user2_data)
    await asyncio.sleep(0.1)
    from app.models.userModel import User
    user2 = db_session.query(User).filter(User.username == "early").first()
    assert user2 is not None
    user2.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "early", "password": "pass1234"})
    token = login_resp.json()["access_token"]
    resp = await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert "not started" in resp.text

@pytest.mark.asyncio
async def test_join_hackathon_organizer_cannot_join(client, test_user, test_hackathon):
    token = test_user["token"]
    hackathon_id = test_hackathon["id"]
    resp = await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert "cannot participate" in resp.text