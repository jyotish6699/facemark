#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"
ENV_FILE="$BACKEND_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  cp "$BACKEND_DIR/.env.example" "$ENV_FILE"
  echo "Created backend/.env from backend/.env.example"
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if ! python -c "import fastapi,uvicorn,sqlalchemy,psycopg2" >/dev/null 2>&1; then
  pip install -r "$BACKEND_DIR/requirements.txt"
fi

cd "$BACKEND_DIR"
exec uvicorn app.main:app --reload --port 8001
