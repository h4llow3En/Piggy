"""
Transaction models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-function-docstring,missing-class-docstring,duplicate-code

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from piggy.models.database.transaction import TransactionType


class TransactionBase(BaseModel):
    description: str
    amount: Decimal
    type: TransactionType = TransactionType.EXPENSE
    category_id: Optional[uuid.UUID] = None
    target_account_id: Optional[uuid.UUID] = None
    timestamp: Optional[datetime] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v.quantize(Decimal("0.00"))


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    type: Optional[TransactionType] = None
    category_id: Optional[uuid.UUID] = None
    target_account_id: Optional[uuid.UUID] = None
    timestamp: Optional[datetime] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v <= 0:
                raise ValueError("amount must be positive")
            return v.quantize(Decimal("0.00"))
        return v


class Transaction(TransactionBase):
    id: uuid.UUID
    account_id: uuid.UUID
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BankTransactionPreview(TransactionBase):
    account_id: uuid.UUID
    is_potential_duplicate: bool

    model_config = ConfigDict(from_attributes=True)
