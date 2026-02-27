"""
Bank sync endpoints for FinTS connections.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.core.auth import get_current_user
from piggy.core.bank_sync import preview_connection
from piggy.core.bank_sync_cache import sync_task_cache
from piggy.core.database import get_db, async_session
from piggy.core.i18n import _
from piggy.models.bank import (
    BankConnectionCreate,
    BankConnection as BankConnectionModel,
    BankProvider,
    SyncRequest,
    SyncTaskResponse,
    SyncTaskStatus,
    SyncTaskStatusResponse,
)
from piggy.models.database.bank_connection import BankConnection as BankConnectionDB
from piggy.models.database.user import User as UserDB

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post(
    "/", response_model=BankConnectionModel, status_code=status.HTTP_201_CREATED
)
async def create_bank_connection(
    payload: BankConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Create a new bank connection for the current user.
    """
    bank_code = None
    server = None
    bank_name = None

    if payload.provider == BankProvider.DKB:
        bank_code = "12030000"
        server = "https://fints.dkb.de/fints"
        bank_name = "DKB"

    if not bank_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {payload.provider}",
        )

    # Deduplicate by (user, bank_code, login)
    exists_q = await db.execute(
        select(BankConnectionDB.id).where(
            and_(
                BankConnectionDB.user_id == current_user.id,
                BankConnectionDB.bank_code == bank_code,
                BankConnectionDB.login == payload.login,
            )
        )
    )
    if exists_q.scalar() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=_("errors.already_exists")
        )

    obj = BankConnectionDB(
        user_id=current_user.id,
        bank_code=bank_code,
        login=payload.login,
        bank_name=bank_name,
        server=server,
        status="ready",
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/", response_model=list[BankConnectionModel])
async def list_bank_connections(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    List all bank connections for the current user.
    """
    rows = await db.execute(
        select(BankConnectionDB).where(BankConnectionDB.user_id == current_user.id)
    )
    return list(rows.scalars().all())


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Delete a bank connection for the current user.
    """
    obj = await db.get(BankConnectionDB, connection_id)
    if not obj or obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_("errors.not_found")
        )
    await db.delete(obj)
    await db.commit()


@router.post("/{connection_id}/sync", response_model=SyncTaskResponse)
async def sync(
    connection_id: uuid.UUID,
    req: SyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Sync transactions for a bank connection in the background.
    """
    obj = await db.get(BankConnectionDB, connection_id)
    if not obj or obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_("errors.not_found")
        )

    task_id = uuid.uuid4()
    sync_task_cache.create_task(task_id)

    background_tasks.add_task(run_sync_task, task_id, obj.id, req.pin, req.since)

    return SyncTaskResponse(task_id=task_id, status=SyncTaskStatus.PENDING)


@router.get(
    "/sync/status/{task_id}",
    response_model=SyncTaskStatusResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_sync_status(
    task_id: uuid.UUID,
):
    """
    Get the status and results of a bank sync task.
    """
    task = sync_task_cache.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_("errors.not_found")
        )

    return SyncTaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        result=task.result,
        error=task.error,
    )


async def run_sync_task(
    task_id: uuid.UUID, connection_id: uuid.UUID, pin: str, since: Any
):
    """
    Background task to run the bank sync and update the cache.
    """
    sync_task_cache.update_task(task_id, SyncTaskStatus.RUNNING)
    try:
        async with async_session() as db:
            result = await preview_connection(
                connection_id, pin=pin, since=since, db=db, task_id=task_id
            )
            # If we are in AWAITING_AUTHENTICATION, preview_connection already updated the status
            # but we only update COMPLETED if it's not in that state.
            task = sync_task_cache.get_task(task_id)
            if task and task.status != SyncTaskStatus.AWAITING_AUTHENTICATION:
                sync_task_cache.update_task(
                    task_id, SyncTaskStatus.COMPLETED, result=result
                )
    except Exception as e:  # pylint: disable=broad-exception-caught

        logging.getLogger(__name__).exception("Bank sync task failed")
        sync_task_cache.update_task(task_id, SyncTaskStatus.FAILED, error=str(e))
