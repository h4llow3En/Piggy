"""
v1 API routes for transactions.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, or_, alias, extract
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.core.auth import get_current_user
from piggy.core.database import get_db
from piggy.core.i18n import _
from piggy.core.utils import get_account_or_404, apply_transaction_effect
from piggy.models.database.account import Account as AccountDB
from piggy.models.database.category import Category as CategoryDB
from piggy.models.database.transaction import Transaction as TransactionDB
from piggy.models.database.transaction import TransactionType
from piggy.models.database.user import User as UserDB
from piggy.models.transaction import TransactionCreate, Transaction, TransactionUpdate

router = APIRouter()


@router.post("/accounts/{account_id}/transactions", response_model=Transaction)
async def create_transaction(
    account_id: uuid.UUID,
    transaction_in: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Creates a new transaction."""
    created = await _create_transactions_internal(
        account_id, [transaction_in], db, current_user.id
    )
    return created[0]


@router.post(
    "/accounts/{account_id}/transactions/bulk", response_model=List[Transaction]
)
async def create_transactions_bulk(
    account_id: uuid.UUID,
    transactions_in: List[TransactionCreate],
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Creates multiple transactions at once."""
    return await _create_transactions_internal(
        account_id, transactions_in, db, current_user.id
    )


async def _create_transactions_internal(
    account_id: uuid.UUID,
    transactions_in: List[TransactionCreate],
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = None,
) -> List[TransactionDB]:
    created_transactions = []

    # Verify account ownership once
    await get_account_or_404(account_id, db, user_id)

    for transaction_in in transactions_in:
        if transaction_in.type == TransactionType.TRANSFER:
            if not transaction_in.target_account_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("errors.transfer_target_required"),
                )
            if transaction_in.target_account_id == account_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("errors.transfer_same_account"),
                )

        transaction_data = transaction_in.model_dump()
        if transaction_data.get("timestamp") is None:
            transaction_data.pop("timestamp", None)

        transaction = TransactionDB(**transaction_data, account_id=account_id)

        if transaction.category_id:
            res = await db.execute(
                select(CategoryDB).where(CategoryDB.id == transaction.category_id)
            )
            if not res.scalars().first():
                raise HTTPException(
                    status_code=400, detail=_("errors.category_not_found")
                )

        db.add(transaction)
        created_transactions.append(transaction)

    await db.commit()

    for tx in created_transactions:
        await db.refresh(tx)
        await apply_transaction_effect(tx, user_id, db)

    return created_transactions


@router.get("/accounts/{account_id}/transactions", response_model=List[Transaction])
async def read_transactions(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Returns all transactions for a given account."""
    await get_account_or_404(account_id, db, current_user.id)

    result = await db.execute(
        select(TransactionDB)
        .where(
            or_(
                TransactionDB.account_id == account_id,
                TransactionDB.target_account_id == account_id,
            )
        )
        .order_by(TransactionDB.timestamp.desc())
    )
    return result.scalars().all()


@router.get("/accounts/transactions", response_model=List[Transaction])
async def read_all_user_transactions(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    all_users: bool = False,
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Returns transactions. By default, only those of the current user.
    Supports filtering by month/year and pagination.
    """
    if all_users:
        query = select(TransactionDB)
    else:
        source_account = alias(AccountDB, name="source_account")
        target_account = alias(AccountDB, name="target_account")

        query = (
            select(TransactionDB)
            .outerjoin(source_account, TransactionDB.account_id == source_account.c.id)
            .outerjoin(
                target_account,
                TransactionDB.target_account_id == target_account.c.id,
            )
            .where(
                or_(
                    source_account.c.user_id == current_user.id,
                    target_account.c.user_id == current_user.id,
                )
            )
            .distinct()
        )

    if month:
        query = query.where(extract("month", TransactionDB.timestamp) == month)
    if year:
        query = query.where(extract("year", TransactionDB.timestamp) == year)

    result = await db.execute(
        query.order_by(TransactionDB.timestamp.desc()).limit(limit).offset(offset)
    )
    return result.scalars().all()


@router.get("/accounts/transactions/{transaction_id}", response_model=Transaction)
async def read_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Returns a single transaction by id"""
    result = await db.execute(
        select(TransactionDB)
        .join(AccountDB, TransactionDB.account_id == AccountDB.id)
        .where(TransactionDB.id == transaction_id, AccountDB.user_id == current_user.id)
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("errors.transaction_not_found"),
        )
    return transaction


@router.put("/accounts/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: uuid.UUID,
    transaction_in: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Updates a transaction"""
    if transaction_in.type == TransactionType.TRANSFER:
        if not transaction_in.target_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_("errors.transfer_target_required"),
            )
        if transaction_in.target_account_id == transaction_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_("errors.transfer_same_account"),
            )
    transaction = await read_transaction(transaction_id, db, current_user)

    await apply_transaction_effect(transaction, current_user.id, db, revert=True)

    if transaction_in.amount is not None:
        transaction.amount = transaction_in.amount

    if transaction_in.type is not None:
        transaction.type = transaction_in.type

    if transaction_in.description is not None:
        transaction.description = transaction_in.description

    if transaction_in.category_id is not None:

        res = await db.execute(
            select(CategoryDB).where(CategoryDB.id == transaction_in.category_id)
        )
        if not res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_("errors.category_not_found"),
            )
        transaction.category_id = transaction_in.category_id

    if transaction_in.target_account_id is not None:
        transaction.target_account_id = transaction_in.target_account_id

    if transaction_in.timestamp is not None:
        transaction.timestamp = transaction_in.timestamp

    await db.commit()
    await db.refresh(transaction)
    await apply_transaction_effect(transaction, current_user.id, db)
    return transaction


@router.delete(
    "/accounts/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Delete a transaction by id."""
    transaction = await read_transaction(transaction_id, db, current_user)
    await apply_transaction_effect(transaction, current_user.id, db, revert=True)

    await db.delete(transaction)
    await db.commit()
