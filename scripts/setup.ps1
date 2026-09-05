$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Invoke-CheckedCommand {
    param(
        [scriptblock]$Command,
        [string]$FailureMessage
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

function Test-Python312 {
    param(
        [string]$Command,
        [string[]]$Args
    )

    & $Command @Args -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" | Out-Null
    return $LASTEXITCODE -eq 0
}

$pythonCmd = $null
$pythonArgs = @()
$pythonCandidates = @(
    @{ Cmd = "py"; Args = @("-3.12") },
    @{ Cmd = "python3.12"; Args = @() },
    @{ Cmd = "python3"; Args = @() },
    @{ Cmd = "python"; Args = @() }
)

foreach ($candidate in $pythonCandidates) {
    if (-not (Get-Command $candidate.Cmd -ErrorAction SilentlyContinue)) {
        continue
    }

    if (Test-Python312 -Command $candidate.Cmd -Args $candidate.Args) {
        $pythonCmd = $candidate.Cmd
        $pythonArgs = $candidate.Args
        break
    }
}

if (-not $pythonCmd) {
    throw "Python 3.12 is required but no usable Python 3.12 command was found."
}

$venvDir = Join-Path $root ".venv"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

$needsVenvCreate = $true
if (Test-Path $venvPython) {
    & $venvPython -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $needsVenvCreate = $false
    }
    else {
        Write-Host "Existing .venv is not Python 3.12. Recreating virtual environment..."
        Remove-Item -Recurse -Force $venvDir
    }
}
elseif (Test-Path $venvDir) {
    Remove-Item -Recurse -Force $venvDir
}

if ($needsVenvCreate) {
    & $pythonCmd @pythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create .venv."
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment Python was not found at '$venvPython'."
}

& $venvPython -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "The virtual environment is not using Python 3.12."
}

Invoke-CheckedCommand -Command { & $venvPython -m pip install --upgrade pip } -FailureMessage "Failed to upgrade pip."
Invoke-CheckedCommand -Command { & $venvPython -m pip install -r requirements.txt } -FailureMessage "Failed to install dependencies from requirements.txt."

if ((-not (Test-Path ".env")) -and (Test-Path ".env.example")) {
    Copy-Item -Path ".env.example" -Destination ".env"
    Write-Host "Created .env from .env.example."
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "To start the app, run:"
Write-Host "  .\scripts\start.ps1"
