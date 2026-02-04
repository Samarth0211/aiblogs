#!/bin/bash

# Dev/Blog Startup Script

echo "╔════════════════════════════════════╗"
echo "║     DEV/BLOG STARTUP               ║"
echo "╚════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "✖ Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
echo "[1/3] Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Start the backend server
echo ""
echo "[2/3] Starting FastAPI backend..."
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2

# Open frontend in browser
echo ""
echo "[3/3] Opening frontend..."
echo ""
echo "╔════════════════════════════════════╗"
echo "║  Blog:  http://localhost:8000      ║"
echo "║  Admin: Open admin.html            ║"
echo "║  API:   http://localhost:8000/docs ║"
echo "╚════════════════════════════════════╝"
echo ""
echo "Frontend files:"
echo "  - index.html (Blog)"
echo "  - admin.html (Admin Panel)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Open index.html
if command -v xdg-open &> /dev/null; then
    xdg-open index.html
elif command -v open &> /dev/null; then
    open index.html
fi

# Wait for Ctrl+C
trap "kill $BACKEND_PID; exit" INT
wait $BACKEND_PID
