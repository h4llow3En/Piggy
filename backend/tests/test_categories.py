import pytest

@pytest.mark.asyncio
async def test_create_category(auth_client):
    response = await auth_client.post(
        "/api/v1/categories/",
        json={"name": "Test Category"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Category"

@pytest.mark.asyncio
async def test_create_category_duplicate(auth_client):
    await auth_client.post(
        "/api/v1/categories/",
        json={"name": "Duplicate"},
    )
    response = await auth_client.post(
        "/api/v1/categories/",
        json={"name": "Duplicate"},
    )
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_read_categories(auth_client):
    await auth_client.post(
        "/api/v1/categories/",
        json={"name": "Cat 1"},
    )
    await auth_client.post(
        "/api/v1/categories/",
        json={"name": "Cat 2"},
    )
    response = await auth_client.get("/api/v1/categories/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

@pytest.mark.asyncio
async def test_read_category(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/categories/",
        json={"name": "Single Cat"},
    )
    cat_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/categories/{cat_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Single Cat"
