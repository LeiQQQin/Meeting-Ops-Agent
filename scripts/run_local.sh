#!/usr/bin/env bash
# Start Meeting-Ops-Agent backend and frontend in development mode
set -e

echo "🚀 Starting Meeting-Ops-Agent..."

# Check .env exists
if [ ! -f .env ]; then
    echo "❌ .env not found. Run ./scripts/setup.sh first."
    exit 1
fi

# Start backend
echo "Starting backend on http://localhost:8000 ..."
cd src/backend
source .venv/bin/activate 2>/dev/null || true
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ../..

# Wait for backend
sleep 2
echo "✅ Backend started (PID: $BACKEND_PID)"

# Start frontend
echo "Starting frontend on http://localhost:3000 ..."
cd src/frontend
npm start &
FRONTEND_PID=$!
cd ../..

echo ""
echo "✅ Meeting-Ops-Agent is running!"
echo "   Backend:  http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services."

# Cleanup on exit
trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
