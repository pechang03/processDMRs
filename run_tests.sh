#!/bin/bash
# run_tests.sh

# Exit on any error
set -e

# Run the test suite
python -m tests.graph_test_suite
