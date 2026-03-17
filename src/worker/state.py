from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorkerState:
    master_base_url: str
    server_uuid: str
    worker_id: str
    host: str
    port: int
    running: bool = True
