# AuraCart dev: FastAPI (8000) + Vite (5173)
# Run from AuraCart folder: .\start-dev.ps1
# Requires: Node.js (npm) + Python 3.11+ on PATH, or backend\venv312

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPy = Join-Path $backend "venv312\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { $venvPy = Join-Path $backend "venv\Scripts\python.exe" }

function Find-Python {
    if (Test-Path $venvPy) {
        $out = & $venvPy -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) { return $venvPy }
    }
    foreach ($cmd in @("py -3", "python", "python3")) {
        try {
            $p = Invoke-Expression "$cmd -c `"import sys; print(sys.executable)`"" 2>$null
            if ($p -and (Test-Path $p.Trim())) { return $p.Trim() }
        } catch { }
    }
    return $null
}

$py = Find-Python
if (-not $py) {
    Write-Host @"

No working Python found. Create a venv under backend and pip install -r requirements.txt

"@ -ForegroundColor Yellow
    exit 1
}

Write-Host "Using Python: $py"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "npm not found. Install Node.js LTS from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting FastAPI on http://127.0.0.1:8000 ..."
Start-Process -FilePath $py -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $backend -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "Starting Vite on http://127.0.0.1:5173 ..."
Push-Location $frontend
npm run dev
Pop-Location
