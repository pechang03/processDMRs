#!/bin/bash

# Exit on any error
set -e

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project root directory
cd "$SCRIPT_DIR"

# Add project root and backend directories to PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/:$PYTHONPATH"
echo "Setting up DMR Analysis Database..."

# Check if PostgreSQL is running
#if ! pg_isready; then
#  echo "Error: PostgreSQL is not running"
#  exit 1
#fi

# Create database if it doesn't exist
echo "Creating database..."
python -c "
from sqlalchemy_utils import create_database, database_exists
from backend.app.database.connection import get_db_engine
engine = get_db_engine()
if not database_exists(engine.url):
    create_database(engine.url)
"

# Initialize database schema
echo "Initializing database schema..."
python -m backend.app.database.management.initialize_database

# Handle SQL views symbolic link
echo "Setting up SQL views symbolic link..."
VIEWS_FILE="backend/app/database/views.sql"
if [ -e "$VIEWS_FILE" ]; then
  echo "Removing existing views.sql file..."
  rm "$VIEWS_FILE"
fi
echo "Creating symbolic link for views.sql..."
ln -s ../management/sql/views/create_views.sql "$VIEWS_FILE"

# Create database views
echo "Creating database views..."
python -m backend.app.database.management.create_views

echo "Database setup complete!"

# Exit with the last command's exit code
exit ${PIPESTATUS[0]}
