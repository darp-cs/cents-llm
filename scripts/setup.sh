#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "Python 3.12 is required but was not found on PATH."
  exit 1
fi

VENV_PY=".venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
  rm -rf .venv
  python3.12 -m venv .venv
fi

"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r requirements.txt

echo ""
echo "Setup complete."
echo "To start the app, run:"
echo "  ./scripts/start.sh"
