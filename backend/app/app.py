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
    # Get the project root directory (three levels up from app.py)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Look for processDMR.env in project root
    env_file = os.path.join(project_root, "processDMR.env")
    
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")
        env_loaded = True
    else:
        print(f"Warning: processDMR.env not found at {env_file}")
        env_loaded = False

    # Get database path from environment or use default in project root
    db_path = os.getenv("DATABASE_PATH", os.path.join(project_root, "dmr_analysis.db"))
    database_url = f"sqlite:///{db_path}"

    # Set configuration
    app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", database_url)
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "development")
    
    # Print the configuration being used
    print(f"Using database: {app.config['DATABASE_URL']}")
    print(f"Environment: {app.config['FLASK_ENV']}")
    
    return env_loaded

if __name__ == '__main__':
    configure_app(app)
    port = int(os.environ.get('FLASK_PORT', 5555))
    app.run(host='0.0.0.0', port=port, debug=True)
