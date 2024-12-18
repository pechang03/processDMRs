#!/bin/bash

# Colors for status messages
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check required dependencies
echo "Checking dependencies..."

# Check for Python
if ! command_exists python; then
  echo -e "${RED}Error: Python is not installed${NC}"
  exit 1
fi

# Check for Node.js
if ! command_exists node; then
  echo -e "${RED}Error: Node.js is not installed${NC}"
  exit 1
fi

# Check for npm
if ! command_exists npm; then
  echo -e "${RED}Error: npm is not installed${NC}"
  exit 1
fi

# Check if conda environment is activated
if [[ -z "${CONDA_DEFAULT_ENV}" ]]; then
  echo -e "${RED}Error: No conda environment is activated${NC}"
  exit 1
fi

# Check if required directories exist
if [ ! -d "backend" ]; then
  echo -e "${RED}Error: backend directory not found${NC}"
  exit 1
fi

if [ ! -d "frontend" ]; then
  echo -e "${RED}Error: frontend directory not found${NC}"
  exit 1
fi

# Start backend server
echo -e "${GREEN}Starting Flask backend server...${NC}"
osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"' && cd backend && python -m flask run --debug"'

# Start frontend development server
echo -e "${GREEN}Starting React frontend...${NC}"
osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"'/frontend && npm start"'

echo -e "${GREEN}Both servers are starting...${NC}"
echo "Backend will be available at: http://localhost:5555"
echo "Frontend will be available at: http://localhost:3000"

#!/bin/bash

# Kill any existing processes on ports 3000 and 5000
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

# Start backend
echo "Starting Flask backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app/app.py
export FLASK_ENV=development
export FLASK_PORT=5555
python -m flask run --host=0.0.0.0 --port=5555 &

# Wait for backend to start
echo "Backend will be available at: http://localhost:5555"
sleep 5

# Start frontend
echo "Starting React frontend..."
cd ../frontend
npm install
npm start &

# Wait for both processes
wait
