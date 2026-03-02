"""
v1 API routes for recurring payments.
"""

import uuid
from decimal import Decimal
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, status
from piggy.core.auth import get_current_user
from piggy.core.database import get_db
from piggy.core.subscription_cache import add_ignore, rebuild_user
from piggy.core.subscription_cache import list_cached_candidates
from piggy.core.subscription_cache import list_ignores
from piggy.core.utils import (
    get_account_or_404,
    get_category_or_404,
    get_recurring_payment_or_404,
)
from piggy.models.database.recurring_payment import (
    RecurringPayment as RecurringPaymentDB,
)
from piggy.models.database.user import User as UserDB
from piggy.models.recurring_payment import (
    RecurringPayment,
    RecurringPaymentCreate,
    RecurringPaymentUpdate,
    SubscriptionCandidateResponse,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/detect", response_model=List[SubscriptionCandidateResponse])
async def get_cached_recurring_payments(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Retrieve cached potential recurring payment."""

    rows = await list_cached_candidates(db, current_user.id)
    return [
        SubscriptionCandidateResponse(
            name=r.name,
            amount=r.amount,
            interval=r.interval,
            count=r.count,
            last_date=r.last_date,
        )
        for r in rows
    ]


@router.post("/detect/ignore", status_code=status.HTTP_204_NO_CONTENT)
async def add_recurring_payment_ignore(
    name: str,
    amount: Decimal | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Ignore a suggested recurring payment."""
    await add_ignore(db, current_user.id, name, amount)
    await rebuild_user(db, current_user.id)
    return None


@router.get("/detect/ignore", response_model=List[str])
async def list_recurring_payment_ignores(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """List ignored recurring payments."""
    rows = await list_ignores(db, current_user.id)
    return [r.normalized_name for r in rows]


@router.post("/", response_model=RecurringPayment)
async def create_recurring_payment(
    payment_in: RecurringPaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Create a new recurring payment."""
    if payment_in.account_id:
        await get_account_or_404(payment_in.account_id, db, current_user.id)
    if payment_in.target_account_id:
        await get_account_or_404(payment_in.target_account_id, db)
    if payment_in.category_id:
        await get_category_or_404(payment_in.category_id, db)

    payment = RecurringPaymentDB(**payment_in.model_dump(), user_id=current_user.id)
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("/", response_model=List[RecurringPayment])
async def read_recurring_payments(
    db: AsyncSession = Depends(get_db), current_user: UserDB = Depends(get_current_user)
):
    """Retrieve all recurring payments for the current user."""
    result = await db.execute(
        select(RecurringPaymentDB).where(RecurringPaymentDB.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{recurring_payment_id}", response_model=RecurringPayment)
async def read_recurring_payment(
    recurring_payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Retrieve a specific recurring payment by ID for the current user."""
    return await get_recurring_payment_or_404(recurring_payment_id, db, current_user.id)


@router.put("/{recurring_payment_id}", response_model=RecurringPayment)
async def update_recurring_payment(
    recurring_payment_id: uuid.UUID,
    payment_in: RecurringPaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Update a specific recurring payment by ID for the current user."""
    payment = await get_recurring_payment_or_404(
        recurring_payment_id, db, current_user.id
    )

    update_data = payment_in.model_dump(exclude_unset=True)

    # Validation for accounts and categories if they are being updated
    if update_data.get("account_id"):
        await get_account_or_404(update_data["account_id"], db, current_user.id)
    if update_data.get("target_account_id"):
        await get_account_or_404(update_data["target_account_id"], db, current_user.id)
    if update_data.get("category_id"):
        await get_category_or_404(update_data["category_id"], db)

    for field, value in update_data.items():
        setattr(payment, field, value)

    await db.commit()
    await db.refresh(payment)
    return payment


@router.delete("/{recurring_payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_payment(
    recurring_payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Delete a specific recurring payment by ID for the current user."""
    payment = await get_recurring_payment_or_404(
        recurring_payment_id, db, current_user.id
    )

    await db.delete(payment)
    await db.commit()
    return None
