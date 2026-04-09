#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Ensure virtual environment
if [ ! -d .venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

# Install Python deps
echo "Installing Python dependencies..."
pip install -q -e ".[dev,ml]"

# Install frontend deps
echo "Installing frontend dependencies..."
cd web && npm install --silent && cd ..

# Kill existing servers
pkill -f "uvicorn alertforge" 2>/dev/null || true
pkill -f "vite.*5173" 2>/dev/null || true

# Start backend
echo "Starting backend on :8000..."
uvicorn alertforge.api.app:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "Backend ready."
    break
  fi
  sleep 1
done

# Start frontend
echo "Starting frontend on :5173..."
cd web && npm run dev -- --open &
FRONTEND_PID=$!

# Cleanup on exit
cleanup() {
  echo "Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
