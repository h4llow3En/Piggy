"""
v1 API routes for users.
"""

import secrets
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count
from starlette.responses import RedirectResponse

from piggy.core.auth import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    get_current_user,
    get_current_admin_user,
    verify_refresh_token,
)
from piggy.core.database import get_db
from piggy.core.i18n import _
from piggy.core.mail import (
    send_verification_email,
    admin_new_user_email,
    user_activated_email,
)
from piggy.models.database.user import User as UserDB, UserRole
from piggy.models.user import (
    Token,
    UserCreate,
    User,
    RefreshTokenRequest,
    UserPublic,
    UserUpdate,
    UserUpdateAdmin,
)

router = APIRouter()


# pylint: disable=duplicate-code
@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Authenticate user with email and password"""
    result = await db.execute(select(UserDB).where(UserDB.email == form_data.username))
    user = result.scalars().first()

    password_to_verify = form_data.password[:72]

    if not user or not verify_password(password_to_verify, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("errors.incorrect_credentials"),
            headers={"WWW-Authenticate": "Bearer"},
        )

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

    access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token"""

    user = await verify_refresh_token(refresh_data, db)

    access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=User)
async def register(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user."""
    result = await db.execute(select(UserDB).where(UserDB.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_("errors.user_already_exists"),
        )

    user_count_result = await db.execute(select(count()).select_from(UserDB))
    user_count = user_count_result.scalar()

    is_first_user = bool(user_count == 0)

    verification_token = secrets.token_urlsafe(32)

    user = UserDB(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        name=user_in.name,
        additional_config=user_in.additional_config,
        role=UserRole.ADMIN if is_first_user else UserRole.USER,
        is_active=is_first_user,
        email_verified=is_first_user,
        verification_token=None if is_first_user else verification_token,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    if not is_first_user:
        base_url = str(request.base_url)[:-1]
        success = await send_verification_email(
            user.name, user.email, base_url, verification_token
        )
        if not success:
            await db.delete(user)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_("errors.email_not_sent"),
            )

    return user


@router.get("/verify-email/{token}", include_in_schema=False)
async def verify_email(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Verify user email."""
    result = await db.execute(select(UserDB).where(UserDB.verification_token == token))
    user = result.scalars().first()
    if not user:
        return RedirectResponse(url="/login?verified=false&error=invalid_token")

    user.email_verified = True
    user.verification_token = None

    admin_result = await db.execute(select(UserDB).where(UserDB.role == UserRole.ADMIN))
    admin = admin_result.scalars().first()
    if admin:
        base_url = str(request.base_url)[:-1]
        await admin_new_user_email(admin.name, admin.email, user.email, base_url)

    await db.commit()
    return RedirectResponse(url=f"/login?verified=true&token={token}")


@router.get("/me", response_model=User)
async def read_user_me(current_user: UserDB = Depends(get_current_user)):
    """Retrieve the current user's information."""
    return current_user


@router.get(
    "/list", response_model=List[UserPublic], dependencies=[Depends(get_current_user)]
)
async def read_users_public(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a list of all active users (only ID and name).
    Accessible to all authenticated users.
    """
    result = await db.execute(select(UserDB).where(UserDB.is_active.is_(True)))
    return result.scalars().all()


@router.put("/me", response_model=User)
async def update_user_me(
    user_in: UserUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's information."""
    if user_in.email is not None:
        result = await db.execute(select(UserDB).where(UserDB.email == user_in.email))
        existing_user = result.scalars().first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_("errors.email_already_registered"),
            )
        current_user.email = user_in.email

    if user_in.name is not None:
        current_user.name = user_in.name

    if user_in.password is not None:
        current_user.hashed_password = get_password_hash(user_in.password)

    if user_in.additional_config is not None:
        current_user.additional_config = user_in.additional_config
    elif "additional_config" in user_in.model_dump(exclude_unset=True):
        current_user.additional_config = None

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_me(
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete the current user."""
    await db.delete(current_user)
    await db.commit()


@router.get(
    "/", response_model=List[User], dependencies=[Depends(get_current_admin_user)]
)
async def read_users(
    db: AsyncSession = Depends(get_db),
):
    """Returns all users."""
    result = await db.execute(select(UserDB).where(UserDB.email_verified.is_(True)))
    return result.scalars().all()


@router.put(
    "/{user_id}", response_model=User, dependencies=[Depends(get_current_admin_user)]
)
async def update_user_admin(
    user_id: uuid.UUID,
    user_in: UserUpdateAdmin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's information."""
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail=_("errors.user_not_found"))

    update_data = user_in.model_dump(exclude_unset=True)

    sending_activation_email = False
    if update_data.get("is_active") is True and not user.is_active:
        sending_activation_email = True

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    if sending_activation_email:
        base_url = str(request.base_url)[:-1]
        await user_activated_email(user.name, user.email, base_url)

    return user
