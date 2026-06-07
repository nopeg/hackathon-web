import asyncio
import pytest
from app.models.userModel import User, UserRole
from app.models.hackathonModel import Hackathon

@pytest.mark.asyncio
async def test_admin_get_users(client, db_session):
    from app.core.security import createAccessToken
    
    admin_data = {"username": "admin", "email": "admin@example.com", "password": "pass1234", "role": "ADMIN"}
    resp = await client.post("/auth/register", json=admin_data)
    assert resp.status_code == 201
    await asyncio.sleep(0.1)
    
    admin = db_session.query(User).filter(User.username == "admin").first()
    assert admin is not None
    admin.isVerified = True
    admin.role = UserRole.ADMIN
    db_session.commit()
    
    admin_token = createAccessToken(data={"sub": "admin"})
    resp = await client.get("/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_admin_get_users_forbidden(client, test_user):
    token = test_user["token"]
    resp = await client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_ban_user_as_moderator(client, db_session):
    from app.core.security import createAccessToken
    
    moderator_data = {"username": "moderator", "email": "moderator@example.com", "password": "pass1234", "role": "MODERATOR"}
    await client.post("/auth/register", json=moderator_data)
    target_data = {"username": "target", "email": "target@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=target_data)
    await asyncio.sleep(0.1)
    
    moderator = db_session.query(User).filter(User.username == "moderator").first()
    assert moderator is not None
    moderator.isVerified = True
    moderator.role = UserRole.MODERATOR
    db_session.commit()
    
    target = db_session.query(User).filter(User.username == "target").first()
    assert target is not None
    target.isVerified = True
    db_session.commit()
    
    moderator_token = createAccessToken(data={"sub": "moderator"})
    resp = await client.post(f"/admin/users/{target.id}/ban", headers={"Authorization": f"Bearer {moderator_token}"})
    assert resp.status_code == 200
    assert "banned" in resp.text
    
    db_session.refresh(target)
    assert target.isBanned is True

@pytest.mark.asyncio
async def test_unban_user_as_moderator(client, db_session):
    from app.core.security import createAccessToken
    
    moderator_data = {"username": "moderator2", "email": "moderator2@example.com", "password": "pass1234", "role": "MODERATOR"}
    await client.post("/auth/register", json=moderator_data)
    target_data = {"username": "target2", "email": "target2@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=target_data)
    await asyncio.sleep(0.1)
    
    moderator = db_session.query(User).filter(User.username == "moderator2").first()
    assert moderator is not None
    moderator.isVerified = True
    moderator.role = UserRole.MODERATOR
    db_session.commit()
    
    target = db_session.query(User).filter(User.username == "target2").first()
    assert target is not None
    target.isVerified = True
    target.isBanned = True
    db_session.commit()
    
    moderator_token = createAccessToken(data={"sub": "moderator2"})
    resp = await client.post(f"/admin/users/{target.id}/unban", headers={"Authorization": f"Bearer {moderator_token}"})
    assert resp.status_code == 200
    assert "unbanned" in resp.text
    
    db_session.refresh(target)
    assert target.isBanned is False

@pytest.mark.asyncio
async def test_ban_admin_forbidden(client, db_session):
    from app.core.security import createAccessToken
    
    admin_data = {"username": "admin2", "email": "admin2@example.com", "password": "pass1234", "role": "ADMIN"}
    await client.post("/auth/register", json=admin_data)
    moderator_data = {"username": "moderator3", "email": "moderator3@example.com", "password": "pass1234", "role": "MODERATOR"}
    await client.post("/auth/register", json=moderator_data)
    await asyncio.sleep(0.1)
    
    admin = db_session.query(User).filter(User.username == "admin2").first()
    assert admin is not None
    admin.isVerified = True
    admin.role = UserRole.ADMIN
    db_session.commit()
    
    moderator = db_session.query(User).filter(User.username == "moderator3").first()
    assert moderator is not None
    moderator.isVerified = True
    moderator.role = UserRole.MODERATOR
    db_session.commit()
    
    moderator_token = createAccessToken(data={"sub": "moderator3"})
    resp = await client.post(f"/admin/users/{admin.id}/ban", headers={"Authorization": f"Bearer {moderator_token}"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_delete_any_hackathon_as_moderator(client, db_session, test_hackathon):
    from app.core.security import createAccessToken
    
    moderator_data = {"username": "moderator4", "email": "moderator4@example.com", "password": "pass1234", "role": "MODERATOR"}
    await client.post("/auth/register", json=moderator_data)
    await asyncio.sleep(0.1)
    
    moderator = db_session.query(User).filter(User.username == "moderator4").first()
    assert moderator is not None
    moderator.isVerified = True
    moderator.role = UserRole.MODERATOR
    db_session.commit()
    
    hackathon_id = test_hackathon["id"]
    moderator_token = createAccessToken(data={"sub": "moderator4"})
    resp = await client.delete(f"/admin/hackathons/{hackathon_id}", headers={"Authorization": f"Bearer {moderator_token}"})
    assert resp.status_code == 200
    assert "deleted" in resp.text
    
    hackathon = db_session.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    assert hackathon is None

@pytest.mark.asyncio
async def test_delete_any_hackathon_as_user_forbidden(client, test_user, test_hackathon):
    token = test_user["token"]
    hackathon_id = test_hackathon["id"]
    resp = await client.delete(f"/admin/hackathons/{hackathon_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403