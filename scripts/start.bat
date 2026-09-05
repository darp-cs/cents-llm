@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0.."
pushd "%ROOT%"

if not exist ".venv\Scripts\python.exe" (
  echo Python virtual environment not found. Run scripts\setup.bat first.
  popd
  exit /b 1
)

where ollama >nul 2>&1
if errorlevel 1 (
  echo Ollama was not found on PATH. Install Ollama and try again.
  popd
  exit /b 1
)

ollama list >nul 2>&1
if errorlevel 1 (
  echo Ollama server is not running. Starting Ollama...
  start "" /B ollama serve

  set /a ATTEMPTS=0
  :wait_for_ollama
  ollama list >nul 2>&1
  if not errorlevel 1 goto :ollama_ready
  set /a ATTEMPTS+=1
  if !ATTEMPTS! geq 20 goto :ollama_failed
  timeout /t 1 /nobreak >nul
  goto :wait_for_ollama

  :ollama_failed
  echo Failed to connect to Ollama after starting it.
  echo Check whether port 11434 is already in use by another process.
  popd
  exit /b 1
)

:ollama_ready
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8100
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
