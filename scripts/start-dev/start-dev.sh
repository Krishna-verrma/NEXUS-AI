#!/usr/bin/env bash
# Nexus AI - Bash Development Launcher
echo "========================================="
echo "   NEXUS AI - Launching Development Hive  "
echo "========================================="

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

echo "[1/2] Starting FastAPI Backend on :8000..."
(cd "$DIR/backend" && python3 -m uvicorn app.main:app --reload --port 8000) &

echo "[2/2] Starting Vite Frontend on :5173..."
(cd "$DIR/frontend" && npm run dev) &

wait
