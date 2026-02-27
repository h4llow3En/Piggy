import pytest
from datetime import date

@pytest.mark.asyncio
async def test_create_recurring_payment(auth_client):
    response = await auth_client.post(
        "/api/v1/recurring-payments/",
        json={
            "name": "Netflix",
            "amount": 17.99,
            "type": "Expense",
            "interval": "Monthly",
            "start_date": date.today().isoformat(),
            "is_subscription": True
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Netflix"
    assert float(data["amount"]) == 17.99

@pytest.mark.asyncio
async def test_read_recurring_payments(auth_client):
    await auth_client.post(
        "/api/v1/recurring-payments/",
        json={
            "name": "Internet",
            "amount": 40.0,
            "type": "Expense",
            "interval": "Monthly",
            "start_date": date.today().isoformat()
        },
    )
    
    response = await auth_client.get("/api/v1/recurring-payments/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Internet"

@pytest.mark.asyncio
async def test_update_recurring_payment(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/recurring-payments/",
        json={
            "name": "Gym",
            "amount": 30.0,
            "type": "Expense",
            "interval": "Monthly",
            "start_date": date.today().isoformat()
        },
    )
    payment_id = create_resp.json()["id"]
    
    response = await auth_client.put(
        f"/api/v1/recurring-payments/{payment_id}",
        json={"amount": 35.0},
    )
    assert response.status_code == 200
    assert float(response.json()["amount"]) == 35.0

@pytest.mark.asyncio
async def test_delete_recurring_payment(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/recurring-payments/",
        json={
            "name": "To Delete",
            "amount": 10.0,
            "type": "Expense",
            "interval": "Monthly",
            "start_date": date.today().isoformat()
        },
    )
    payment_id = create_resp.json()["id"]
    
    response = await auth_client.delete(f"/api/v1/recurring-payments/{payment_id}")
    assert response.status_code == 204
    
    get_resp = await auth_client.get(f"/api/v1/recurring-payments/{payment_id}")
    assert get_resp.status_code == 404
