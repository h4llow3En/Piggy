"""
Account models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-function-docstring,missing-class-docstring

import uuid
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from schwifty import IBAN

from piggy.models.database.account import AccountType


class AccountBase(BaseModel):
    name: str
    type: AccountType
    balance: Decimal = Decimal("0.00")
    iban: Optional[str] = None
    sort_order: int = 0

    @field_validator("iban")
    @classmethod
    def validate_iban(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.replace(" ", "").upper()
            try:
                IBAN(v)
            except ValueError as error:
                raise ValueError("invalid_iban") from error
        return v

    @model_validator(mode="after")
    def check_iban_required(self) -> "AccountBase":
        if self.type in [AccountType.GIRO, AccountType.SAVINGS] and not self.iban:
            raise ValueError("iban_required")
        return self


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    balance: Optional[Decimal] = None
    iban: Optional[str] = None
    sort_order: Optional[int] = None

    @field_validator("iban")
    @classmethod
    def validate_iban(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.replace(" ", "").upper()
            try:
                IBAN(v)
            except ValueError as error:
                raise ValueError("invalid_iban") from error
        return v


class Account(AccountBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class AccountSortUpdate(BaseModel):
    account_id: uuid.UUID
    sort_order: int


class AccountWithUser(Account):
    user_name: str
