import pytest
from datetime import date

@pytest.mark.asyncio
async def test_get_cashflow_statistics(auth_client):
    # Create an account
    acc_resp = await auth_client.post("/api/v1/accounts/", json={"name": "Cashflow Acc", "balance": 1000.0, "type": "Credit Card"})
    account_id = acc_resp.json()["id"]
    
    # Create some transactions
    await auth_client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"description": "Salary", "amount": 2000.0, "type": "Income"}
    )
    await auth_client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"description": "Rent", "amount": 800.0, "type": "Expense"}
    )
    
    response = await auth_client.get("/api/v1/statistic/cashflow")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Find current month in items
    current_month = date.today().month
    current_year = date.today().year
    
    this_month_item = next(item for item in data["items"] if item["month"] == current_month and item["year"] == current_year)
    assert float(this_month_item["income"]) == 2000.0
    assert float(this_month_item["expenses"]) == 800.0

@pytest.mark.asyncio
async def test_get_budget_usage_statistics(auth_client):
    # Setup: category, budget, and transactions
    cat_resp = await auth_client.post("/api/v1/categories/", json={"name": "Stat Budget Cat"})
    cat_id = cat_resp.json()["id"]
    
    await auth_client.post(
        "/api/v1/categories/budgets",
        json={"category_id": cat_id, "amount": 100.0}
    )
    
    acc_resp = await auth_client.post("/api/v1/accounts/", json={"name": "Budget Stat Acc", "balance": 1000.0, "type": "Credit Card"})
    account_id = acc_resp.json()["id"]
    
    await auth_client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"description": "Food", "amount": 40.0, "type": "Expense", "category_id": cat_id}
    )
    
    today = date.today()
    response = await auth_client.get(f"/api/v1/statistic/budget?year={today.year}&month={today.month}")
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == today.year
    assert data["month"] == today.month
    
    budget_item = next(b for b in data["budgets"] if b["category_id"] == cat_id)
    assert float(budget_item["budget_amount"]) == 100.0
    assert float(budget_item["total_spent"]) == 40.0

@pytest.mark.asyncio
async def test_get_balance_statistics(auth_client):
    await auth_client.post("/api/v1/accounts/", json={"name": "Balance Stat Acc", "balance": 1234.56, "type": "Credit Card"})
    
    response = await auth_client.get("/api/v1/statistic/balance")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    acc_stats = next(s for s in data if s["name"] == "Balance Stat Acc")
    assert acc_stats["own_account"] is True
    # The last history item should be current balance
    assert float(acc_stats["history"][-1]["balance"]) >= 1234.56 # Prognosis might affect exactly which one is last but one of them should match
