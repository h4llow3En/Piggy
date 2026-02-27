import pytest

@pytest.mark.asyncio
async def test_login_success(client, test_user):
    response = await client.post(
        "/api/v1/users/login",
        data={"username": "test@example.com", "password": "password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_fail_wrong_password(client, test_user):
    response = await client.post(
        "/api/v1/users/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_fail_inactive_user(client, db, test_user):
    test_user.is_active = False
    await db.commit()
    
    response = await client.post(
        "/api/v1/users/login",
        data={"username": "test@example.com", "password": "password"},
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token(client, test_user):
    login_response = await client.post(
        "/api/v1/users/login",
        data={"username": "test@example.com", "password": "password"},
    )
    refresh_token = login_response.json()["refresh_token"]
    
    response = await client.post(
        "/api/v1/users/refresh-token",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
