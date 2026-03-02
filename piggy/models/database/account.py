"""
Database Account models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-class-docstring,duplicate-code

import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, UUID, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from piggy.core.database import Base

if TYPE_CHECKING:
    from piggy.models.database.user import User
    from piggy.models.database.transaction import Transaction


class AccountType(str, Enum):
    """Account types for bank accounts."""

    GIRO = "Giro"
    SAVINGS = "Savings"
    CREDIT_CARD = "Credit Card"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[AccountType] = mapped_column(String(50), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    iban: Mapped[Optional[str]] = mapped_column(String(34), nullable=True, unique=True)
    sort_order: Mapped[int] = mapped_column(default=0)

    user: Mapped["User"] = relationship("User", back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
        foreign_keys="[Transaction.account_id]",
    )
