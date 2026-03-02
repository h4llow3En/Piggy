"""
v1 API routes for accounts.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from piggy.core.auth import get_current_user
from piggy.core.database import get_db
from piggy.core.i18n import _
from piggy.core.utils import get_account_or_404
from piggy.models.account import (
    Account,
    AccountCreate,
    AccountSortUpdate,
    AccountUpdate,
    AccountWithUser,
)
from piggy.models.database.account import Account as AccountDB
from piggy.models.database.user import User as UserDB

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/", response_model=Account)
async def create_account(
    account_in: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Create a new account."""
    if account_in.iban:
        result = await db.execute(
            select(AccountDB).where(AccountDB.iban == account_in.iban)
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_("errors.iban_already_exists"),
            )

    account = AccountDB(**account_in.model_dump(), user_id=current_user.id)
    db.add(account)
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_("errors.iban_already_exists"),
        ) from error

    await db.refresh(account)
    return account


@router.get("/", response_model=List[Account])
async def read_accounts(
    all_users: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Returns accounts. By default, only those of the current user.
    If all_users=True, all accounts in the system are returned.
    """

    if all_users:
        result = await db.execute(
            select(AccountDB).order_by(AccountDB.sort_order.asc(), AccountDB.name.asc())
        )
    else:
        result = await db.execute(
            select(AccountDB)
            .where(AccountDB.user_id == current_user.id)
            .order_by(AccountDB.name.asc(), AccountDB.sort_order.asc())
        )
    return result.scalars().all()


@router.get("/transfer-targets", response_model=List[AccountWithUser])
async def read_transfer_targets(
    db: AsyncSession = Depends(get_db), current_user: UserDB = Depends(get_current_user)
):
    """
    Returns accounts for transfer target selection.
    Sorted by:
    1. Own accounts (first), then other users' accounts.
    2. Grouped by user.
    3. Within each user group, sorted by sort_order.
    """

    # Load all active accounts with their users
    result = await db.execute(
        select(AccountDB)
        .options(joinedload(AccountDB.user))
        .order_by(
            case((AccountDB.user_id == current_user.id, 0), else_=1).asc(),
            AccountDB.user_id.asc(),
            AccountDB.sort_order.asc(),
            AccountDB.name.asc(),
        )
    )

    return [
        AccountWithUser(**Account.model_validate(a).model_dump(), user_name=a.user.name)
        for a in result.scalars().all()
    ]


@router.put("/sort", status_code=status.HTTP_204_NO_CONTENT)
async def update_accounts_sort(
    sort_data: List[AccountSortUpdate],
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Update sort order for multiple accounts.
    """
    for item in sort_data:
        await db.execute(
            update(AccountDB)
            .where(
                AccountDB.id == item.account_id, AccountDB.user_id == current_user.id
            )
            .values(sort_order=item.sort_order)
        )

    await db.commit()


@router.get("/{account_id}", response_model=Account)
async def read_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Return a single account by id
    """
    return await get_account_or_404(account_id, db, current_user.id)


@router.put("/{account_id}", response_model=Account)
async def update_account(
    account_id: uuid.UUID,
    account_in: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Update an existing account."""
    account = await get_account_or_404(account_id, db, current_user.id)

    update_data = account_in.model_dump(exclude_unset=True)

    if "iban" in update_data and update_data["iban"]:
        result = await db.execute(
            select(AccountDB).where(
                AccountDB.iban == update_data["iban"], AccountDB.id != account_id
            )
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_("errors.iban_already_exists"),
            )

    for field, value in update_data.items():
        setattr(account, field, value)

    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_("errors.iban_already_exists"),
        ) from error
    await db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Delete an account."""
    account = await get_account_or_404(account_id, db, current_user.id)

    await db.delete(account)
    await db.commit()
