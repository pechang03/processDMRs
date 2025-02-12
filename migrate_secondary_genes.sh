#!/bin/bash
# Get the directory containing this script (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load and export environment variables from processDMR.env
if [ -f "processDMR.env" ]; then
  echo "Loading environment variables from processDMR.env..."
  set -a  # Automatically export all variables
  source processDMR.env
  set +a  # Stop automatically exporting
  
  # Explicitly export the required variables
  export DATABASE_URL
  export DATABASE_SECONDARY_URL
  
  # Verify the variables are set
  if [ -z "$DATABASE_URL" ] || [ -z "$DATABASE_SECONDARY_URL" ]; then
    echo "Error: Required environment variables are not set"
    exit 1
  fi
  
  echo "DATABASE_URL=$DATABASE_URL"
  echo "DATABASE_SECONDARY_URL=$DATABASE_SECONDARY_URL"
else
  echo "Error: processDMR.env not found"
  exit 1
fi

echo "Migrating secondary gene data..."
python -m backend.app.database.management.migrate_secondary_genes
echo "Migration complete!"

exit 0
