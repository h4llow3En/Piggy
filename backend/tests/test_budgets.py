import pytest
import uuid

@pytest.mark.asyncio
async def test_create_global_budget(auth_client):
    # Create category
    cat_resp = await auth_client.post("/api/v1/categories/", json={"name": "Budget Cat"})
    cat_id = cat_resp.json()["id"]
    
    response = await auth_client.post(
        "/api/v1/categories/budgets",
        json={"category_id": cat_id, "amount": 500.0, "user_id": None},
    )
    assert response.status_code == 200
    assert float(response.json()["amount"]) == 500.0

@pytest.mark.asyncio
async def test_create_personal_budget(auth_client, test_user):
    cat_resp = await auth_client.post("/api/v1/categories/", json={"name": "Personal Cat"})
    cat_id = cat_resp.json()["id"]
    
    response = await auth_client.post(
        "/api/v1/categories/budgets",
        json={"category_id": cat_id, "amount": 200.0, "user_id": str(test_user.id)},
    )
    assert response.status_code == 200
    assert float(response.json()["amount"]) == 200.0

@pytest.mark.asyncio
async def test_create_budget_conflict(auth_client):
    cat_resp = await auth_client.post("/api/v1/categories/", json={"name": "Conflict Cat"})
    cat_id = cat_resp.json()["id"]
    
    await auth_client.post(
        "/api/v1/categories/budgets",
        json={"category_id": cat_id, "amount": 100.0},
    )
    
    # Try creating another global budget for same category
    response = await auth_client.post(
        "/api/v1/categories/budgets",
        json={"category_id": cat_id, "amount": 200.0},
    )
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_update_budget(auth_client):
    cat_resp = await auth_client.post("/api/v1/categories/", json={"name": "Update Cat"})
    cat_id = cat_resp.json()["id"]
    
    budget_resp = await auth_client.post(
        "/api/v1/categories/budgets",
        json={"category_id": cat_id, "amount": 100.0},
    )
    budget_id = budget_resp.json()["id"]
    
    response = await auth_client.put(
        f"/api/v1/categories/budgets/{budget_id}",
        json={"amount": 150.0},
    )
    assert response.status_code == 200
    assert float(response.json()["amount"]) == 150.0

@pytest.mark.asyncio
async def test_delete_budget(auth_client):
    cat_resp = await auth_client.post("/api/v1/categories/", json={"name": "Delete Cat"})
    cat_id = cat_resp.json()["id"]
    
    budget_resp = await auth_client.post(
        "/api/v1/categories/budgets",
        json={"category_id": cat_id, "amount": 100.0},
    )
    budget_id = budget_resp.json()["id"]
    
    response = await auth_client.delete(f"/api/v1/categories/budgets/{budget_id}")
    assert response.status_code == 204
