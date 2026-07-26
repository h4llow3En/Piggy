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


@pytest.mark.asyncio
async def test_personal_budget_always_belongs_to_creator(auth_client, test_user, second_user):
    """user_id in the payload is a mode switch, not a way to write in someone else's name."""
    cat_resp = await auth_client.post("/api/v1/categories/", json={"name": "Ownership Cat"})
    cat_id = cat_resp.json()["id"]

    response = await auth_client.post(
        "/api/v1/categories/budgets",
        json={"category_id": cat_id, "amount": 300.0, "user_id": str(second_user.id)},
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_personal_budget_of_others_is_readable_but_not_writable(
    auth_client, test_user, second_user_auth
):
    """Shared visibility is intended, silently overwriting a partner's budget is not."""
    cat_resp = await auth_client.post("/api/v1/categories/", json={"name": "Partner Cat"})
    cat_id = cat_resp.json()["id"]

    budget_resp = await auth_client.post(
        "/api/v1/categories/budgets",
        json={"category_id": cat_id, "amount": 100.0, "user_id": str(test_user.id)},
    )
    budget_id = budget_resp.json()["id"]

    read = await auth_client.get(
        f"/api/v1/categories/budgets/{budget_id}", headers=second_user_auth
    )
    assert read.status_code == 200

    update = await auth_client.put(
        f"/api/v1/categories/budgets/{budget_id}",
        json={"amount": 999.0},
        headers=second_user_auth,
    )
    assert update.status_code == 404

    delete = await auth_client.delete(
        f"/api/v1/categories/budgets/{budget_id}", headers=second_user_auth
    )
    assert delete.status_code == 404

    # Untouched
    check = await auth_client.get(f"/api/v1/categories/budgets/{budget_id}")
    assert float(check.json()["amount"]) == 100.0


@pytest.mark.asyncio
async def test_global_budget_is_writable_by_everyone(auth_client, second_user_auth):
    """Global budgets are shared household budgets, everyone may manage them."""
    cat_resp = await auth_client.post("/api/v1/categories/", json={"name": "Shared Cat"})
    cat_id = cat_resp.json()["id"]

    budget_resp = await auth_client.post(
        "/api/v1/categories/budgets",
        json={"category_id": cat_id, "amount": 100.0, "user_id": None},
    )
    budget_id = budget_resp.json()["id"]

    update = await auth_client.put(
        f"/api/v1/categories/budgets/{budget_id}",
        json={"amount": 250.0},
        headers=second_user_auth,
    )
    assert update.status_code == 200
    assert float(update.json()["amount"]) == 250.0

    delete = await auth_client.delete(
        f"/api/v1/categories/budgets/{budget_id}", headers=second_user_auth
    )
    assert delete.status_code == 204
