import sqlite3
from typing import Dict, List, Optional
from ...database.connection import get_database_path

class DatabaseUtils:
    def __init__(self):
        self.db_path = get_database_path()

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection using the configured path."""
        return sqlite3.connect(self.db_path)

    def get_schema(self) -> Dict[str, List[str]]:
        """Get the database schema as a dictionary of table names and their CREATE statements."""
        schema = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
                create_statement = cursor.fetchone()[0]
                schema[table_name] = create_statement

        return schema

    def get_table_info(self, table_name: str) -> List[Dict[str, str]]:
        """Get detailed information about a specific table's columns."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            return [
                {
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "default": col[4],
                    "is_primary": bool(col[5])
                }
                for col in columns
            ]

    def format_schema_for_prompt(self) -> str:
        """Format the database schema in a way that's suitable for LLM prompts."""
        schema = self.get_schema()
        formatted = []
        
        for table_name, create_stmt in schema.items():
            columns = self.get_table_info(table_name)
            formatted.append(f"Table: {table_name}")
            formatted.append("Columns:")
            for col in columns:
                constraints = []
                if col["is_primary"]:
                    constraints.append("PRIMARY KEY")
                if col["notnull"]:
                    constraints.append("NOT NULL")
                if col["default"]:
                    constraints.append(f"DEFAULT {col['default']}")
                
                formatted.append(f"  - {col['name']} ({col['type']}) {' '.join(constraints)}")
            formatted.append("")
        
        return "\n".join(formatted)

