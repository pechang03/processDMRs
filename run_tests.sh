#!/bin/bash

# Exit on any error
set -e

# Get the directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project root directory
cd "$SCRIPT_DIR"

# Run the test suite
PYTHONPATH="$SCRIPT_DIR" python -m tests.graph_test_suite
