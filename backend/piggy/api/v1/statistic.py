"""
v1 API routes for statistics.
"""

from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.core.auth import get_current_user
from piggy.core.database import get_db
from piggy.core.statistics import (
    categories_spent_statistics,
    balance_statistics,
    budget_usage_statistics,
    cashflow_statistics,
)
from piggy.models.database.user import User as UserDB
from piggy.models.statistic import (
    CategorySpendStatistics,
    AccountBalanceStatistics,
    BudgetUsageStatistics,
    CashflowStatistics,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/category", response_model=list[CategorySpendStatistics])
async def get_category_spend_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Get category spend statistics"""
    return await categories_spent_statistics(db, current_user)


@router.get("/balance", response_model=list[AccountBalanceStatistics])
async def get_account_balance_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Get account balance statistics"""
    return await balance_statistics(db, current_user)


@router.get("/budget", response_model=BudgetUsageStatistics)
async def get_budget_usage_statistics(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Get budget usage statistics for a specific year and month"""
    return await budget_usage_statistics(db, current_user, year, month)


@router.get("/cashflow", response_model=CashflowStatistics)
async def get_cashflow_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Get monthly cashflow statistics (income vs expenses) for the last 12 months"""
    return await cashflow_statistics(db, current_user)
