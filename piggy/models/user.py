"""
User models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-function-docstring,missing-class-docstring

import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

from piggy.models.database.user import UserRole

# bcrypt refuses anything longer and would raise on hashing. Rejecting is
# preferable to silently truncating, which would make two different long
# passwords interchangeable.
MAX_PASSWORD_BYTES = 72


def _validate_password_length(value: Optional[str]) -> Optional[str]:
    if value is not None and len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"password must not be longer than {MAX_PASSWORD_BYTES} bytes"
        )
    return value


class UserBase(BaseModel):
    email: EmailStr
    name: str
    additional_config: Optional[str] = None


class UserCreate(UserBase):
    password: str

    _check_password = field_validator("password")(_validate_password_length)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    additional_config: Optional[str] = None

    _check_password = field_validator("password")(_validate_password_length)


class UserUpdateAdmin(UserUpdate):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: uuid.UUID
    is_active: bool
    email_verified: bool
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    id: uuid.UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    email: Optional[str] = None
