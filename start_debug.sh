#!/bin/bash

# Kill any existing processes on ports 3000 and 5555
kill_port() {
  local port=$1
  pid=$(lsof -t -i:$port)
  if [ ! -z "$pid" ]; then
    echo "Killing process on port $port"
    kill -9 $pid
  fi
}

kill_port 3000
kill_port 5555

# Set environment variables and Python path
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export FLASK_APP=backend/app/app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_PORT=5555
export DATABASE_URL=sqlite:///$PWD/dmr_analysis.db

# Add API base URL for frontend
export REACT_APP_API_URL=http://localhost:5555/api

# Start backend
echo "Starting Flask backend..."
python -m flask run --host=0.0.0.0 --port=5555 &

# Wait for backend to start
echo "Backend will be available at: http://localhost:5555"
sleep 2

# Start frontend
echo "Starting React frontend..."
cd frontend
REACT_APP_API_URL=$REACT_APP_API_URL npm start &

# Wait for both processes
wait
