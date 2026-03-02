"""
v1 API routes for categories.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from piggy.core.auth import get_current_user
from piggy.core.database import get_db
from piggy.core.i18n import _
from piggy.core.utils import get_category_or_404
from piggy.models.category import CategoryRead, CategoryCreate, CategoryWithBudgets
from piggy.models.database.category import Category as CategoryDB

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/", response_model=CategoryRead)
async def create_category(
    category_in: CategoryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new category."""
    result = await db.execute(
        select(CategoryDB).where(CategoryDB.name == category_in.name)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_("errors.category_already_exists"),
        )

    category = CategoryDB(**category_in.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/", response_model=List[CategoryRead])
async def read_categories(
    db: AsyncSession = Depends(get_db),
):
    """Returns all categories."""
    result = await db.execute(select(CategoryDB))
    return result.scalars().all()


@router.get("/{category_id}", response_model=CategoryWithBudgets)
async def read_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return a single category by id"""

    return await get_category_or_404(
        category_id, db, options=selectinload(CategoryDB.budgets)
    )
