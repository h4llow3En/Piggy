"""
v1 API routes for budgets.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from piggy.core.auth import get_current_user
from piggy.core.database import get_db
from piggy.core.i18n import _
from piggy.core.utils import get_category_or_404, get_budget_or_404
from piggy.models.category import Budget, BudgetCreate, BudgetWithCategory, BudgetUpdate
from piggy.models.database.budget import Budget as BudgetDB

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/categories/budgets", response_model=Budget)
async def create_budget(
    budget_in: BudgetCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new budget.
    If user_id is not set in budget_in, we attempt to create a global budget.
    If user_id is set, a personal one.
    """

    await get_category_or_404(budget_in.category_id, db)

    result = await db.execute(
        select(BudgetDB).where(BudgetDB.category_id == budget_in.category_id)
    )
    existing_budgets = result.scalars().all()

    is_global_request = budget_in.user_id is None

    if is_global_request:
        if existing_budgets:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_("errors.budget_already_exists"),
            )
    else:
        for b in existing_budgets:
            if b.user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=_("errors.budget_already_exists"),
                )
            if b.user_id == budget_in.user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=_("errors.budget_already_exists"),
                )

    budget = BudgetDB(**budget_in.model_dump())
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


@router.get("/categories/budgets", response_model=List[BudgetWithCategory])
async def read_budgets(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all budgets with their associated categories.
    """
    result = await db.execute(select(BudgetDB).options(joinedload(BudgetDB.category)))
    return result.scalars().all()


@router.get("/categories/budgets/{budget_id}", response_model=Budget)
async def read_budget(
    budget_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return a single budget by id"""
    return await get_budget_or_404(budget_id, db)


@router.put("/categories/budgets/{budget_id}", response_model=Budget)
async def update_budget(
    budget_id: uuid.UUID,
    budget_in: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a budget by id"""
    budget = await get_budget_or_404(budget_id, db)

    update_data = budget_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)

    await db.commit()
    await db.refresh(budget)
    return budget


@router.delete(
    "/categories/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_budget(
    budget_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a budget by id"""
    budget = await get_budget_or_404(budget_id, db)

    await db.delete(budget)
    await db.commit()
    return None
