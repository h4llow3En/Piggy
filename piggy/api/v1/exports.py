"""
Exports API endpoints.
"""

import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.core.auth import get_current_user
from piggy.core.database import get_db
from piggy.core.export import export_transactions_csv, generate_monthly_pdf_report
from piggy.models.database.user import User as UserDB

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/transactions.csv")
async def export_transactions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Export transactions as CSV for the current user."""
    csv_data = await export_transactions_csv(db, current_user.id, start_date, end_date)
    headers = {"Content-Disposition": "attachment; filename=transactions.csv"}
    return StreamingResponse(
        io.BytesIO(csv_data.encode("utf-8")), media_type="text/csv", headers=headers
    )


@router.get("/monthly-report.pdf")
async def export_monthly_report(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Generate and return a monthly PDF report for the current user."""
    pdf_bytes = await generate_monthly_pdf_report(db, current_user.id, year, month)
    headers = {
        "Content-Disposition": f"attachment; filename=report-{year}-{month:02d}.pdf"
    }
    return StreamingResponse(
        io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers
    )
