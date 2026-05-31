#!/bin/sh
set -eu

python - <<'PY'
import os
import socket
import time


def wait_for(host: str, port: int, label: str) -> None:
    for _ in range(60):
        try:
            with socket.create_connection((host, port), timeout=2):
                return
        except OSError:
            time.sleep(2)
    raise SystemExit(f"{label} did not become available")


wait_for(os.environ.get("DB_HOST", "db"), int(os.environ.get("DB_PORT", "5432")), "database")
wait_for(os.environ.get("REDIS_HOST", "redis"), int(os.environ.get("REDIS_PORT", "6379")), "redis")
PY

exec "$@"
