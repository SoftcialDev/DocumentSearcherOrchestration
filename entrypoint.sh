#!/usr/bin/env bash
set -euo pipefail

# Forward signals to children
_term() {
  echo "Received SIGTERM, stopping services..."
  pkill -TERM -P $$
  wait
}
trap _term TERM INT

# Start backend (your main.py runs uvicorn on :5000 and orchestration)
echo "Starting backend (FastAPI) on :5000..."
python -u /app/main.py &

# Start frontend dev server (CRA) on :3000
echo "Starting frontend (CRA) on :3000..."
cd /frontend
npm start &

# Wait for the first one to exit, then exit with same code
wait -n
exit $?
