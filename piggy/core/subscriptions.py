"""
Module to detect potential /recurring payments.
"""
import re
import statistics
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.models.database.account import Account
from piggy.models.database.recurring_payment import RecurringInterval, RecurringPayment
from piggy.models.database.transaction import Transaction, TransactionType


class RecurringPaymentCandidate:  # pylint: disable=too-few-public-methods
    """
    Represents a potential recurring payment detected from transaction history.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        name: str,
        amount: Decimal,
        interval: RecurringInterval,
        count: int,
        last_date: datetime,
    ):
        self.name = name
        self.amount = amount
        self.interval = interval
        self.count = count
        self.last_date = last_date

    def to_dict(self):
        """
        Convert RecurringPaymentCandidate to dictionary for serialization.
        """
        return {
            "name": self.name,
            "amount": self.amount,
            "interval": self.interval,
            "count": self.count,
            "last_date": self.last_date.isoformat(),
        }


def normalize_description(desc: str) -> str:
    """Public helper to normalize descriptions consistently across API and tasks."""
    return _normalize_description(desc)


def _normalize_description(desc: str) -> str:
    """Normalize description to group similar transactions."""
    desc = desc.lower().strip()
    # Remove common variable parts like dates (DD.MM.YYYY, DD.MM.YY)
    desc = re.sub(r"\d{1,2}\.\d{1,2}\.\d{2,4}", "", desc)
    # Remove anything that looks like a transaction ID or reference number (long digit strings)
    desc = re.sub(r"\d{5,}", "", desc)
    # Remove extra spaces
    desc = re.sub(r"\s+", " ", desc)
    return desc.strip()


def _detect_interval(  # pylint: disable=too-many-return-statements
    txs: List[Transaction],
) -> Optional[RecurringInterval]:
    """Detect if transactions follow a regular interval.
    Returns the most likely interval or None if variance is too high.
    """
    if len(txs) < 2:
        return None

    intervals = []
    for i in range(1, len(txs)):
        diff = (txs[i].timestamp - txs[i - 1].timestamp).days
        intervals.append(diff)

    avg_interval = sum(intervals) / len(intervals)

    if len(intervals) > 1:
        stdev = statistics.stdev(intervals)
        if stdev > 5:
            return None

    if 25 <= avg_interval <= 35:
        return RecurringInterval.MONTHLY
    if 80 <= avg_interval <= 100:
        return RecurringInterval.QUARTERLY
    if 170 <= avg_interval <= 200:
        return RecurringInterval.SEMI_ANNUALLY
    if 350 <= avg_interval <= 390:
        return RecurringInterval.YEARLY
    if 6 <= avg_interval <= 8:
        return RecurringInterval.WEEKLY

    return None


async def detect_potential_recurring_payments(  # pylint: disable=too-many-locals
    db: AsyncSession, user_id: uuid.UUID
) -> List[RecurringPaymentCandidate]:
    """
    Analyzes transaction history to find potential recurring payments/subscriptions.
    Filters out common non-subscription recurring items like groceries by requiring
    exact amount matches and consistent intervals.
    """
    lookback_limit = datetime.now() - timedelta(days=730)

    query = (
        select(Transaction)
        .join(Account)
        .where(
            and_(
                Account.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.timestamp >= lookback_limit,
            )
        )
        .order_by(Transaction.timestamp.asc())
    )

    transactions = (await db.execute(query)).scalars().all()

    desc_groups = defaultdict(list)
    for tx in transactions:
        norm_desc = _normalize_description(tx.description)
        if len(norm_desc) < 3:
            continue
        desc_groups[norm_desc].append(tx)

    candidates = []

    existing_query = select(RecurringPayment.name).where(
        RecurringPayment.user_id == user_id
    )
    existing_names = {
        name.lower().strip()
        for name in (await db.execute(existing_query)).scalars().all()
    }

    for norm_desc, txs in desc_groups.items():
        # Avoid already tracked subscriptions
        if any(
            norm_desc in existing_name or existing_name in norm_desc
            for existing_name in existing_names
        ):
            continue

        amount_groups = defaultdict(list)
        for tx in txs:
            amount_groups[tx.amount].append(tx)

        for amount, amt_txs in amount_groups.items():
            if len(amt_txs) < 2:
                continue

            # Check day-of-month consistency (avoid grocery-like weekly patterns)
            dom = [t.timestamp.day for t in amt_txs]
            if len(dom) > 1:
                try:
                    dom_stdev = statistics.stdev(dom)
                    if dom_stdev > 5:  # too scattered over the month
                        continue
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

            interval = _detect_interval(amt_txs)
            if not interval:
                continue

            min_counts = {
                RecurringInterval.WEEKLY: 4,
                RecurringInterval.MONTHLY: 3,
                RecurringInterval.QUARTERLY: 2,
                RecurringInterval.SEMI_ANNUALLY: 2,
                RecurringInterval.YEARLY: 2,
            }
            if len(amt_txs) < min_counts.get(interval, 3):
                continue

            candidates.append(
                RecurringPaymentCandidate(
                    name=amt_txs[-1].description,
                    amount=amount,
                    interval=interval,
                    count=len(amt_txs),
                    last_date=amt_txs[-1].timestamp,
                )
            )

    candidates.sort(key=lambda x: x.count, reverse=True)
    return candidates
