"""
Statistics models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-function-docstring,missing-class-docstring,duplicate-code

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CategorySpendItem(BaseModel):
    date: date
    amount: Decimal
    amount_user: Decimal


class CategorySpendStatistics(BaseModel):
    name: str
    items: list[CategorySpendItem]


class AccountBalanceItem(BaseModel):
    date: date
    balance: Decimal


class AccountBalanceStatistics(BaseModel):
    name: str
    own_account: bool
    history: list[AccountBalanceItem]


class BudgetUsageItem(BaseModel):
    category_id: str
    category_name: str
    budget_amount: Decimal
    total_spent: Decimal
    user_spent: Decimal
    user_percentage: Decimal


class BudgetUsageStatistics(BaseModel):
    year: int
    month: int
    budgets: list[BudgetUsageItem]


class MonthlyCashflowItem(BaseModel):
    year: int
    month: int
    income: Decimal
    expenses: Decimal


class CashflowStatistics(BaseModel):
    items: list[MonthlyCashflowItem]
