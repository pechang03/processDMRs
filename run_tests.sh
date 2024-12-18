#!/bin/bash

# Exit on any error
set -e

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project root directory
cd "$SCRIPT_DIR"

# Run the test suite with coverage reporting
PYTHONPATH="$SCRIPT_DIR/backend:$PYTHONPATH" python -m coverage run -m unittest discover -s backend/tests -p 'test_*.py' -v

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html

# Exit with the test suite's exit code
exit ${PIPESTATUS[0]}
