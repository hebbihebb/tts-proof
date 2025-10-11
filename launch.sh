#!/bin/bash

# TTS-Proof Application Launcher for Unix-like systems
# Usage: ./launch.sh

set -e  # Exit on error

echo ""
echo "=================================================="
echo "    TTS-Proof Application Launcher"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed"
    echo "Please install Python 3.10+ and try again"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ ERROR: Node.js is not installed"
    echo "Please install Node.js 16+ and try again"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo "✓ Node.js found: $(node --version)"

# Check and install backend dependencies
echo ""
echo "Checking Python dependencies..."
cd backend
if ! python3 -c "import fastapi, uvicorn, websockets" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip3 install fastapi uvicorn[standard] websockets python-multipart requests regex
fi
echo "✓ Python dependencies OK"

# Check and install frontend dependencies
cd ../frontend
echo "Checking Node.js dependencies..."
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi
echo "✓ Node.js dependencies OK"

cd ..

echo ""
echo "🚀 Starting TTS-Proof application..."
echo ""
echo "Backend will start on: http://localhost:8000"
echo "Frontend will start on: http://localhost:5173"
echo ""

# Start backend in new terminal window
if command -v gnome-terminal &> /dev/null; then
    # Linux with GNOME
    gnome-terminal --title="TTS-Proof Backend" --working-directory="$(pwd)/backend" -- python3 app.py
elif command -v xterm &> /dev/null; then
    # Generic X11 terminal
    xterm -title "TTS-Proof Backend" -e "cd backend && python3 app.py" &
elif command -v osascript &> /dev/null; then
    # macOS
    osascript -e "tell app \"Terminal\" to do script \"cd $(pwd)/backend && python3 app.py\""
else
    echo "⚠️  Could not detect terminal emulator, starting in background..."
    cd backend
    python3 app.py &
    BACKEND_PID=$!
    cd ..
fi

# Wait a moment for backend to start
sleep 3

# Start frontend in new terminal window  
if command -v gnome-terminal &> /dev/null; then
    # Linux with GNOME
    gnome-terminal --title="TTS-Proof Frontend" --working-directory="$(pwd)/frontend" -- npm run dev
elif command -v xterm &> /dev/null; then
    # Generic X11 terminal
    xterm -title "TTS-Proof Frontend" -e "cd frontend && npm run dev" &
elif command -v osascript &> /dev/null; then
    # macOS
    osascript -e "tell app \"Terminal\" to do script \"cd $(pwd)/frontend && npm run dev\""
else
    echo "⚠️  Could not detect terminal emulator, starting in background..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
fi

# Wait for servers to be ready
echo "⏳ Waiting for servers to start..."
sleep 5

# Try to open browser (if available)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173 2>/dev/null || true
elif command -v open &> /dev/null; then
    open http://localhost:5173 2>/dev/null || true
fi

echo ""
echo "=================================================="
echo "🎉 TTS-Proof is now running!"
echo "=================================================="
echo ""
echo "📍 Application URLs:"
echo "   • Frontend (Web UI): http://localhost:5173"
echo "   • Backend (API):     http://localhost:8000"
echo ""
echo "✅ Servers are running in separate terminal windows"
echo "💡 Close individual terminal windows to stop servers"
echo ""
echo "🚪 Launcher will exit in 3 seconds..."
sleep 3