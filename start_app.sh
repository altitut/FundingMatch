#!/bin/bash

echo "🚀 Starting FundingMatch Application"
echo "===================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt -q

# Start Flask backend
echo "Starting Flask backend..."
python app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

# Check if Flask is running
if ! kill -0 $FLASK_PID 2>/dev/null; then
    echo "❌ Failed to start Flask backend"
    exit 1
fi

echo "✅ Flask backend running on http://localhost:5000"

# Start React frontend
echo "Starting React frontend..."
cd frontend
npm start

# Cleanup on exit
trap "kill $FLASK_PID 2>/dev/null" EXIT