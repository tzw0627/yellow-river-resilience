#!/bin/bash
set -e
cd "$(dirname "$0")"
if curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
  open http://127.0.0.1:8000
  exit 0
fi
export WEB_DIST_DIR=../web/dist
(
  for attempt in {1..30}; do
    if curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
      open http://127.0.0.1:8000
      exit 0
    fi
    sleep 1
  done
) &
cd server
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
