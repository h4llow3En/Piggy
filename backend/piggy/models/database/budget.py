"""
Database Budget models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-class-docstring

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UUID, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from piggy.core.database import Base

if TYPE_CHECKING:
    from piggy.models.database.user import User
    from piggy.models.database.category import Category


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    category: Mapped["Category"] = relationship("Category", back_populates="budgets")
    user: Mapped[Optional["User"]] = relationship("User")
