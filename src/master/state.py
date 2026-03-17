from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from src.protocol.models import TaskRequestPayload


@dataclass
class WorkerInfo:
    worker_id: str
    host: str
    port: int
    borrowed_from_uuid: Optional[str] = None


@dataclass
class MasterState:
    server_uuid: str
    threshold: int
    neighbor_masters: list[str]
    master_host: str = "127.0.0.1"
    master_port: int = 8000
    workers: list[WorkerInfo] = field(default_factory=list)
    _pending_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _pending_count: int = 0
    _task_queue: asyncio.Queue[tuple[str, TaskRequestPayload]] = field(default_factory=asyncio.Queue)
    _results: dict[str, str] = field(default_factory=dict)
    _consensus_in_progress: bool = False

    async def increment_pending(self) -> None:
        async with self._pending_lock:
            self._pending_count += 1

    async def decrement_pending(self) -> None:
        async with self._pending_lock:
            self._pending_count = max(0, self._pending_count - 1)

    async def get_pending_count(self) -> int:
        async with self._pending_lock:
            return self._pending_count

    def add_worker(self, worker_id: str, host: str, port: int, borrowed_from_uuid: Optional[str] = None) -> None:
        if any(w.worker_id == worker_id for w in self.workers):
            return
        self.workers.append(WorkerInfo(worker_id=worker_id, host=host, port=port, borrowed_from_uuid=borrowed_from_uuid))

    def remove_worker(self, worker_id: str) -> bool:
        for i, w in enumerate(self.workers):
            if w.worker_id == worker_id:
                self.workers.pop(i)
                return True
        return False

    def get_own_workers(self) -> list[WorkerInfo]:
        return [w for w in self.workers if w.borrowed_from_uuid is None]

    def get_workers_available_to_lend(self) -> list[WorkerInfo]:
        return [w for w in self.workers if w.borrowed_from_uuid is None]
