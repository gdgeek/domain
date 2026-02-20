#!/bin/sh
set -eu

DB_WAIT_MAX_ATTEMPTS="${DB_WAIT_MAX_ATTEMPTS:-30}"
DB_WAIT_SECONDS="${DB_WAIT_SECONDS:-2}"

echo "[entrypoint] Waiting for database connection..."
python - <<'PY'
import os
import sys
import time

from sqlalchemy import create_engine, text

from config import get_database_url

url = get_database_url()
if url.startswith("sqlite"):
    print("[entrypoint] SQLite detected, skip DB wait.")
    sys.exit(0)

max_attempts = int(os.getenv("DB_WAIT_MAX_ATTEMPTS", "30"))
wait_seconds = int(os.getenv("DB_WAIT_SECONDS", "2"))

for attempt in range(1, max_attempts + 1):
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[entrypoint] Database is ready (attempt {attempt}).")
        sys.exit(0)
    except Exception as exc:
        print(f"[entrypoint] Database not ready (attempt {attempt}/{max_attempts}): {exc}")
        time.sleep(wait_seconds)

print("[entrypoint] Database wait timeout.")
sys.exit(1)
PY

echo "[entrypoint] Running database migrations..."
if ! flask db upgrade >/tmp/migrate.log 2>&1; then
  echo "[entrypoint] Migration failed:"
  cat /tmp/migrate.log
  exit 1
fi

if [ -n "${START_COMMAND:-}" ]; then
  echo "[entrypoint] Starting custom command..."
  exec sh -c "$START_COMMAND"
fi

if [ "${FLASK_ENV:-production}" = "development" ]; then
  echo "[entrypoint] Starting Flask development server..."
  exec flask run --host=0.0.0.0 --reload
fi

echo "[entrypoint] Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --access-logfile - run:app