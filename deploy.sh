#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/web/frontend"
BACKEND_DIR="$PROJECT_ROOT/web/backend"

echo "=== Activating virtual environment ==="
source "$PROJECT_ROOT/.venv/bin/activate"

echo "=== Installing backend dependencies ==="
pip install -r "$BACKEND_DIR/requirements.txt" --quiet

echo "=== Installing frontend dependencies ==="
cd "$FRONTEND_DIR"
npm install --silent

echo "=== Building frontend ==="
npm run build

echo "=== Starting server ==="
cd "$BACKEND_DIR"
uvicorn main:combined_app --host 0.0.0.0 --port 8000
