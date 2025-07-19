#!/bin/bash

echo "🚀 Starting FundingMatch Application"
echo "===================================="

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "🔪 Killing process on port $port (PID: $pid)..."
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
}

# Clear ports before starting
echo "🧹 Clearing ports..."
kill_port 8787  # Flask backend
kill_port 3000  # React frontend

# Kill any existing python app.py processes
pkill -f "python app.py" 2>/dev/null

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt -q

# Start Flask backend
echo "🔧 Starting Flask backend..."
python app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

# Check if Flask is running
if ! kill -0 $FLASK_PID 2>/dev/null; then
    echo "❌ Failed to start Flask backend"
    exit 1
fi

echo "✅ Flask backend running on http://localhost:8787"

# Start React frontend
echo "⚛️  Starting React frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start the frontend
npm start &
REACT_PID=$!

# Give frontend time to start
sleep 3

echo ""
echo "✅ FundingMatch Application Started!"
echo "===================================="
echo "🔧 Backend: http://localhost:8787"
echo "⚛️  Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the application"

# Wait for either process to exit
wait

# Cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down FundingMatch..."
    kill $FLASK_PID 2>/dev/null
    kill $REACT_PID 2>/dev/null
    # Also kill any npm start processes
    pkill -f "npm start" 2>/dev/null
    pkill -f "react-scripts start" 2>/dev/null
    echo "👋 Goodbye!"
}

trap cleanup EXIT INT TERM