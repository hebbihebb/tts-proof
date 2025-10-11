# TTS-Proof Application Launcher (PowerShell)
# Usage: .\launch.ps1

param(
    [switch]$NoAutoOpen
)

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "    TTS-Proof Application Launcher" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>$null
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js 16+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow

# Check backend dependencies
Set-Location backend
Write-Host "Checking Python dependencies..."
try {
    python -c "import fastapi, uvicorn, websockets" 2>$null
    Write-Host "✓ Python dependencies OK" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
    pip install fastapi "uvicorn[standard]" websockets python-multipart requests regex
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: Failed to install Python dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "✓ Python dependencies installed" -ForegroundColor Green
}

# Check frontend dependencies
Set-Location ..\frontend
Write-Host "Checking Node.js dependencies..."
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: Failed to install Node.js dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "✓ Node.js dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✓ Node.js dependencies OK" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "🚀 Starting TTS-Proof application..." -ForegroundColor Green
Write-Host ""
Write-Host "Backend will start on: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend will start on: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""

# Start backend in new window
$backendJob = Start-Process -FilePath "python" -ArgumentList "app.py" -WorkingDirectory "backend" -WindowStyle Normal -PassThru

# Wait for backend to start
Start-Sleep -Seconds 3

# Start frontend in new window
$frontendJob = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory "frontend" -WindowStyle Normal -PassThru

# Wait for frontend to start
Write-Host "⏳ Waiting for servers to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Detect actual frontend port
Write-Host "🔍 Detecting frontend port..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$frontendPort = 5173
$portsToCheck = @(5173, 5174, 5175, 5176)

foreach ($port in $portsToCheck) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $frontendPort = $port
            Write-Host "✓ Frontend detected on port $port" -ForegroundColor Green
            break
        }
    } catch {
        # Port not responding, continue checking
    }
}

# Open browser
if (-not $NoAutoOpen) {
    Write-Host "🌐 Opening browser on port $frontendPort..." -ForegroundColor Green  
    Start-Process "http://localhost:$frontendPort"
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🎉 TTS-Proof is now running!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Application URLs:" -ForegroundColor White
Write-Host "   • Frontend (Web UI): http://localhost:$frontendPort" -ForegroundColor Cyan
Write-Host "   • Backend (API):     http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Servers are running in separate windows" -ForegroundColor Green
Write-Host "💡 Close individual server windows to stop them" -ForegroundColor Yellow
Write-Host ""
Write-Host "� Launcher will exit in 3 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 3