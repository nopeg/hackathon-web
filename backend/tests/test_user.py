import asyncio
import pytest
from datetime import datetime, timedelta, timezone

@pytest.mark.asyncio
async def test_get_my_profile(client, test_user):
    token = test_user["token"]
    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == test_user["id"]
    assert data["username"] == test_user["user"]["username"]
    assert data["email"] == test_user["user"]["email"]
    assert "createdHackathons" in data
    assert "participations" in data
    assert isinstance(data["createdHackathons"], list)
    assert isinstance(data["participations"], list)

@pytest.mark.asyncio
async def test_get_my_profile_unauthenticated(client):
    resp = await client.get("/users/me")
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_get_user_hackathons(client, test_user, test_hackathon):
    token = test_user["token"]
    user_id = test_user["id"]
    resp = await client.get(f"/users/{user_id}/hackathons", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "created" in data
    assert "participated" in data
    assert isinstance(data["created"], list)
    assert isinstance(data["participated"], list)
    assert len(data["created"]) >= 1
    assert data["created"][0]["id"] == test_hackathon["id"]

@pytest.mark.asyncio
async def test_get_user_hackathons_not_found(client, test_user):
    token = test_user["token"]
    resp = await client.get("/users/99999/hackathons", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_get_user_hackathons_other_user(client, db_session, test_user, test_hackathon):
    token = test_user["token"]
    user2_data = {"username": "otherprofile", "email": "otherprofile@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user2_data)
    await asyncio.sleep(0.1)
    from app.models.userModel import User
    user2 = db_session.query(User).filter(User.username == "otherprofile").first()
    assert user2 is not None
    user2.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "otherprofile", "password": "pass1234"})
    other_token = login_resp.json()["access_token"]
    resp = await client.get(f"/users/{user2.id}/hackathons", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == []
    assert data["participated"] == []

@pytest.mark.asyncio
async def test_my_profile_contains_created_hackathon(client, test_user, test_hackathon):
    token = test_user["token"]
    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["createdHackathons"]) >= 1
    assert data["createdHackathons"][0]["id"] == test_hackathon["id"]
    assert data["createdHackathons"][0]["title"] == test_hackathon["title"]
    assert "status" in data["createdHackathons"][0]

@pytest.mark.asyncio
async def test_my_profile_contains_participation(client, db_session, test_user, test_hackathon):
    from app.models.hackathonModel import Hackathon
    token = test_user["token"]
    hackathon_id = test_hackathon["id"]
    
    hackathon = db_session.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    hackathon.registrationStart = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()
    
    user2_data = {"username": "participantprofile", "email": "participantprofile@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user2_data)
    await asyncio.sleep(0.1)
    from app.models.userModel import User
    user2 = db_session.query(User).filter(User.username == "participantprofile").first()
    assert user2 is not None
    user2.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "participantprofile", "password": "pass1234"})
    participant_token = login_resp.json()["access_token"]
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {participant_token}"})
    
    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {participant_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["participations"]) >= 1
    assert data["participations"][0]["hackathonId"] == hackathon_id
    assert data["participations"][0]["hackathonTitle"] == test_hackathon["title"]