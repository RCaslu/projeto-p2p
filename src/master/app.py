from __future__ import annotations

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Union

import httpx
from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel

from src.protocol import (
    HeartbeatRequest,
    HeartbeatResponse,
    RegisterRequest,
    RegisterResponse,
)
from src.protocol.models import (
    HelpAccept,
    HelpOffer,
    HelpRequest,
    RedirectCommand,
    TaskRequest,
    TaskRequestPayload,
)
from src.master.state import MasterState, WorkerInfo

_MASTER_STATE: Optional[MasterState] = None


def get_state(request: Request) -> MasterState:
    return request.app.state.master_state


async def try_consensus_request_help(state: MasterState) -> None:
    state._consensus_in_progress = True
    try:
        if not state.neighbor_masters:
            return
        pending = await state.get_pending_count()
        if pending <= state.threshold:
            return
        help_req = HelpRequest(
            SERVER_UUID=state.server_uuid,
            TASK="HELP_REQUEST",
            PENDING_COUNT=pending,
            THRESHOLD=state.threshold,
        )
        best_offer: Optional[tuple[str, HelpOffer]] = None
        async with httpx.AsyncClient(timeout=10.0) as client:
            for neighbor_url in state.neighbor_masters:
                try:
                    resp = await client.post(
                        f"{neighbor_url.rstrip('/')}/help/request",
                        json=help_req.model_dump(),
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        offer = HelpOffer(
                            SERVER_UUID=data["SERVER_UUID"],
                            TASK=data["TASK"],
                            AVAILABLE_WORKERS=data["AVAILABLE_WORKERS"],
                            OFFER_COUNT=data["OFFER_COUNT"],
                            WORKER_IDS=data.get("WORKER_IDS", []),
                        )
                        if offer.OFFER_COUNT > 0 and (best_offer is None or offer.OFFER_COUNT > best_offer[1].OFFER_COUNT):
                            best_offer = (neighbor_url, offer)
                except Exception:
                    continue
        if best_offer is None:
            return
        neighbor_url, offer = best_offer
        accept_count = min(offer.OFFER_COUNT, len(offer.WORKER_IDS) if offer.WORKER_IDS else offer.OFFER_COUNT)
        worker_ids = offer.WORKER_IDS[:accept_count] if offer.WORKER_IDS else []
        help_accept = HelpAccept(
            SERVER_UUID=state.server_uuid,
            TASK="HELP_ACCEPT",
            REQUESTER_UUID=state.server_uuid,
            REQUESTER_HOST=state.master_host,
            REQUESTER_PORT=state.master_port,
            ACCEPTED_COUNT=accept_count,
            WORKER_IDS=worker_ids,
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{neighbor_url.rstrip('/')}/help/accept",
                json=help_accept.model_dump(),
            )
    finally:
        state._consensus_in_progress = False


def load_config() -> MasterState:
    server_uuid = os.environ.get("SERVER_UUID") or str(uuid.uuid4())
    threshold = int(os.environ.get("THRESHOLD", "10"))
    neighbors_str = os.environ.get("NEIGHBOR_MASTERS", "")
    neighbor_masters = [u.strip() for u in neighbors_str.split(",") if u.strip()]
    master_host = os.environ.get("MASTER_HOST", "127.0.0.1")
    master_port = int(os.environ.get("MASTER_PORT", "8000"))
    return MasterState(
        server_uuid=server_uuid,
        threshold=threshold,
        neighbor_masters=neighbor_masters,
        master_host=master_host,
        master_port=master_port,
    )


async def distributor_loop(state: MasterState) -> None:
    idx = 0
    while True:
        try:
            task_id, payload = await state._task_queue.get()
            workers = state.workers
            if not workers:
                await state._task_queue.put((task_id, payload))
                await asyncio.sleep(0.5)
                continue
            worker = workers[idx % len(workers)]
            idx += 1
            url = f"http://{worker.host}:{worker.port}/execute"
            task_req = TaskRequest(
                SERVER_UUID=state.server_uuid,
                TASK="TASK_REQUEST",
                TASK_ID=task_id,
                PAYLOAD=payload,
            )
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=task_req.model_dump())
                    if resp.status_code == 200:
                        data = resp.json()
                        state._results[task_id] = data.get("RESULT", "")
                    else:
                        await state._task_queue.put((task_id, payload))
                        await asyncio.sleep(0.2)
                        continue
            except Exception:
                await state._task_queue.put((task_id, payload))
                await asyncio.sleep(0.5)
                continue
            await state.decrement_pending()
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(0.5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _MASTER_STATE
    state = app.state.master_state
    _MASTER_STATE = state
    task = asyncio.create_task(distributor_loop(state))
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    _MASTER_STATE = None


class TaskSubmitBody(BaseModel):
    type: str = "sleep"
    seconds: Optional[int] = 1
    expression: Optional[str] = None


_state = load_config()
app = FastAPI(title="P2P Master", lifespan=lifespan)
app.state.master_state = _state


@app.get("/info")
async def info(state: MasterState = Depends(get_state)) -> dict[str, str]:
    return {"SERVER_UUID": state.server_uuid}


@app.post("/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(body: HeartbeatRequest, state: MasterState = Depends(get_state)) -> HeartbeatResponse:
    return HeartbeatResponse(SERVER_UUID=state.server_uuid, TASK="HEARTBEAT", RESPONSE="ALIVE")


@app.post("/workers/register", response_model=RegisterResponse)
async def register_worker(body: RegisterRequest, state: MasterState = Depends(get_state)) -> RegisterResponse:
    state.add_worker(body.WORKER_ID, body.HOST, body.PORT, borrowed_from_uuid=None)
    return RegisterResponse(
        SERVER_UUID=state.server_uuid,
        TASK="REGISTER",
        RESPONSE="OK",
        WORKER_ID=body.WORKER_ID,
    )


@app.post("/tasks")
async def submit_task(body: TaskSubmitBody, state: MasterState = Depends(get_state)) -> dict[str, str]:
    task_id = str(uuid.uuid4())
    payload = TaskRequestPayload(
        type="sleep" if body.type == "sleep" else "compute",
        seconds=body.seconds,
        expression=body.expression,
    )
    state._task_queue.put_nowait((task_id, payload))
    await state.increment_pending()
    pending = await state.get_pending_count()
    if pending > state.threshold and not state._consensus_in_progress:
        asyncio.create_task(try_consensus_request_help(state))
    return {"task_id": task_id}


@app.post("/help/request", response_model=HelpOffer)
async def help_request(body: HelpRequest, state: MasterState = Depends(get_state)) -> HelpOffer:
    available = state.get_workers_available_to_lend()
    worker_ids = [w.worker_id for w in available]
    return HelpOffer(
        SERVER_UUID=state.server_uuid,
        TASK="HELP_OFFER",
        AVAILABLE_WORKERS=len(available),
        OFFER_COUNT=len(available),
        WORKER_IDS=worker_ids,
    )


@app.post("/help/accept")
async def help_accept(body: HelpAccept, state: MasterState = Depends(get_state)) -> dict[str, str]:
    for worker_id in body.WORKER_IDS:
        worker = next((w for w in state.workers if w.worker_id == worker_id), None)
        if worker is None:
            continue
        redirect_cmd = RedirectCommand(
            SERVER_UUID=state.server_uuid,
            TASK="REDIRECT",
            TARGET_MASTER_HOST=body.REQUESTER_HOST or "127.0.0.1",
            TARGET_MASTER_PORT=body.REQUESTER_PORT or 8000,
            TARGET_MASTER_UUID=body.REQUESTER_UUID,
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"http://{worker.host}:{worker.port}/redirect",
                    json=redirect_cmd.model_dump(),
                )
        except Exception:
            pass
        state.remove_worker(worker_id)
    return {"status": "ok"}


@app.get("/metrics")
async def metrics(state: MasterState = Depends(get_state)) -> Dict[str, Union[int, List[str]]]:
    pending = await state.get_pending_count()
    return {
        "pending_count": pending,
        "threshold": state.threshold,
        "workers_count": len(state.workers),
        "worker_ids": [w.worker_id for w in state.workers],
    }
