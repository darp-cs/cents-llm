#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

PYTHON_CMD=""
for candidate in python3.12 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' >/dev/null 2>&1; then
    PYTHON_CMD="$candidate"
    break
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  echo "Python 3.12 is required but was not found on PATH."
  exit 1
fi

VENV_PY=".venv/bin/python"

RECREATE_VENV=0
if [ -x "$VENV_PY" ]; then
  if ! "$VENV_PY" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' >/dev/null 2>&1; then
    echo "Existing .venv is not Python 3.12. Recreating virtual environment..."
    RECREATE_VENV=1
  fi
else
  RECREATE_VENV=1
fi

if [ "$RECREATE_VENV" -eq 1 ]; then
  rm -rf .venv
  "$PYTHON_CMD" -m venv .venv
fi

"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r requirements.txt

if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "Created .env from .env.example."
fi

echo ""
echo "Setup complete."
echo "To start the app, run:"
echo "  ./scripts/start.sh"
