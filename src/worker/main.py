from __future__ import annotations

import argparse
import uuid

import httpx
import uvicorn

from src.worker.app import create_app
from src.worker.state import WorkerState


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-url", required=True, help="Base URL of the Master (e.g. http://localhost:8000)")
    parser.add_argument("--port", type=int, default=8001, help="Port for this Worker")
    parser.add_argument("--host", default="127.0.0.1", help="Host for this Worker (for Master to reach it)")
    parser.add_argument("--worker-id", default=None, help="Worker ID (default: generated UUID)")
    args = parser.parse_args()

    master_url = args.master_url.rstrip("/")
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{master_url}/info")
            resp.raise_for_status()
            data = resp.json()
            server_uuid = data["SERVER_UUID"]
    except Exception as e:
        raise SystemExit(f"Could not get Master info from {master_url}: {e}") from e

    worker_id = args.worker_id or str(uuid.uuid4())
    state = WorkerState(
        master_base_url=master_url,
        server_uuid=server_uuid,
        worker_id=worker_id,
        host=args.host,
        port=args.port,
    )
    app = create_app(state)
    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
