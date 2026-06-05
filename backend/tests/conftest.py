import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.main import app
from app.database import Base, getDB
from app.core.config import settingsInstance

TEST_DB_URL = settingsInstance.databaseUrl

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)

    def override_get_db():
        try:
            yield session
        finally:
            pass
    app.dependency_overrides[getDB] = override_get_db

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture(autouse=True)
def mock_smtp(mocker):
    return mocker.patch("app.core.emailUtils.sendVerificationEmail", return_value=None)

@pytest_asyncio.fixture
async def test_user(client, db_session):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "role": "USER"
    }
    resp = await client.post("/auth/register", json=user_data)
    assert resp.status_code == 201

    from app.models.userModel import User
    user = db_session.query(User).filter(User.email == user_data["email"]).first()
    assert user is not None
    user.isVerified = True
    db_session.commit()

    login_resp = await client.post("/auth/login", data={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"user": user_data, "token": token, "id": user.id}

@pytest_asyncio.fixture
async def test_hackathon(client, test_user):
    token = test_user["token"]
    from datetime import datetime, timedelta, timezone
    start = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    reg_start = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    payload = {
        "title": "Test Hackathon",
        "description": "Test Description",
        "location": "Online",
        "startDate": start,
        "endDate": end,
        "registrationStart": reg_start,
        "maxParticipants": 100,
        "imageUrl": "https://example.com/image.png"
    }
    resp = await client.post("/hackathons", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    return resp.json()
