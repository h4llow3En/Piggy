"""
User models for Piggy application.
"""

# pylint: disable=too-few-public-methods,missing-function-docstring,missing-class-docstring

import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from piggy.models.database.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    name: str
    additional_config: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    additional_config: Optional[str] = None


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
