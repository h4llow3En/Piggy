"""
RecurringPayment models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-function-docstring,missing-class-docstring,duplicate-code

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from piggy.models.database.recurring_payment import RecurringInterval
from piggy.models.database.transaction import TransactionType


class RecurringPaymentBase(BaseModel):
    name: str
    amount: Decimal
    type: TransactionType = TransactionType.EXPENSE
    account_id: Optional[uuid.UUID] = None
    target_account_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    interval: RecurringInterval = RecurringInterval.MONTHLY
    interval_x_days: Optional[int] = None
    start_date: date
    is_subscription: bool = False

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v.quantize(Decimal("0.00"))


class RecurringPaymentCreate(RecurringPaymentBase):
    pass


class RecurringPaymentUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[Decimal] = None
    type: Optional[TransactionType] = None
    account_id: Optional[uuid.UUID] = None
    target_account_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    interval: Optional[RecurringInterval] = None
    interval_x_days: Optional[int] = None
    start_date: Optional[date] = None
    is_subscription: Optional[bool] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v <= 0:
                raise ValueError("amount must be positive")
            return v.quantize(Decimal("0.00"))
        return v


class RecurringPayment(RecurringPaymentBase):
    id: uuid.UUID
    user_id: uuid.UUID
    last_generated_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionCandidateResponse(BaseModel):
    name: str
    amount: Decimal
    interval: RecurringInterval
    count: int
    last_date: datetime
