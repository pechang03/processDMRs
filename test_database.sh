#!/bin/bash

# Exit on any error
set -e

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project root directory
cd "$SCRIPT_DIR"

echo "Running DMR Analysis Database Tests..."

# Run database-specific tests with coverage
PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/backend" python -m coverage run -m pytest backend/tests/database/ -v

# Generate coverage report for database modules
coverage report --include="backend/app/database/*,backend/app/database/management/*"

# Generate HTML coverage report
coverage html --include="backend/app/database/*,backend/app/database/management/*"

# Exit with the test suite's exit code
exit ${PIPESTATUS[0]}
