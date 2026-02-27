import pytest
import uuid

@pytest.mark.asyncio
async def test_create_account(auth_client):
    response = await auth_client.post(
        "/api/v1/accounts/",
        json={
            "name": "Test Account",
            "balance": 1000.0,
            "iban": "DE89370400440532013000",
            "type": "Giro",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Account"
    assert float(data["balance"]) == 1000.0

@pytest.mark.asyncio
async def test_read_accounts(auth_client):
    # Create two accounts
    await auth_client.post(
        "/api/v1/accounts/",
        json={"name": "Account 1", "balance": 100.0, "type": "Credit Card"},
    )
    await auth_client.post(
        "/api/v1/accounts/",
        json={"name": "Account 2", "balance": 200.0, "type": "Credit Card"},
    )
    
    response = await auth_client.get("/api/v1/accounts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

@pytest.mark.asyncio
async def test_update_account(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/accounts/",
        json={"name": "Old Name", "balance": 50.0, "type": "Credit Card"},
    )
    account_id = create_resp.json()["id"]
    
    response = await auth_client.put(
        f"/api/v1/accounts/{account_id}",
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"

@pytest.mark.asyncio
async def test_delete_account(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/accounts/",
        json={"name": "To Delete", "balance": 0.0, "type": "Credit Card"},
    )
    account_id = create_resp.json()["id"]
    
    response = await auth_client.delete(f"/api/v1/accounts/{account_id}")
    assert response.status_code == 204
    
    get_resp = await auth_client.get(f"/api/v1/accounts/{account_id}")
    assert get_resp.status_code == 404
