"""
Pydantic models for BankConnection entities.
"""

# pylint: disable=too-few-public-methods,missing-class-docstring

import uuid
from datetime import datetime, date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict

from piggy.models.transaction import BankTransactionPreview


class BankProvider(str, Enum):
    DKB = "DKB"


class SyncTaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    AWAITING_AUTHENTICATION = "AWAITING_AUTHENTICATION"


class BankConnectionBase(BaseModel):
    bank_code: str
    login: str
    customer_id: Optional[str] = None
    bank_name: Optional[str] = None
    server: Optional[str] = None


class BankConnectionCreate(BaseModel):
    provider: BankProvider
    login: str


class SyncRequest(BaseModel):
    pin: str
    since: date


class SyncTaskResponse(BaseModel):
    task_id: uuid.UUID
    status: SyncTaskStatus


class SyncTaskStatusResponse(BaseModel):
    task_id: uuid.UUID
    status: SyncTaskStatus
    result: Optional[list["BankTransactionPreview"]] = None
    error: Optional[str] = None


SyncTaskStatusResponse.model_rebuild()


class BankConnection(BankConnectionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    consent_valid_until: Optional[date] = None
    last_sync_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
