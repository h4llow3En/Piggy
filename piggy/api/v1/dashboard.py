"""
v1 API routes for dashboard.
"""

from datetime import date

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.core.auth import get_current_user
from piggy.core.database import get_db
from piggy.core.utils import (
    get_transactions_of_month,
    calculate_balance,
    get_budget_status,
)
from piggy.models.dashboard import DashboardData, DashboardSummary
from piggy.models.database.user import User

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=DashboardData)
async def get_dashboard_summary(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    all_users: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns summary data for the dashboard."""
    today = date.today()
    is_current_month = month == today.month and year == today.year
    current_user = current_user if not all_users else None

    transactions, account_ids = await get_transactions_of_month(
        db, month, year, current_user
    )

    all_transactions, _ = await get_transactions_of_month(db, month, year)

    balance, monthly_income, monthly_expenses, monthly_balance, prognosed_balance = (
        await calculate_balance(
            db, current_user, transactions, account_ids, today, is_current_month
        )
    )
    return DashboardData(
        summary=DashboardSummary(
            total_balance=balance,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            monthly_balance=monthly_balance,
            prognosis_balance=prognosed_balance,
        ),
        budgets=await get_budget_status(db, current_user, all_transactions),
    )
