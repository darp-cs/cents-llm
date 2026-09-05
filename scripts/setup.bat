@echo off
setlocal

set "ROOT=%~dp0.."
pushd "%ROOT%"

set "PYTHON_CMD="
set "VENV_PY=.venv\Scripts\python.exe"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
  if %ERRORLEVEL%==0 set "PYTHON_CMD=py -3.12"
)

if not defined PYTHON_CMD (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
    if %ERRORLEVEL%==0 set "PYTHON_CMD=python"
  )
)

if not defined PYTHON_CMD (
  echo Python 3.12 is required but was not found on PATH.
  goto :error
)

set "RECREATE_VENV=0"
if exist "%VENV_PY%" (
  "%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
  if %ERRORLEVEL% neq 0 (
    echo Existing .venv is not Python 3.12. Recreating virtual environment...
    set "RECREATE_VENV=1"
  )
) else (
  set "RECREATE_VENV=1"
)

if "%RECREATE_VENV%"=="1" (
  if exist ".venv" rmdir /s /q ".venv"
  call %PYTHON_CMD% -m venv .venv
  if %ERRORLEVEL% neq 0 goto :error
)

if not exist "%VENV_PY%" (
  echo Virtual environment Python was not found at "%VENV_PY%".
  goto :error
)

"%VENV_PY%" -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 goto :error

"%VENV_PY%" -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 goto :error

if not exist ".env" (
  if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
    echo Created .env from .env.example.
  )
)

echo.
echo Setup complete.
echo To start the app, run:
echo   scripts\start.bat
popd
exit /b 0

:error
echo Setup failed.
popd
exit /b 1
