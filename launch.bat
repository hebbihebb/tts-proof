@echo off
title TTS-Proof Launcher
echo.
echo ============================:: Open browser
echo Opening browser...
start http://localhost:5173

echo.
echo TTS-Proof is now running!
echo.
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:5173echo    TTS-Proof Application Launcher
echo ===================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ and try again
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 16+ and try again
    pause
    exit /b 1
)

echo Checking dependencies...

:: Check if backend dependencies are installed
cd backend
echo Checking Python dependencies...
python -c "import fastapi, uvicorn, websockets" >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install fastapi uvicorn websockets python-multipart requests regex
    if errorlevel 1 (
        echo ERROR: Failed to install Python dependencies
        pause
        exit /b 1
    )
)

:: Check if frontend dependencies are installed
cd ..\frontend
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install Node.js dependencies
        pause
        exit /b 1
    )
)

cd ..

echo.
echo Starting TTS-Proof application...
echo.
echo Backend will start on: http://localhost:8000
echo Frontend will start on: http://localhost:5173
echo.
echo Press Ctrl+C to stop both servers
echo.

:: Start backend in a new window
start "TTS-Proof Backend" /D "%CD%\backend" python app.py

:: Wait a moment for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend in a new window
start "TTS-Proof Frontend" /D "%CD%\frontend" npm run dev

:: Wait a moment for frontend to start
timeout /t 5 /nobreak >nul

:: Open browser
echo Opening browser...
start http://localhost:5174

echo.
echo TTS-Proof is now running!
echo.
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:5174
echo.
echo Close this window or press any key to continue...
pause >nul