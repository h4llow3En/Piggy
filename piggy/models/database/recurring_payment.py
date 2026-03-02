"""
Database RecurringPayment models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-class-docstring,duplicate-code


import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, UUID, ForeignKey, Numeric, Date, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from piggy.core.database import Base
from piggy.models.database.transaction import TransactionType

if TYPE_CHECKING:
    from piggy.models.database.user import User
    from piggy.models.database.account import Account
    from piggy.models.database.category import Category


class RecurringInterval(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    SEMI_ANNUALLY = "Semi-Annually"
    YEARLY = "Yearly"
    DAYS_X = "Every X Days"


class RecurringPayment(Base):
    __tablename__ = "recurring_payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    type: Mapped[TransactionType] = mapped_column(
        String(50), nullable=False, default=TransactionType.EXPENSE
    )

    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True
    )
    target_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )

    interval: Mapped[RecurringInterval] = mapped_column(
        String(50), nullable=False, default=RecurringInterval.MONTHLY
    )
    interval_x_days: Mapped[Optional[int]] = mapped_column(
        nullable=True
    )  # Used when interval is DAYS_X

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),  # pylint: disable=not-callable
    )
    is_subscription: Mapped[bool] = mapped_column(Boolean, default=False)

    last_generated_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),  # pylint: disable=not-callable
    )

    user: Mapped["User"] = relationship("User")
    account: Mapped[Optional["Account"]] = relationship(
        "Account", foreign_keys=[account_id]
    )
    target_account: Mapped[Optional["Account"]] = relationship(
        "Account", foreign_keys=[target_account_id]
    )
    category: Mapped[Optional["Category"]] = relationship("Category")
