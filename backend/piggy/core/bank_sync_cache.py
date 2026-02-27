"""
Cache for bank synchronization tasks.
"""

import time
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from piggy.models.bank import SyncTaskStatus

# pylint: disable=missing-class-docstring,missing-function-docstring


@dataclass
class CachedSyncTask:
    task_id: uuid.UUID
    status: SyncTaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    expires_at: float = field(default_factory=lambda: time.time() + 1800)  # 30 minutes


class SyncTaskCache:
    def __init__(self):
        self._tasks: Dict[uuid.UUID, CachedSyncTask] = {}

    def create_task(self, task_id: uuid.UUID) -> CachedSyncTask:
        task = CachedSyncTask(task_id=task_id, status=SyncTaskStatus.PENDING)
        self._tasks[task_id] = task
        self._cleanup()
        return task

    def update_task(
        self,
        task_id: uuid.UUID,
        status: SyncTaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ):
        if task_id in self._tasks:
            self._tasks[task_id].status = status
            if result is not None:
                self._tasks[task_id].result = result
            if error is not None:
                self._tasks[task_id].error = error
        self._cleanup()

    def get_task(self, task_id: uuid.UUID) -> Optional[CachedSyncTask]:
        self._cleanup()
        return self._tasks.get(task_id)

    def _cleanup(self):
        now = time.time()
        expired_ids = [
            tid for tid, task in self._tasks.items() if task.expires_at < now
        ]
        for tid in expired_ids:
            del self._tasks[tid]


sync_task_cache = SyncTaskCache()
