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
    TaskRequest,
    TaskRequestPayload,
)


def test_heartbeat_request_serialization() -> None:
    req = HeartbeatRequest(SERVER_UUID="uuid-1")
    assert req.TASK == "HEARTBEAT"
    d = req.model_dump()
    assert d["SERVER_UUID"] == "uuid-1"
    assert d["TASK"] == "HEARTBEAT"


def test_heartbeat_response_serialization() -> None:
    resp = HeartbeatResponse(SERVER_UUID="uuid-1", RESPONSE="ALIVE")
    assert resp.RESPONSE == "ALIVE"
    d = resp.model_dump()
    assert d["TASK"] == "HEARTBEAT"
    assert d["RESPONSE"] == "ALIVE"


def test_register_request_serialization() -> None:
    req = RegisterRequest(
        SERVER_UUID="uuid-1",
        WORKER_ID="w1",
        HOST="127.0.0.1",
        PORT=8001,
    )
    d = req.model_dump()
    assert d["WORKER_ID"] == "w1"
    assert d["PORT"] == 8001


def test_help_request_serialization() -> None:
    req = HelpRequest(
        SERVER_UUID="uuid-1",
        PENDING_COUNT=15,
        THRESHOLD=10,
    )
    d = req.model_dump()
    assert d["PENDING_COUNT"] == 15
    assert d["THRESHOLD"] == 10


def test_help_offer_serialization() -> None:
    offer = HelpOffer(
        SERVER_UUID="uuid-2",
        AVAILABLE_WORKERS=2,
        OFFER_COUNT=2,
        WORKER_IDS=["w1", "w2"],
    )
    d = offer.model_dump()
    assert d["OFFER_COUNT"] == 2
    assert d["WORKER_IDS"] == ["w1", "w2"]


def test_help_accept_serialization() -> None:
    accept = HelpAccept(
        SERVER_UUID="uuid-1",
        REQUESTER_UUID="uuid-1",
        REQUESTER_HOST="127.0.0.1",
        REQUESTER_PORT=8000,
        ACCEPTED_COUNT=1,
        WORKER_IDS=["w1"],
    )
    d = accept.model_dump()
    assert d["REQUESTER_HOST"] == "127.0.0.1"
    assert d["WORKER_IDS"] == ["w1"]


def test_task_request_payload_sleep() -> None:
    payload = TaskRequestPayload(type="sleep", seconds=2)
    assert payload.type == "sleep"
    assert payload.seconds == 2


def test_task_request_payload_compute() -> None:
    payload = TaskRequestPayload(type="compute", expression="1+1")
    assert payload.type == "compute"
    assert payload.expression == "1+1"
