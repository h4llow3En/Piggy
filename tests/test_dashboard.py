import pytest
from datetime import date

@pytest.mark.asyncio
async def test_get_dashboard_summary(auth_client):
    today = date.today()
    
    # Create account and transactions
    acc_resp = await auth_client.post("/api/v1/accounts/", json={"name": "Dash Acc", "balance": 1000.0, "type": "Credit Card"})
    account_id = acc_resp.json()["id"]
    
    await auth_client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"description": "Dash Income", "amount": 100.0, "type": "Income"}
    )
    
    response = await auth_client.get(f"/api/v1/dashboard/summary?month={today.month}&year={today.year}")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert float(data["summary"]["total_balance"]) == 1100.0
    assert float(data["summary"]["monthly_income"]) == 100.0
    assert "budgets" in data
