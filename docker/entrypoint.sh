#!/bin/sh
set -eu

python - <<'PY'
import os
import socket
import time

host = os.getenv("POSTGRES_HOST")
port = int(os.getenv("POSTGRES_PORT", "5432"))

if os.getenv("DB_ENGINE", "sqlite").lower() != "postgresql" or not host:
    raise SystemExit(0)

for attempt in range(30):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("PostgreSQL доступен.")
            break
    except OSError:
        if attempt == 29:
            raise
        print("Ожидание PostgreSQL...")
        time.sleep(1)
PY

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    python manage.py migrate --noinput
fi

if [ "${COLLECT_STATIC:-1}" = "1" ]; then
    python manage.py collectstatic --noinput
fi

if [ "${CREATE_TEST_DATA:-0}" = "1" ]; then
    python manage.py ccu \
        --min-count "${CCU_MIN_COUNT:-20}" \
        --max-count "${CCU_MAX_COUNT:-50}"
fi

exec "$@"
