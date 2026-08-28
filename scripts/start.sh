#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

VENV_PY=".venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
  echo "Virtual environment not found. Please run ./scripts/setup.sh first."
  exit 1
fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama was not found on PATH. Install Ollama and try again."
  exit 1
fi

if ! ollama list >/dev/null 2>&1; then
  echo "Ollama server is not running. Starting Ollama..."
  OLLAMA_LOG="${TMPDIR:-/tmp}/cents-llm-ollama.log"
  nohup ollama serve >"$OLLAMA_LOG" 2>&1 &

  READY=0
  for _ in $(seq 1 20); do
    if ollama list >/dev/null 2>&1; then
      READY=1
      break
    fi
    sleep 1
  done

  if [ "$READY" -ne 1 ]; then
    echo "Failed to connect to Ollama after starting it. Check log: $OLLAMA_LOG"
    exit 1
  fi
fi

"$VENV_PY" -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8100
