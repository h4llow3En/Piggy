"""
Database model for external bank connections (FinTS/HBCI).
"""

# pylint: disable=too-few-public-methods,missing-class-docstring

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, UUID, DateTime, func, Date
from sqlalchemy.orm import Mapped, mapped_column

from piggy.core.database import Base


class BankConnection(Base):
    __tablename__ = "bank_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    bank_code: Mapped[str] = mapped_column(String(16), nullable=False)  # BLZ/BIC Code
    login: Mapped[str] = mapped_column(String(128), nullable=False)
    customer_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    server: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), default="ready"
    )  # ready|awaiting_tan|error
    consent_valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),  # pylint: disable=not-callable
    )
