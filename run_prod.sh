#!/bin/bash

# Stop on error
set -e

echo "🧹 Cleaning up previous instances..."
# Stop background scheduler
./stop_background.sh

# Kill process on port 8000 if it exists
PORT_PID=$(lsof -ti:8000 || true)
if [ -n "$PORT_PID" ]; then
    echo "🛑 Killing process on port 8000 (PID: $PORT_PID)..."
    kill -9 $PORT_PID
else
    echo "✅ Port 8000 is free."
fi

echo "🚀 Building Frontend..."
cd dashboard
npm install
npm run build
cd ..

echo "✅ Frontend Build Complete."

# Start Background Scheduler
./run_background.sh

echo "🚀 Starting Production Server..."
echo "🌐 Open http://localhost:8000 in your browser."

# Install Python deps if needed (optional check)
# pip install -r requirements.txt

uv run dashboard_server.py
