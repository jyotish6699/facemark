#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  cp "$BACKEND_DIR/.env.example" "$ENV_FILE"
  echo "Created backend/.env from backend/.env.example"
else
  echo "backend/.env already exists, keeping your current values."
fi

echo "Local setup complete."
echo "Use 3 terminals from repo root:"
echo "1) ./scripts/run-database.sh"
echo "2) ./scripts/run-backend.sh"
echo "3) ./scripts/run-frontend.sh"
