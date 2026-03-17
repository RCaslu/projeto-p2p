import pytest
from httpx import ASGITransport, AsyncClient

from src.master.app import app as master_app


@pytest.mark.asyncio
async def test_info() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=master_app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "SERVER_UUID" in data
        assert len(data["SERVER_UUID"]) > 0


@pytest.mark.asyncio
async def test_heartbeat() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=master_app),
        base_url="http://test",
    ) as client:
        info_resp = await client.get("/info")
        server_uuid = info_resp.json()["SERVER_UUID"]
        resp = await client.post(
            "/heartbeat",
            json={"SERVER_UUID": server_uuid, "TASK": "HEARTBEAT"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["TASK"] == "HEARTBEAT"
        assert data["RESPONSE"] == "ALIVE"


@pytest.mark.asyncio
async def test_register_worker() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=master_app),
        base_url="http://test",
    ) as client:
        info_resp = await client.get("/info")
        server_uuid = info_resp.json()["SERVER_UUID"]
        resp = await client.post(
            "/workers/register",
            json={
                "SERVER_UUID": server_uuid,
                "TASK": "REGISTER",
                "WORKER_ID": "test-worker-1",
                "HOST": "127.0.0.1",
                "PORT": 9000,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["RESPONSE"] == "OK"
        assert data["WORKER_ID"] == "test-worker-1"


@pytest.mark.asyncio
async def test_submit_task() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=master_app),
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/tasks",
            json={"type": "sleep", "seconds": 0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data


@pytest.mark.asyncio
async def test_metrics() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=master_app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "pending_count" in data
        assert "threshold" in data
        assert "workers_count" in data
        assert "worker_ids" in data


@pytest.mark.asyncio
async def test_help_request_returns_offer() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=master_app),
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/help/request",
            json={
                "SERVER_UUID": "other-master",
                "TASK": "HELP_REQUEST",
                "PENDING_COUNT": 20,
                "THRESHOLD": 10,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["TASK"] == "HELP_OFFER"
        assert "OFFER_COUNT" in data
        assert "WORKER_IDS" in data
