import pytest
import uuid
from piggy.models.database.user import UserRole

@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post(
        "/api/v1/users/register",
        json={"email": "new@example.com", "password": "newpassword", "name": "New User"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["name"] == "New User"
    assert "id" in data

@pytest.mark.asyncio
async def test_read_user_me(auth_client, test_user):
    response = await auth_client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name

@pytest.mark.asyncio
async def test_update_user_me(auth_client, test_user):
    response = await auth_client.put(
        "/api/v1/users/me",
        json={"name": "Updated Name"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"

@pytest.mark.asyncio
async def test_list_users_admin(admin_client, test_user, test_admin):
    response = await admin_client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

@pytest.mark.asyncio
async def test_list_users_forbidden(auth_client):
    response = await auth_client.get("/api/v1/users/")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_register_user_already_exists(client, test_user):
    response = await client.post(
        "/api/v1/users/register",
        json={"email": test_user.email, "password": "password", "name": "Duplicate"},
    )
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_verify_email(client, db, test_user):
    from piggy.core.auth import create_access_token
    # Need a user with a verification token
    test_user.verification_token = "some_token"
    test_user.email_verified = False
    await db.commit()
    
    response = await client.get(f"/api/v1/users/verify-email/some_token")
    assert response.status_code == 307  # Redirects to frontend
    
    await db.refresh(test_user)
    assert test_user.email_verified is True

@pytest.mark.asyncio
async def test_delete_user_me(auth_client, db, test_user):
    response = await auth_client.delete("/api/v1/users/me")
    assert response.status_code == 204
    
    from sqlalchemy import select
    from piggy.models.database.user import User as UserDB
    result = await db.execute(select(UserDB).where(UserDB.id == test_user.id))
    assert result.scalars().first() is None
