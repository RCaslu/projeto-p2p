from __future__ import annotations

import json
from typing import Literal, Optional

from pydantic import BaseModel, Field


class HeartbeatRequest(BaseModel):
    SERVER_UUID: str
    TASK: Literal["HEARTBEAT"] = "HEARTBEAT"


class HeartbeatResponse(BaseModel):
    SERVER_UUID: str
    TASK: Literal["HEARTBEAT"] = "HEARTBEAT"
    RESPONSE: Literal["ALIVE"] = "ALIVE"


class RegisterRequest(BaseModel):
    SERVER_UUID: str
    TASK: Literal["REGISTER"] = "REGISTER"
    WORKER_ID: str
    HOST: str
    PORT: int


class RegisterResponse(BaseModel):
    SERVER_UUID: str
    TASK: Literal["REGISTER"] = "REGISTER"
    RESPONSE: Literal["OK"] = "OK"
    WORKER_ID: str


class TaskRequestPayload(BaseModel):
    type: Literal["sleep", "compute"] = "sleep"
    seconds: Optional[int] = None
    expression: Optional[str] = None


class TaskRequest(BaseModel):
    SERVER_UUID: str
    TASK: Literal["TASK_REQUEST"] = "TASK_REQUEST"
    TASK_ID: str
    PAYLOAD: TaskRequestPayload


class TaskResult(BaseModel):
    SERVER_UUID: str
    TASK: Literal["TASK_RESULT"] = "TASK_RESULT"
    TASK_ID: str
    RESULT: str


class RedirectCommand(BaseModel):
    SERVER_UUID: str
    TASK: Literal["REDIRECT"] = "REDIRECT"
    TARGET_MASTER_HOST: str
    TARGET_MASTER_PORT: int
    TARGET_MASTER_UUID: str


class HelpRequest(BaseModel):
    SERVER_UUID: str
    TASK: Literal["HELP_REQUEST"] = "HELP_REQUEST"
    PENDING_COUNT: int
    THRESHOLD: int


class HelpOffer(BaseModel):
    SERVER_UUID: str
    TASK: Literal["HELP_OFFER"] = "HELP_OFFER"
    AVAILABLE_WORKERS: int
    OFFER_COUNT: int
    WORKER_IDS: list[str] = Field(default_factory=list)


class HelpAccept(BaseModel):
    SERVER_UUID: str
    TASK: Literal["HELP_ACCEPT"] = "HELP_ACCEPT"
    REQUESTER_UUID: str
    REQUESTER_HOST: str = ""
    REQUESTER_PORT: int = 0
    ACCEPTED_COUNT: int
    WORKER_IDS: list[str] = Field(default_factory=list)


class WorkerReturn(BaseModel):
    SERVER_UUID: str
    TASK: Literal["WORKER_RETURN"] = "WORKER_RETURN"
    WORKER_ID: str
    ORIGINAL_MASTER_UUID: str


def serialize_message(obj: BaseModel) -> str:
    return obj.model_dump_json() + "\n"


def parse_message(line: str) -> dict[str, object]:
    return json.loads(line.strip())
