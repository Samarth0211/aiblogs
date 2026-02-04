#!/bin/bash

# Run AI Agents Script
echo "╔════════════════════════════════════╗"
echo "║   RUNNING AI AGENTS                ║"
echo "╚════════════════════════════════════╝"
echo ""

# Check if backend server is running
if ! curl -s http://localhost:8000/api/posts > /dev/null 2>&1; then
    echo "✖ Backend server is not running!"
    echo ""
    echo "Please start the backend first:"
    echo "  cd backend && python3 main.py"
    exit 1
fi

# Run agents
cd backend
python3 agents.py $@
cd ..

echo ""
echo "✓ Done! Check your blog at index.html"
