from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI

from src.protocol import (
    HeartbeatRequest,
    RedirectCommand,
    RegisterRequest,
    TaskRequest,
    TaskResult,
)
from src.protocol.models import TaskRequestPayload
from src.worker.state import WorkerState

WORKER_STATE: Optional[WorkerState] = None


def get_state() -> WorkerState:
    if WORKER_STATE is None:
        raise RuntimeError("WorkerState not initialized")
    return WORKER_STATE


async def heartbeat_loop(state: WorkerState) -> None:
    while state.running:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{state.master_base_url.rstrip('/')}/heartbeat",
                    json=HeartbeatRequest(SERVER_UUID=state.server_uuid).model_dump(),
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("RESPONSE") == "ALIVE":
                        pass
        except Exception:
            pass
        await asyncio.sleep(2.0)


async def register_with_master(state: WorkerState) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{state.master_base_url.rstrip('/')}/workers/register",
                json=RegisterRequest(
                    SERVER_UUID=state.server_uuid,
                    TASK="REGISTER",
                    WORKER_ID=state.worker_id,
                    HOST=state.host,
                    PORT=state.port,
                ).model_dump(),
            )
            if resp.status_code == 200:
                return True
    except Exception:
        pass
    return False


def execute_payload(payload: TaskRequestPayload) -> str:
    if payload.type == "sleep":
        import time
        secs = payload.seconds or 1
        time.sleep(min(secs, 10))
        return f"slept_{secs}s"
    if payload.type == "compute":
        try:
            result = eval(payload.expression or "0")
            return str(result)
        except Exception as e:
            return f"error:{e!s}"
    return "unknown_task_type"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global WORKER_STATE
    state = app.state.worker_state
    WORKER_STATE = state
    await register_with_master(state)
    task = asyncio.create_task(heartbeat_loop(state))
    try:
        yield
    finally:
        state.running = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    WORKER_STATE = None


def create_app(worker_state: WorkerState) -> FastAPI:
    app = FastAPI(title="P2P Worker", lifespan=lifespan)
    app.state.worker_state = worker_state

    @app.post("/execute", response_model=TaskResult)
    async def execute(task_req: TaskRequest):
        state = get_state()
        result = execute_payload(task_req.PAYLOAD)
        return TaskResult(
            SERVER_UUID=state.server_uuid,
            TASK="TASK_RESULT",
            TASK_ID=task_req.TASK_ID,
            RESULT=result,
        )

    @app.post("/redirect")
    async def redirect(cmd: RedirectCommand):
        state = get_state()
        new_base = f"http://{cmd.TARGET_MASTER_HOST}:{cmd.TARGET_MASTER_PORT}"
        state.master_base_url = new_base
        state.server_uuid = cmd.TARGET_MASTER_UUID
        await register_with_master(state)
        return {"status": "ok"}

    return app
