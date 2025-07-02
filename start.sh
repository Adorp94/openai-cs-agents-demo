#!/bin/bash

echo "🚀 Starting Promotional Products Chat System..."

# Kill any existing servers first
echo "🛑 Stopping any existing servers..."
pkill -f "uvicorn.*api:app" 2>/dev/null
pkill -f "next dev" 2>/dev/null
sleep 2

# Start backend in background
echo "📡 Starting backend server..."
cd backend
./venv/bin/python -m uvicorn api:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd ..

# Wait a moment for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Test backend connection
curl -s http://localhost:8000 >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Backend started successfully on port 8000"
else
    echo "❌ Backend failed to start"
fi

# Start frontend
echo "🎨 Starting frontend server..."
cd frontend
npm run dev:next &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ..

echo ""
echo "✅ Servers started successfully!"
echo "📡 Backend:  http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT

# Wait for either process to exit
wait $BACKEND_PID $FRONTEND_PID 