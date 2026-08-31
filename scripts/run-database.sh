#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PG_BASE_DIR="$ROOT_DIR/.local/postgres"
PG_DATA_DIR="$PG_BASE_DIR/data"
PG_LOG_FILE="$PG_BASE_DIR/postgres.log"
PG_PORT="55432"
PG_USER="facemark"
PG_DB="facemark_demo"

PG_BIN_DIR="/usr/lib/postgresql/16/bin"
INITDB_BIN="$PG_BIN_DIR/initdb"
PG_CTL_BIN="$PG_BIN_DIR/pg_ctl"
PSQL_BIN="$PG_BIN_DIR/psql"
CREATEDB_BIN="$PG_BIN_DIR/createdb"
PG_ISREADY_BIN="$PG_BIN_DIR/pg_isready"

if [ ! -x "$INITDB_BIN" ] || [ ! -x "$PG_CTL_BIN" ] || [ ! -x "$PSQL_BIN" ]; then
  echo "PostgreSQL server binaries were not found at $PG_BIN_DIR."
  echo "Install postgresql server packages and retry."
  exit 1
fi

mkdir -p "$PG_BASE_DIR"

if [ ! -f "$PG_DATA_DIR/PG_VERSION" ]; then
  "$INITDB_BIN" -D "$PG_DATA_DIR" -U "$PG_USER" --auth=trust >/dev/null
fi

if ! "$PG_CTL_BIN" -D "$PG_DATA_DIR" status >/dev/null 2>&1; then
  "$PG_CTL_BIN" -D "$PG_DATA_DIR" -l "$PG_LOG_FILE" -o "-p $PG_PORT -h 127.0.0.1" start >/dev/null
fi

for _ in 1 2 3 4 5 6 7 8 9 10; do
  if "$PG_ISREADY_BIN" -h 127.0.0.1 -p "$PG_PORT" -U "$PG_USER" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

DB_EXISTS="$("$PSQL_BIN" -h 127.0.0.1 -p "$PG_PORT" -U "$PG_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$PG_DB'")"
if [ "$DB_EXISTS" != "1" ]; then
  "$CREATEDB_BIN" -h 127.0.0.1 -p "$PG_PORT" -U "$PG_USER" "$PG_DB"
fi

echo "PostgreSQL is running on 127.0.0.1:$PG_PORT"
echo "DATABASE_URL=postgresql+psycopg2://$PG_USER:facemark123@127.0.0.1:$PG_PORT/$PG_DB"
echo "Press Ctrl+C to stop the local PostgreSQL server."

cleanup() {
  "$PG_CTL_BIN" -D "$PG_DATA_DIR" stop -m fast >/dev/null 2>&1 || true
}

trap cleanup INT TERM
tail -f "$PG_LOG_FILE"
