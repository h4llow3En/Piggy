"""
Database module.

This module provides database configuration and initialization for the Piggy API application.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase

from piggy.core.config import config

engine = create_async_engine(config.DATABASE_URL, echo=False)
async_session = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """Base class for all database models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with async_session() as session:
        yield session
