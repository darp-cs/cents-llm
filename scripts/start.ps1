$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Python virtual environment not found. Run .\scripts\setup.ps1 first."
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama was not found on PATH. Install Ollama and try again."
}

& ollama list | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ollama server is not running. Starting Ollama..."
    $ollamaLog = Join-Path $env:TEMP "cents-llm-ollama.log"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "ollama serve > `"$ollamaLog`" 2>&1"

    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
        & ollama list | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 1
    }

    if (-not $ready) {
        throw "Failed to connect to Ollama after starting it. Check log: $ollamaLog"
    }
}

& (Join-Path $root ".venv\Scripts\python.exe") -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8100
