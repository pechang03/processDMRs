#!/bin/bash

# Exit on any error
set -e

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project root directory
cd "$SCRIPT_DIR"

# Add backend directory to PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/backend:$PYTHONPATH"

echo "Setting up DMR Analysis Database..."

# Check if PostgreSQL is running
if ! pg_isready; then
  echo "Error: PostgreSQL is not running"
  exit 1
fi

# Create database if it doesn't exist
echo "Creating database..."
python -c "
from sqlalchemy_utils import create_database, database_exists
from app.database.connection import get_db_engine
engine = get_db_engine()
if not database_exists(engine.url):
    create_database(engine.url)
"

# Initialize database schema
echo "Initializing database schema..."
python backend/app/database/scripts/initialize_database.py

# Create database views
echo "Creating database views..."
python backend/app/database/scripts/create_views.py

echo "Database setup complete!"

# Exit with the last command's exit code
exit ${PIPESTATUS[0]}
