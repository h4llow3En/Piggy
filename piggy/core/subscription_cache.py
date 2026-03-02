"""
Cache management for subscription detection results: nightly rebuild for all users,
manual rebuild for a specific user, and ignore-list handling.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.core.subscriptions import (
    detect_potential_recurring_payments,
    normalize_description,
)
from piggy.models.database.subscription import SubscriptionCandidate, SubscriptionIgnore
from piggy.models.database.user import User


async def rebuild_all_users(db: AsyncSession) -> int:
    """Rebuild cached subscription candidates for all users. Returns number of users processed."""
    users = (await db.execute(select(User.id))).scalars().all()
    for uid in users:
        await rebuild_user(db, uid)
    return len(users)


async def rebuild_user(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Rebuild cached candidates for a single user. Returns number of candidates stored."""
    # Load ignores
    ignores = (
        await db.execute(
            select(SubscriptionIgnore.normalized_name, SubscriptionIgnore.amount).where(
                SubscriptionIgnore.user_id == user_id
            )
        )
    ).all()
    ignore_set = {(row.normalized_name, row.amount) for row in ignores}

    candidates = await detect_potential_recurring_payments(db, user_id)

    filtered = []
    for c in candidates:
        norm = normalize_description(c.name)
        key_exact = (norm, c.amount)
        key_any_amount = (norm, None)
        if key_exact in ignore_set or key_any_amount in ignore_set:
            continue
        filtered.append(c)

    await db.execute(
        delete(SubscriptionCandidate).where(SubscriptionCandidate.user_id == user_id)
    )

    now = datetime.now(timezone.utc)
    for c in filtered:
        row = SubscriptionCandidate(
            user_id=user_id,
            name=c.name,
            normalized_name=normalize_description(c.name),
            amount=c.amount,
            interval=(
                c.interval.value if hasattr(c.interval, "value") else str(c.interval)
            ),
            count=c.count,
            last_date=c.last_date,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    await db.commit()
    return len(filtered)


async def add_ignore(
    db: AsyncSession, user_id: uuid.UUID, name: str, amount=None
) -> None:
    """Add a potential recurring payment to ignore list for user."""
    norm = normalize_description(name)
    now = datetime.now(timezone.utc)

    if amount is None:
        amount_condition = SubscriptionIgnore.amount.is_(None)
    else:
        amount_condition = SubscriptionIgnore.amount == amount

    existing = await db.execute(
        select(SubscriptionIgnore).where(
            and_(
                SubscriptionIgnore.user_id == user_id,
                SubscriptionIgnore.normalized_name == norm,
                amount_condition,
            )
        )
    )
    if existing.scalars().first() is None:
        db.add(
            SubscriptionIgnore(
                user_id=user_id,
                normalized_name=norm,
                amount=amount,
                created_at=now,
            )
        )
        await db.commit()


async def list_ignores(db: AsyncSession, user_id: uuid.UUID):
    """List ignored recurring payment suggestions for user."""
    rows = (
        (
            await db.execute(
                select(SubscriptionIgnore).where(SubscriptionIgnore.user_id == user_id)
            )
        )
        .scalars()
        .all()
    )
    return rows


async def list_cached_candidates(db: AsyncSession, user_id: uuid.UUID):
    """List cached recurring payment suggestions for user."""
    rows = (
        (
            await db.execute(
                select(SubscriptionCandidate)
                .where(SubscriptionCandidate.user_id == user_id)
                .order_by(
                    SubscriptionCandidate.count.desc(),
                    SubscriptionCandidate.last_date.desc(),
                )
            )
        )
        .scalars()
        .all()
    )
    return rows
