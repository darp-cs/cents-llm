@echo off
setlocal

set ROOT=%~dp0\..
pushd "%ROOT%"

if not exist ".venv\Scripts\python.exe" (
  set CREATED_VENV=0

  where py >nul 2>&1
  if %ERRORLEVEL%==0 (
    py -3.12 -m venv .venv
    if %ERRORLEVEL%==0 set CREATED_VENV=1
  )

  if %CREATED_VENV%==0 (
    python -m venv .venv
    if %ERRORLEVEL% neq 0 goto :error
  )
)

.venv\Scripts\python.exe -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 goto :error

.venv\Scripts\python.exe -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 goto :error

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
