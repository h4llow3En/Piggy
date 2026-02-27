"""
Bank synchronization service using FinTS.

- Provides manual sync per connection (with PIN provided on demand)
- Provides scheduled sync that tries best-effort without storing PIN
- Maps imported transactions into existing DB models
- Deduplicates and categorizes locally
- Detects internal transfers by IBAN across all users
"""

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from sqlalchemy import select, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.core.bank.fints_client import FinTSClient, FinTSNotAvailable
from piggy.core.bank_sync_cache import sync_task_cache
from piggy.core.categorization import (
    suggest_category_id,
    is_internal_transfer_candidate,
)
from piggy.core.config import config
from piggy.core.database import async_session
from piggy.models.bank import SyncTaskStatus
from piggy.models.database.account import Account
from piggy.models.database.bank_connection import BankConnection
from piggy.models.database.transaction import Transaction, TransactionType
from piggy.models.transaction import BankTransactionPreview

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _managed_session():
    async with async_session() as session:
        yield session


async def _get_known_ibans(db: AsyncSession) -> set[str]:
    rows = await db.execute(select(Account.iban).where(Account.iban.is_not(None)))
    return {r[0] for r in rows.all() if r[0]}


async def _transaction_exists(
    db: AsyncSession,
    account_id,
    timestamp: datetime,
    amount: Decimal,
    description: str,
) -> bool:
    # dedupe based on exact match of 4 fields
    stmt = select(
        exists().where(
            and_(
                Transaction.account_id == account_id,
                Transaction.timestamp == timestamp,
                Transaction.amount == amount,
                Transaction.description == description,
            )
        )
    )
    return bool((await db.execute(stmt)).scalar())


def _parse_amount(s: str) -> Decimal:
    try:
        d = Decimal(s)
        return d.copy_abs()
    except InvalidOperation:  # pragma: no cover
        return Decimal("0.00")


def _infer_type(raw_amount: str) -> TransactionType:
    try:
        d = Decimal(raw_amount)
    except InvalidOperation:  # pragma: no cover
        d = Decimal("0.00")
    if d < 0:
        return TransactionType.EXPENSE
    if d > 0:
        return TransactionType.INCOME
    return TransactionType.EXPENSE


async def _is_potential_duplicate(
    db: AsyncSession, account_id, ts: datetime, amount: Decimal
) -> bool:
    window_start = ts - timedelta(days=3)
    window_end = ts + timedelta(days=3)
    stmt = select(
        exists().where(
            and_(
                Transaction.account_id == account_id,
                Transaction.amount == amount,
                Transaction.timestamp >= window_start,
                Transaction.timestamp <= window_end,
            )
        )
    )
    return bool((await db.execute(stmt)).scalar())


async def _get_internal_accounts(db: AsyncSession) -> dict:
    """Fetch and format internal accounts as a dict {iban: account_id}."""
    result = await db.execute(select(Account.id, Account.iban))
    return {
        iban: acc_id for acc_id, iban in [(r[0], r[1]) for r in result.all()] if iban
    }


async def _process_transaction(  # pylint: disable=too-many-arguments,too-many-positional-arguments)
    it,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    known_ibans: List[str],
    internal_accounts: dict,
    db: AsyncSession,
) -> Optional[BankTransactionPreview]:
    """Process a single FinTS transaction and return a preview item."""
    ts = datetime.combine(it.booking_date, datetime.min.time(), tzinfo=timezone.utc)
    amount = _parse_amount(it.amount)
    ttype = _infer_type(it.amount)

    target_account_id = None
    if is_internal_transfer_candidate(it.partner_iban, known_ibans):
        # skip transfers towards this account
        if ttype == TransactionType.INCOME:
            return None
        ttype = TransactionType.TRANSFER
        if it.partner_iban in internal_accounts:
            target_account_id = internal_accounts[it.partner_iban]

    # Update description for expenses
    description: str = it.description or ""
    if ttype == TransactionType.EXPENSE and it.partner_name:
        description = (
            f"{it.partner_name} - {description}" if description else it.partner_name
        )

    # suggestions
    category_id = None
    if ttype != TransactionType.TRANSFER:
        cat = await suggest_category_id(db, user_id=user_id, description=description)
        category_id = cat if cat else None

    is_dup = await _is_potential_duplicate(db, account_id, ts, amount)

    return BankTransactionPreview(
        account_id=account_id,
        description=description,
        amount=amount,
        type=ttype,
        category_id=category_id,
        target_account_id=target_account_id,
        timestamp=ts,
        is_potential_duplicate=is_dup,
    )


async def preview_connection(
    connection_id,
    *,
    pin: str,
    since: date,
    db: AsyncSession,
    task_id: Optional[uuid.UUID] = None,
) -> List[BankTransactionPreview]:
    """Fetch transactions via FinTS and return a preview list without persisting.
    Each item contains suggestion fields for the frontend.
    """

    conn = await db.get(BankConnection, connection_id)
    if not conn:
        return []

    until = datetime.now(timezone.utc).date()

    try:
        client = FinTSClient(
            conn.bank_code,
            conn.login,
            customer_id=conn.customer_id,
            server=conn.server,
            product_id=config.FINTS_PRODUCT_ID,
        )
    except FinTSNotAvailable:
        return []

    client.open(pin)

    if client.tan_required:
        if task_id:
            sync_task_cache.update_task(
                task_id,
                SyncTaskStatus.AWAITING_AUTHENTICATION,
                error=client.tan_message,
            )
        return []

    try:
        internal_accounts = await _get_internal_accounts(db)
        known_ibans = await _get_known_ibans(db)

        previews: List[BankTransactionPreview] = []
        for iban, account_id in internal_accounts.items():
            try:
                for it in client.fetch_transactions(iban, since, until):
                    if preview := await _process_transaction(
                        it, account_id, conn.user_id, known_ibans, internal_accounts, db
                    ):
                        previews.append(preview)
            except Exception:  # pylint: disable=broad-exception-caught
                continue
        return previews
    finally:
        try:
            client.close()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
