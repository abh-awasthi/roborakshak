#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="$(command -v python3)"

if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/venv/bin/activate"
  if ! python3 - <<'PY' >/dev/null 2>&1
import importlib.util
import sys
sys.exit(0 if importlib.util.find_spec('picamera2') else 1)
PY
  then
    deactivate 2>/dev/null || true
    PYTHON_BIN="/usr/bin/python3"
  fi
fi

exec "$PYTHON_BIN" -u "$SCRIPT_DIR/backend/app.py"
