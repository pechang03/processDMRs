from flask import jsonify
import os
from app.utils.extensions import app
from dotenv import load_dotenv

from flask import jsonify
import os
from app.utils.extensions import app
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database.connection import get_db_engine
from app.database.models import Timepoint

@app.route('/api/timepoints')
def get_timepoints():
    """Get all timepoint names from the database."""
    engine = get_db_engine()
    with Session(engine) as session:
        timepoints = session.query(Timepoint.id, Timepoint.name).all()
        return jsonify([{
            'id': t.id,
            'name': t.name
        } for t in timepoints])

def configure_app(app):
    # Look for processDMR.env in current and parent directories
    env_file = "processDMR.env"
    env_paths = [
        env_file,
        os.path.join("..", env_file),
        os.path.join("..", "..", env_file)
    ]
    
    env_loaded = False
    for path in env_paths:
        if os.path.exists(path):
            load_dotenv(path)
            print(f"Loaded environment from {path}")
            env_loaded = True
            break
    
    if not env_loaded:
        print("Warning: processDMR.env not found")

    # Set default configuration with specific database name
    app.config.setdefault("DATABASE_URL", "sqlite:///dmr_analysis.db")
    app.config.setdefault("FLASK_ENV", "development")

    # Override with environment variables if they exist
    app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", app.config["DATABASE_URL"])
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", app.config["FLASK_ENV"])
    
    # Add MIME type handling
    app.config["MIME_TYPES"] = {".css": "text/css", ".js": "application/javascript"}
    
    # Print the configuration being used
    print(f"Using database: {app.config['DATABASE_URL']}")
    print(f"Environment: {app.config['FLASK_ENV']}")
    
    return env_loaded

if __name__ == '__main__':
    configure_app(app)
    port = int(os.environ.get('FLASK_PORT', 5555))
    app.run(host='0.0.0.0', port=port, debug=True)
