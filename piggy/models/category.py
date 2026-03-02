"""
Category and budget models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-function-docstring,missing-class-docstring

import uuid
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class Category(CategoryRead):
    budgets: List["Budget"] = []


class CategoryWithBudgets(Category):
    budgets: List["Budget"]


class BudgetBase(BaseModel):
    amount: Decimal
    user_id: Optional[uuid.UUID] = None


class BudgetCreate(BudgetBase):
    category_id: uuid.UUID


class BudgetUpdate(BaseModel):
    amount: Optional[Decimal] = None
    user_id: Optional[uuid.UUID] = None


class Budget(BudgetBase):
    id: uuid.UUID
    category_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class BudgetWithCategory(Budget):
    category: CategoryRead
