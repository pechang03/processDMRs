"""Create database views for DMR analysis system."""

import os
import sys
from sqlalchemy import text
from database.connection import get_db_engine

def read_sql_file(filename):
    """Read SQL from a file in the sql/views directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_dir = os.path.join(script_dir, '..', 'sql', 'views')
    file_path = os.path.join(sql_dir, filename)
    
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading SQL file {filename}: {e}")
        return None

def create_views(engine):
    """Create all database views."""
    try:
        # Read SQL files
        drop_views_sql = read_sql_file('drop_views.sql')
        create_views_sql = read_sql_file('create_views.sql')

        if not drop_views_sql or not create_views_sql:
            raise Exception("Failed to read SQL files")

        with engine.connect() as conn:
            print("Dropping existing views...")
            # Execute drop statements
            for statement in drop_views_sql.split(';'):
                if statement.strip():
                    try:
                        conn.execute(text(statement))
                    except Exception as e:
                        print(f"Warning: Error dropping view: {e}")

            print("Creating new views...")
            # Execute create statements
            for statement in create_views_sql.split(';'):
                if statement.strip():
                    try:
                        conn.execute(text(statement))
                        print(f"Successfully executed: {statement[:60]}...")
                    except Exception as e:
                        print(f"Error creating view: {e}")
                        print(f"Failed statement: {statement}")
                        raise

            conn.commit()
            print("Database views created successfully")

    except Exception as e:
        print(f"Error creating views: {e}")
        raise
    

def main():
    """Main entry point for creating database views."""
    try:
        engine = get_db_engine()
        create_views(engine)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    finally:
        pass

if __name__ == "__main__":
    main()
