"""
Database models for subscription detection cache and ignore list.
"""

# pylint: disable=too-few-public-methods,missing-class-docstring

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import UUID, String, ForeignKey, DateTime, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from piggy.core.database import Base


class SubscriptionCandidate(Base):
    __tablename__ = "subscription_candidates"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "normalized_name", "amount", "interval", name="uq_sub_candidate"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    interval: Mapped[str] = mapped_column(String(50), nullable=False)
    count: Mapped[int] = mapped_column(nullable=False)
    last_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SubscriptionIgnore(Base):
    __tablename__ = "subscription_ignores"
    __table_args__ = (
        UniqueConstraint("user_id", "normalized_name", "amount", name="uq_sub_ignore"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user = relationship("User")
