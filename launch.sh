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
echo "Frontend will start on: http://localhost:5174"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo "✓ Servers stopped"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Start backend in background
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend in background
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for servers to be ready
echo "⏳ Waiting for servers to start..."
sleep 5

# Try to open browser (if available)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5174 2>/dev/null || true
elif command -v open &> /dev/null; then
    open http://localhost:5174 2>/dev/null || true
fi

echo ""
echo "=================================================="
echo "🎉 TTS-Proof is now running!"
echo "=================================================="
echo ""
echo "📍 Application URLs:"
echo "   • Frontend (Web UI): http://localhost:5174"
echo "   • Backend (API):     http://localhost:8000"
echo ""
echo "🛑 Press Ctrl+C to stop the application"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID