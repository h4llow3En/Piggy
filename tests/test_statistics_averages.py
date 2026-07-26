"""
Equivalence checks for the batched per-account average.

balance_statistics used to call get_past_transactions_average once per account.
The batched variant must produce the exact same numbers, otherwise the balance
prognosis silently changes.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from piggy.core.auth import get_password_hash
from piggy.core.utils import (
    get_past_transactions_average,
    get_past_transactions_average_per_account,
)
from piggy.models.database.account import Account
from piggy.models.database.recurring_payment import RecurringPayment, RecurringInterval
from piggy.models.database.transaction import Transaction, TransactionType
from piggy.models.database.user import User, UserRole


async def _seed(db):
    user = User(
        email="avg@example.com",
        hashed_password=get_password_hash("password"),
        name="Avg User",
        is_active=True,
        email_verified=True,
        role=UserRole.USER,
    )
    partner = User(
        email="avgpartner@example.com",
        hashed_password=get_password_hash("password"),
        name="Avg Partner",
        is_active=True,
        email_verified=True,
        role=UserRole.USER,
    )
    db.add_all([user, partner])
    await db.commit()
    await db.refresh(user)
    await db.refresh(partner)

    a = Account(user_id=user.id, name="A", type="Giro", balance=Decimal("0.00"))
    b = Account(user_id=user.id, name="B", type="Giro", balance=Decimal("0.00"))
    c = Account(user_id=partner.id, name="C", type="Giro", balance=Decimal("0.00"))
    db.add_all([a, b, c])
    await db.commit()
    for acc in (a, b, c):
        await db.refresh(acc)

    now = datetime.now()
    rows = [
        # Spread over several months so more than one group exists
        Transaction(account_id=a.id, description="Salary", amount=Decimal("2000.00"),
                    type=TransactionType.INCOME, timestamp=now - timedelta(days=20)),
        Transaction(account_id=a.id, description="Groceries", amount=Decimal("80.00"),
                    type=TransactionType.EXPENSE, timestamp=now - timedelta(days=40)),
        Transaction(account_id=a.id, description="Shoes", amount=Decimal("120.00"),
                    type=TransactionType.EXPENSE, timestamp=now - timedelta(days=75)),
        # Transfer between two accounts of the same user
        Transaction(account_id=a.id, target_account_id=b.id, description="To savings",
                    amount=Decimal("300.00"), type=TransactionType.TRANSFER,
                    timestamp=now - timedelta(days=25)),
        # Transfer to the partner's account
        Transaction(account_id=b.id, target_account_id=c.id, description="Rent share",
                    amount=Decimal("450.00"), type=TransactionType.TRANSFER,
                    timestamp=now - timedelta(days=35)),
        # Matches a recurring payment and must be excluded
        Transaction(account_id=a.id, description="Netflix", amount=Decimal("17.99"),
                    type=TransactionType.EXPENSE, timestamp=now - timedelta(days=15)),
        # Outside the six month window
        Transaction(account_id=a.id, description="Ancient", amount=Decimal("999.00"),
                    type=TransactionType.EXPENSE, timestamp=now - timedelta(days=400)),
    ]
    db.add_all(rows)

    db.add(
        RecurringPayment(
            user_id=user.id,
            name="Netflix",
            amount=Decimal("17.99"),
            type=TransactionType.EXPENSE,
            interval=RecurringInterval.MONTHLY,
            start_date=(now - timedelta(days=200)).date(),
        )
    )
    await db.commit()
    return user, [a, b, c]


@pytest.mark.asyncio
async def test_batched_average_matches_per_account_average(db):
    user, accounts = await _seed(db)

    batched = await get_past_transactions_average_per_account(db, user)

    for acc in accounts:
        expected = await get_past_transactions_average(
            db, user, account_ids={acc.id}
        )
        actual = batched.get(acc.id, Decimal("0.00"))
        assert actual == pytest.approx(expected), f"mismatch for account {acc.name}"


@pytest.mark.asyncio
async def test_batched_average_skips_accounts_without_transactions(db):
    user, _ = await _seed(db)

    empty = Account(
        user_id=user.id, name="Empty", type="Giro", balance=Decimal("0.00")
    )
    db.add(empty)
    await db.commit()
    await db.refresh(empty)

    batched = await get_past_transactions_average_per_account(db, user)
    assert empty.id not in batched
    assert await get_past_transactions_average(
        db, user, account_ids={empty.id}
    ) == Decimal("0.00")


@pytest.mark.asyncio
async def test_batched_average_ignores_unknown_account(db):
    user, _ = await _seed(db)
    batched = await get_past_transactions_average_per_account(db, user)
    assert uuid.uuid4() not in batched
