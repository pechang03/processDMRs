#!/bin/bash

# Exit on any error
set -e

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project root directory
cd "$SCRIPT_DIR"

echo "Running DMR Analysis Database Tests..."

# Run database-specific tests with coverage
PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" python -m coverage run -m pytest tests/database/ -v

# Generate coverage report for database modules
coverage report --include="database/*,scripts/initialize_database.py"

# Generate HTML coverage report
coverage html --include="database/*,scripts/initialize_database.py"

# Exit with the test suite's exit code
exit ${PIPESTATUS[0]}
