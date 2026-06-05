import asyncio
import pytest
from app.models.userModel import User
from app.models.verificationToken import VerificationToken

@pytest.mark.asyncio
async def test_register_success(client, db_session, mock_smtp):
    resp = await client.post("/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "pass1234",
        "role": "USER"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert data["isVerified"] == False
    await asyncio.sleep(0.1)
    token = db_session.query(VerificationToken).filter(VerificationToken.userEmail == "new@example.com").first()
    assert token is not None

@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    resp1 = await client.post("/auth/register", json={
        "username": "duplicate",
        "email": "dup1@example.com",
        "password": "pass1234",
        "role": "USER"
    })
    assert resp1.status_code == 201
    resp2 = await client.post("/auth/register", json={
        "username": "duplicate",
        "email": "dup2@example.com",
        "password": "pass1234",
        "role": "USER"
    })
    assert resp2.status_code == 400
    assert "already registered" in resp2.text

@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    resp1 = await client.post("/auth/register", json={
        "username": "user1",
        "email": "same@example.com",
        "password": "pass1234",
        "role": "USER"
    })
    assert resp1.status_code == 201
    resp2 = await client.post("/auth/register", json={
        "username": "user2",
        "email": "same@example.com",
        "password": "pass1234",
        "role": "USER"
    })
    assert resp2.status_code == 400
    assert "Email already registered" in resp2.text

@pytest.mark.asyncio
async def test_login_unverified(client):
    await client.post("/auth/register", json={
        "username": "unver",
        "email": "unver@example.com",
        "password": "pass1234",
        "role": "USER"
    })
    resp = await client.post("/auth/login", data={"username": "unver", "password": "pass1234"})
    assert resp.status_code == 403
    assert "Email not verified" in resp.text

@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    resp = await client.post("/auth/login", data={
        "username": test_user["user"]["username"],
        "password": "wrongpassword"
    })
    assert resp.status_code == 401
    assert "Incorrect" in resp.text

@pytest.mark.asyncio
async def test_verify_email_success(client, db_session):
    user_data = {"username": "verify", "email": "verify@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user_data)
    await asyncio.sleep(0.1)
    token_record = db_session.query(VerificationToken).filter(VerificationToken.userEmail == "verify@example.com").first()
    assert token_record is not None
    token = token_record.token
    resp = await client.get(f"/auth/verifyEmail?token={token}")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["username"] == "verify"
    user = db_session.query(User).filter(User.email == "verify@example.com").first()
    assert user.isVerified is True
    assert db_session.query(VerificationToken).filter(VerificationToken.token == token).first() is None

@pytest.mark.asyncio
async def test_verify_email_invalid_token(client):
    resp = await client.get("/auth/verifyEmail?token=invalid_token")
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_verify_email_expired_token(client, db_session):
    from datetime import datetime, timedelta
    user_data = {"username": "expired", "email": "expired@example.com", "password": "pass1234", "role": "USER"}
    await client.post("/auth/register", json=user_data)
    await asyncio.sleep(0.1)
    token_record = db_session.query(VerificationToken).filter(VerificationToken.userEmail == "expired@example.com").first()
    assert token_record is not None
    token_record.expiresAt = datetime.utcnow() - timedelta(hours=1)
    db_session.commit()
    resp = await client.get(f"/auth/verifyEmail?token={token_record.token}")
    assert resp.status_code == 400
    assert "expired" in resp.text

@pytest.mark.asyncio
async def test_get_current_user(client, test_user):
    token = test_user["token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == test_user["user"]["username"]
    assert data["email"] == test_user["user"]["email"]

@pytest.mark.asyncio
async def test_get_current_user_unauthenticated(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401