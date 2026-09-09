#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -x "$PROJECT_DIR/server/.venv/bin/python" ]; then
  python3 -m venv "$PROJECT_DIR/server/.venv"
fi

"$PROJECT_DIR/server/.venv/bin/python" -m pip install -r "$PROJECT_DIR/server/requirements.txt"

cd "$PROJECT_DIR/web"
npm ci
npm run build

cd "$PROJECT_DIR/server"
export WEB_DIST_DIR=../web/dist
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
