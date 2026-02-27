import pytest
import uuid
from datetime import datetime

@pytest.mark.asyncio
async def test_create_transaction(auth_client):
    # Create an account first
    acc_resp = await auth_client.post(
        "/api/v1/accounts/",
        json={"name": "Source", "balance": 1000.0, "type": "Credit Card"},
    )
    account_id = acc_resp.json()["id"]
    
    response = await auth_client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={
            "description": "Lunch",
            "amount": 15.50,
            "type": "Expense",
            "timestamp": datetime.now().isoformat()
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Lunch"
    assert float(data["amount"]) == 15.50
    
    # Check if balance updated
    acc_resp = await auth_client.get(f"/api/v1/accounts/{account_id}")
    assert float(acc_resp.json()["balance"]) == 984.50

@pytest.mark.asyncio
async def test_create_transfer(auth_client):
    # Create two accounts
    acc1_resp = await auth_client.post("/api/v1/accounts/", json={"name": "Acc 1", "balance": 100.0, "type": "Credit Card"})
    acc2_resp = await auth_client.post("/api/v1/accounts/", json={"name": "Acc 2", "balance": 50.0, "type": "Credit Card"})
    id1 = acc1_resp.json()["id"]
    id2 = acc2_resp.json()["id"]
    
    response = await auth_client.post(
        f"/api/v1/accounts/{id1}/transactions",
        json={
            "description": "Transfer",
            "amount": 30.0,
            "type": "Transfer",
            "target_account_id": id2
        },
    )
    assert response.status_code == 200
    
    # Check balances
    acc1_resp = await auth_client.get(f"/api/v1/accounts/{id1}")
    acc2_resp = await auth_client.get(f"/api/v1/accounts/{id2}")
    assert float(acc1_resp.json()["balance"]) == 70.0
    assert float(acc2_resp.json()["balance"]) == 80.0

@pytest.mark.asyncio
async def test_delete_transaction(auth_client):
    acc_resp = await auth_client.post("/api/v1/accounts/", json={"name": "Acc", "balance": 100.0, "type": "Credit Card"})
    account_id = acc_resp.json()["id"]
    
    tx_resp = await auth_client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"description": "Buy", "amount": 20.0, "type": "Expense"},
    )
    tx_id = tx_resp.json()["id"]
    
    # Revert effect
    await auth_client.delete(f"/api/v1/accounts/transactions/{tx_id}")
    
    acc_resp = await auth_client.get(f"/api/v1/accounts/{account_id}")
    assert float(acc_resp.json()["balance"]) == 100.0
