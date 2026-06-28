#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/venv/bin/activate"
fi

exec python3 -u "$SCRIPT_DIR/backend/app.py"
