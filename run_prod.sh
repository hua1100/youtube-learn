#!/bin/bash

# Stop on error
set -e

echo "🚀 Building Frontend..."
cd dashboard
npm install
npm run build
cd ..

echo "✅ Frontend Build Complete."
echo "🚀 Starting Production Server..."
echo "🌐 Open http://localhost:8000 in your browser."

# Install Python deps if needed (optional check)
# pip install -r requirements.txt

python dashboard_server.py
