import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from app.models.userModel import User
from app.models.hackathonModel import Hackathon, Participant

def set_registration_past(db_session, hackathon_id):
    hackathon = db_session.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    hackathon.registrationStart = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

@pytest.mark.asyncio
async def test_create_team_success(client, db_session, test_hackathon):
    hackathon_id = test_hackathon["id"]
    set_registration_past(db_session, hackathon_id)
    
    user_data = {"username": "teamcreator", "email": "teamcreator@example.com", "password": "pass1234", "role": "USER"}
    reg_resp = await client.post("/auth/register", json=user_data)
    assert reg_resp.status_code == 201
    await asyncio.sleep(0.1)
    
    user = db_session.query(User).filter(User.username == "teamcreator").first()
    assert user is not None
    user.isVerified = True
    db_session.commit()
    
    login_resp = await client.post("/auth/login", data={"username": "teamcreator", "password": "pass1234"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    
    join_resp = await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {token}"})
    assert join_resp.status_code == 201, f"Failed to register: {join_resp.text}"
    
    resp = await client.post("/teams", json={"name": "Test Team", "hackathonId": hackathon_id}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Team"
    assert data["creatorId"] == user.id
    assert "inviteCode" in data

@pytest.mark.asyncio
async def test_create_team_without_registration(client, db_session, test_hackathon):
    hackathon_id = test_hackathon["id"]
    set_registration_past(db_session, hackathon_id)
    
    user_data = {"username": "noreg", "email": "noreg@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user_data)
    await asyncio.sleep(0.1)
    user = db_session.query(User).filter(User.username == "noreg").first()
    assert user is not None
    user.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "noreg", "password": "pass1234"})
    token = login_resp.json()["access_token"]
    resp = await client.post("/teams", json={"name": "No Reg Team", "hackathonId": hackathon_id}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert "register" in resp.text

@pytest.mark.asyncio
async def test_create_team_already_in_team(client, db_session, test_hackathon):
    hackathon_id = test_hackathon["id"]
    set_registration_past(db_session, hackathon_id)
    
    user_data = {"username": "alreadyinteam", "email": "already@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user_data)
    await asyncio.sleep(0.1)
    user = db_session.query(User).filter(User.username == "alreadyinteam").first()
    assert user is not None
    user.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "alreadyinteam", "password": "pass1234"})
    token = login_resp.json()["access_token"]
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {token}"})
    await client.post("/teams", json={"name": "Team One", "hackathonId": hackathon_id}, headers={"Authorization": f"Bearer {token}"})
    resp = await client.post("/teams", json={"name": "Team Two", "hackathonId": hackathon_id}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert "already in a team" in resp.text

@pytest.mark.asyncio
async def test_join_team_by_invite_code(client, db_session, test_hackathon):
    hackathon_id = test_hackathon["id"]
    set_registration_past(db_session, hackathon_id)
    
    creator_data = {"username": "teamlead", "email": "lead@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=creator_data)
    await asyncio.sleep(0.1)
    creator = db_session.query(User).filter(User.username == "teamlead").first()
    assert creator is not None
    creator.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "teamlead", "password": "pass1234"})
    creator_token = login_resp.json()["access_token"]
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {creator_token}"})
    team_resp = await client.post("/teams", json={"name": "Joinable Team", "hackathonId": hackathon_id}, headers={"Authorization": f"Bearer {creator_token}"})
    invite_code = team_resp.json()["inviteCode"]
    joiner_data = {"username": "joiner", "email": "joinerteam@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=joiner_data)
    await asyncio.sleep(0.1)
    joiner = db_session.query(User).filter(User.username == "joiner").first()
    assert joiner is not None
    joiner.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "joiner", "password": "pass1234"})
    joiner_token = login_resp.json()["access_token"]
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {joiner_token}"})
    resp = await client.post("/teams/join", json={"inviteCode": invite_code}, headers={"Authorization": f"Bearer {joiner_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Joinable Team"

@pytest.mark.asyncio
async def test_join_team_invalid_invite_code(client, test_user):
    token = test_user["token"]
    resp = await client.post("/teams/join", json={"inviteCode": "INVALID"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_join_team_full(client, db_session, test_hackathon):
    hackathon_id = test_hackathon["id"]
    set_registration_past(db_session, hackathon_id)
    
    creator_data = {"username": "fullteamlead", "email": "fullteamlead@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=creator_data)
    await asyncio.sleep(0.1)
    creator = db_session.query(User).filter(User.username == "fullteamlead").first()
    assert creator is not None
    creator.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "fullteamlead", "password": "pass1234"})
    creator_token = login_resp.json()["access_token"]
    
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {creator_token}"})
    
    team_resp = await client.post("/teams", json={"name": "Full Team", "hackathonId": hackathon_id}, headers={"Authorization": f"Bearer {creator_token}"})
    assert team_resp.status_code == 201, f"Failed to create team: {team_resp.text}"
    invite_code = team_resp.json()["inviteCode"]
    
    hackathon = db_session.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    hackathon.maxTeamSize = 1
    db_session.commit()
    
    joiner_data = {"username": "cantjoin", "email": "cantjoin@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=joiner_data)
    await asyncio.sleep(0.1)
    joiner = db_session.query(User).filter(User.username == "cantjoin").first()
    assert joiner is not None
    joiner.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "cantjoin", "password": "pass1234"})
    joiner_token = login_resp.json()["access_token"]
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {joiner_token}"})
    
    resp = await client.post("/teams/join", json={"inviteCode": invite_code}, headers={"Authorization": f"Bearer {joiner_token}"})
    assert resp.status_code == 400
    assert "full" in resp.text

@pytest.mark.asyncio
async def test_get_team_details(client, db_session, test_hackathon):
    hackathon_id = test_hackathon["id"]
    set_registration_past(db_session, hackathon_id)
    
    creator_data = {"username": "teamdetail", "email": "teamdetail@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=creator_data)
    await asyncio.sleep(0.1)
    creator = db_session.query(User).filter(User.username == "teamdetail").first()
    assert creator is not None
    creator.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "teamdetail", "password": "pass1234"})
    creator_token = login_resp.json()["access_token"]
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {creator_token}"})
    team_resp = await client.post("/teams", json={"name": "Detail Team", "hackathonId": hackathon_id}, headers={"Authorization": f"Bearer {creator_token}"})
    team_id = team_resp.json()["id"]
    resp = await client.get(f"/teams/{team_id}", headers={"Authorization": f"Bearer {creator_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == team_id
    assert data["name"] == "Detail Team"
    assert "members" in data

@pytest.mark.asyncio
async def test_leave_team_as_member(client, db_session, test_hackathon):
    hackathon_id = test_hackathon["id"]
    set_registration_past(db_session, hackathon_id)
    
    creator_data = {"username": "leavelead", "email": "leavelead@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=creator_data)
    await asyncio.sleep(0.1)
    creator = db_session.query(User).filter(User.username == "leavelead").first()
    assert creator is not None
    creator.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "leavelead", "password": "pass1234"})
    creator_token = login_resp.json()["access_token"]
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {creator_token}"})
    team_resp = await client.post("/teams", json={"name": "Leave Team", "hackathonId": hackathon_id}, headers={"Authorization": f"Bearer {creator_token}"})
    team_id = team_resp.json()["id"]
    member_data = {"username": "memberleave", "email": "memberleave@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=member_data)
    await asyncio.sleep(0.1)
    member = db_session.query(User).filter(User.username == "memberleave").first()
    assert member is not None
    member.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "memberleave", "password": "pass1234"})
    member_token = login_resp.json()["access_token"]
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {member_token}"})
    await client.post("/teams/join", json={"inviteCode": team_resp.json()["inviteCode"]}, headers={"Authorization": f"Bearer {member_token}"})
    resp = await client.post(f"/teams/{team_id}/leave", headers={"Authorization": f"Bearer {member_token}"})
    assert resp.status_code == 204

@pytest.mark.asyncio
async def test_leave_team_as_creator_deletes_team(client, db_session, test_hackathon):
    hackathon_id = test_hackathon["id"]
    set_registration_past(db_session, hackathon_id)
    
    creator_data = {"username": "creatordelete", "email": "creatordelete@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=creator_data)
    await asyncio.sleep(0.1)
    creator = db_session.query(User).filter(User.username == "creatordelete").first()
    assert creator is not None
    creator.isVerified = True
    db_session.commit()
    login_resp = await client.post("/auth/login", data={"username": "creatordelete", "password": "pass1234"})
    creator_token = login_resp.json()["access_token"]
    await client.post(f"/hackathons/{hackathon_id}/register", headers={"Authorization": f"Bearer {creator_token}"})
    team_resp = await client.post("/teams", json={"name": "Delete Team", "hackathonId": hackathon_id}, headers={"Authorization": f"Bearer {creator_token}"})
    team_id = team_resp.json()["id"]
    resp = await client.post(f"/teams/{team_id}/leave", headers={"Authorization": f"Bearer {creator_token}"})
    assert resp.status_code == 204
    get_resp = await client.get(f"/teams/{team_id}", headers={"Authorization": f"Bearer {creator_token}"})
    assert get_resp.status_code == 404