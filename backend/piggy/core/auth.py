"""
Authentication module.

This module provides authentication functionality for the Piggy API application.
"""

import logging
from datetime import timedelta, datetime, timezone
from typing import Literal

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.core.config import config
from piggy.core.database import get_db
from piggy.core.i18n import _
from piggy.models.database.user import User, UserRole
from piggy.models.user import TokenData, RefreshTokenRequest

logger = logging.getLogger(__name__)

# OAuth2 scheme for extracting bearer token from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify if the plain password matches the hashed password."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError as error:
        logger.exception("Error verifying password: %s", error)
        return False


def get_password_hash(password: str) -> str:
    """Get the hashed password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict) -> str:
    """Create an access token for the given data with optional expiration."""
    return _create_token(
        data.copy(), timedelta(days=config.ACCESS_TOKEN_EXPIRE_MINUTES), "access"
    )


def create_refresh_token(data: dict) -> str:
    """Create a refresh token for the given data."""
    return _create_token(
        data.copy(), timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS), "refresh"
    )


def _create_token(
    data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh"]
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    data.update({"exp": expire, "type": token_type})
    return jwt.encode(data, config.SECRET_KEY, algorithm=config.ALGORITHM)


async def verify_refresh_token(
    refresh_data: RefreshTokenRequest, db: AsyncSession
) -> User:
    """Verify if the refresh token is valid."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=_("errors.could_not_validate_credentials"),
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            refresh_data.refresh_token,
            config.SECRET_KEY,
            algorithms=[config.ALGORITHM],
        )
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "refresh":
            raise credentials_exception
    except JWTError as error:
        raise credentials_exception from error

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


# pylint: disable=duplicate-code
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Resolve and validate the current authenticated user from the bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=_("errors.could_not_validate_credentials"),
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as error:
        raise credentials_exception from error

    result = await db.execute(select(User).where(User.email == token_data.email))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("errors.inactive_user"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("errors.email_not_verified"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Resolve and validate the current authenticated admin user."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("errors.insufficient_privileges"),
        )
    return current_user
