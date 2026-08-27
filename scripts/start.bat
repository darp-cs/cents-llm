@echo off
setlocal

set ROOT=%~dp0\..
pushd "%ROOT%"

if not exist ".venv\Scripts\python.exe" (
  echo Python virtual environment not found. Run scripts\setup.bat first.
  popd
  exit /b 1
)

.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8100
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
