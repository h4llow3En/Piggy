import pytest
from datetime import date

@pytest.mark.asyncio
async def test_export_csv(auth_client):
    response = await auth_client.get("/api/v1/exports/transactions.csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

@pytest.mark.asyncio
async def test_export_pdf(auth_client):
    today = date.today()
    response = await auth_client.get(f"/api/v1/exports/monthly-report.pdf?year={today.year}&month={today.month}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_export_pdf_with_non_latin1_description(auth_client):
    """
    fpdf2's built-in fonts only cover cp1252, so an emoji or Cyrillic text in a
    description used to abort the export with a 500.
    """
    acc_resp = await auth_client.post(
        "/api/v1/accounts/",
        json={"name": "Unicode Acc", "balance": 500.0, "type": "Credit Card"},
    )
    account_id = acc_resp.json()["id"]

    cat_resp = await auth_client.post("/api/v1/categories/", json={"name": "Кириллица 🎉"})
    category_id = cat_resp.json()["id"]

    await auth_client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={
            "description": "Ресторан 🍕 dinner",
            "amount": 42.0,
            "type": "Expense",
            "category_id": category_id,
        },
    )

    today = date.today()
    response = await auth_client.get(
        f"/api/v1/exports/monthly-report.pdf?year={today.year}&month={today.month}"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_export_pdf_rejects_invalid_month(auth_client):
    """month=13 reached date() and raised, which surfaced as a 500."""
    response = await auth_client.get("/api/v1/exports/monthly-report.pdf?year=2026&month=13")
    assert response.status_code == 422
