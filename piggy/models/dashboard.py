"""
Dashboard models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-function-docstring,missing-class-docstring


import uuid
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class BudgetStatus(BaseModel):
    category_id: uuid.UUID
    category_name: str
    budget_amount: Decimal
    spent_amount: Decimal
    user_id: Optional[uuid.UUID] = None


class DashboardSummary(BaseModel):
    total_balance: Decimal
    monthly_income: Decimal
    monthly_expenses: Decimal
    monthly_balance: Decimal
    prognosis_balance: Optional[Decimal] = None


class DashboardData(BaseModel):
    summary: DashboardSummary
    budgets: List[BudgetStatus]
