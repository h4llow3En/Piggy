"""
Task functions for the Piggy application.
"""

import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import delete

from piggy.core.database import async_session
from piggy.core.subscription_cache import rebuild_all_users
from piggy.models.database.user import User

logger = logging.getLogger(__name__)


async def cleanup_unverified_users():
    """Remove unverified users older than 24 hours."""
    async with async_session() as session:
        limit = datetime.now(timezone.utc) - timedelta(hours=24)
        stmt = delete(User).where(
            User.email_verified.is_(False),
            User.created_at < limit,
        )
        result = await session.execute(stmt)
        await session.commit()
        logger.info("Cleaned up %d unverified users", result.rowcount)


async def rebuild_subscription_candidates_nightly():
    """Rebuild cached subscription candidates for all users (nightly job)."""
    async with async_session() as session:
        count = await rebuild_all_users(session)
        logger.info("Rebuilt subscription candidates for %d users", count)
