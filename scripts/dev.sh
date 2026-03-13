#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5174}"

PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "❌ Missing virtualenv python at $PYTHON_BIN"
  echo "Create it first: python -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "❌ npm is not installed or not in PATH"
  exit 1
fi

if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
  echo "❌ frontend dependencies missing (frontend/node_modules not found)"
  echo "Install first: cd frontend && npm install"
  exit 1
fi

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "🚀 Starting backend on http://$BACKEND_HOST:$BACKEND_PORT"
(
  cd "$ROOT_DIR"
  "$PYTHON_BIN" -m uvicorn app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

echo "🚀 Starting frontend on http://$FRONTEND_HOST:$FRONTEND_PORT"
(
  cd "$ROOT_DIR/frontend"
  npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

echo "✅ Dev stack running. Press Ctrl+C to stop both processes."
echo "   Backend docs:  http://$BACKEND_HOST:$BACKEND_PORT/docs"
echo "   Frontend app:  http://$FRONTEND_HOST:$FRONTEND_PORT"

wait "$BACKEND_PID" "$FRONTEND_PID"
