#!/bin/sh

DB_WAIT_MAX_ATTEMPTS="${DB_WAIT_MAX_ATTEMPTS:-30}"
DB_WAIT_SECONDS="${DB_WAIT_SECONDS:-2}"

echo "[entrypoint] Waiting for database connection..."
python - <<'PY'
import os, sys, time
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
        print(f"[entrypoint] DB not ready ({attempt}/{max_attempts}): {exc}")
        time.sleep(wait_seconds)

print("[entrypoint] Database wait timeout.")
sys.exit(1)
PY

echo "[entrypoint] Diagnosing database state..."
python - <<'PY'
import sys
from sqlalchemy import create_engine, text, inspect as sa_inspect
from config import get_database_url

url = get_database_url()
print(f"[entrypoint] DB URL scheme: {url.split('://')[0]}")
engine = create_engine(url)
inspector = sa_inspect(engine)
tables = inspector.get_table_names()
print(f"[entrypoint] Existing tables: {tables}")

if 'alembic_version' in tables:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        versions = [r[0] for r in rows]
        print(f"[entrypoint] alembic_version records: {versions}")
else:
    print("[entrypoint] alembic_version table does NOT exist.")

if 'domains' in tables:
    cols = {c['name'] for c in inspector.get_columns('domains')}
    print(f"[entrypoint] domains columns: {sorted(cols)}")
PY

echo "[entrypoint] Checking current migration state..."
flask db current 2>&1 || true

echo "[entrypoint] Running database migrations..."
if flask db upgrade 2>&1; then
  echo "[entrypoint] Migration completed successfully."
else
  EXITCODE=$?
  echo "[entrypoint] ERROR: flask db upgrade failed with exit code $EXITCODE"
  echo "[entrypoint] Trying verbose migration for diagnostics..."
  flask db upgrade --sql 2>&1 || true
  echo "[entrypoint] Aborting due to migration failure."
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