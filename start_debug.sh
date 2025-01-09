#!/bin/bash

# Add timestamp to logs
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Kill any existing processes on ports 3000 and 5555
kill_port() {
    local port=$1
    pid=$(lsof -t -i:$port)
    if [ ! -z "$pid" ]; then
        log "Killing process on port $port"
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
log "Setting REACT_APP_API_URL to: $REACT_APP_API_URL"

# Start backend with increased logging
log "Starting Flask backend..."
export FLASK_LOG_LEVEL=DEBUG
python -m flask run --host=0.0.0.0 --port=5555 &

# Wait for backend to start
log "Backend will be available at: http://localhost:5555"
sleep 2

# Start frontend with environment variable
log "Starting React frontend with REACT_APP_API_URL=$REACT_APP_API_URL"
cd frontend
REACT_APP_API_URL=$REACT_APP_API_URL npm start &

# Wait for both processes
wait
