import os

# Set dummy SECRET_KEY for tests before importing anything from piggy
os.environ["SECRET_KEY"] = "test-secret-key"

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from piggy import app
from piggy.core.database import Base, get_db
from piggy.models.database.user import User, UserRole
from piggy.core.auth import get_password_hash

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db():
    async with TestingSessionLocal() as session:
        yield session
        # Clean up after each test
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()

@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_mail():
    with patch("piggy.core.mail._send_email", return_value=None):
        yield

@pytest_asyncio.fixture
async def test_user(db):
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password"),
        name="Test User",
        is_active=True,
        email_verified=True,
        role=UserRole.USER
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_admin(db):
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("password"),
        name="Admin User",
        is_active=True,
        email_verified=True,
        role=UserRole.ADMIN
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin

@pytest_asyncio.fixture
async def user_token(client, test_user):
    response = await client.post(
        "/api/v1/users/login",
        data={"username": "test@example.com", "password": "password"},
    )
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def admin_token(client, test_admin):
    response = await client.post(
        "/api/v1/users/login",
        data={"username": "admin@example.com", "password": "password"},
    )
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def auth_client(client, user_token):
    client.headers.update({"Authorization": f"Bearer {user_token}"})
    return client

@pytest_asyncio.fixture
async def admin_client(client, admin_token):
    client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return client
