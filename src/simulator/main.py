from __future__ import annotations

import argparse
import asyncio
import sys

import httpx


async def run_simulator(master_url: str, rps: float, duration_seconds: int) -> None:
    url = f"{master_url.rstrip('/')}/tasks"
    interval = 1.0 / rps if rps > 0 else 1.0
    elapsed = 0.0
    count = 0
    async with httpx.AsyncClient(timeout=10.0) as client:
        while duration_seconds <= 0 or elapsed < duration_seconds:
            try:
                resp = await client.post(url, json={"type": "sleep", "seconds": 1})
                if resp.status_code == 200:
                    count += 1
            except Exception:
                pass
            await asyncio.sleep(interval)
            elapsed += interval
    print(f"Submitted {count} tasks in {elapsed:.1f}s", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-url", required=True, help="Base URL of the Master")
    parser.add_argument("--rps", type=float, default=5.0, help="Requests per second")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds (0 = infinite)")
    args = parser.parse_args()
    asyncio.run(run_simulator(args.master_url, args.rps, args.duration))


if __name__ == "__main__":
    main()
