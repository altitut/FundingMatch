#!/bin/bash

echo "🛑 Stopping FundingMatch Application"
echo "===================================="

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "🔪 Killing process on port $port (PID: $pid)..."
        kill -9 $pid 2>/dev/null
    else
        echo "✅ Port $port is already free"
    fi
}

# Kill Flask backend
echo "Stopping Flask backend..."
kill_port 5001
pkill -f "python app.py" 2>/dev/null

# Kill React frontend
echo "Stopping React frontend..."
kill_port 3000
pkill -f "npm start" 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null

echo ""
echo "✅ All processes stopped!"
echo "👋 Goodbye!"