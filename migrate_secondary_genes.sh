#!/bin/bash
# Get the directory containing this script (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from processDMR.env
if [ -f "processDMR.env" ]; then
  echo "Loading environment variables from processDMR.env..."
  source processDMR.env
else
  echo "Warning: processDMR.env not found. Make sure your environment variables are set."
fi
echo $DATABASE_URL
echo $DATABASE_SECONDARY_URL

echo "Migrating secondary gene data..."
python -m backend.app.database.management.migrate_secondary_genes
echo "Migration complete!"

exit 0
