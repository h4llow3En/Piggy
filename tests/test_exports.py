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
