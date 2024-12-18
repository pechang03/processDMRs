from flask import jsonify
import os
from app.utils.extensions import app
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.connection import get_db_engine
from app.database.models import Timepoint

print("\n" + "="*50)
print(">>> IMPORTING app.py MODULE")
print("="*50 + "\n")
def configure_app(app):
    print("\n" + "*"*50)
    print(">>> STARTING APP CONFIGURATION")
    print("*"*50)
    
    print("\n>>> Getting project paths...")
    # Get the project root directory (three levels up from app.py)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    print(f">>> Current file location (__file__): {__file__}")
    print(f">>> Resolved project root: {project_root}")

    # Look for processDMR.env in project root
    env_file = os.path.join(project_root, "processDMR.env")
    print(f">>> Looking for env file at: {env_file}")

    if os.path.exists(env_file):
        print(">>> ENV FILE FOUND - Loading environment variables")
        load_dotenv(env_file)
        print(f">>> Successfully loaded environment from {env_file}")
        env_loaded = True
    else:
        print("\n" + "!"*50)
        print(f">>> ERROR: processDMR.env not found at {env_file}")
        print("!"*50 + "\n")
        env_loaded = False
        exit(1)
    # Get database path from environment or use default in project root
    db_path = os.getenv("DATABASE_PATH", os.path.join(project_root, "dmr_analysis.db"))
    database_url = f"sqlite:///{db_path}"

    # Set configuration
    app.config["DATABASE_URL"] = database_url
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "development")

    print("\n>>> FINAL CONFIGURATION:")
    print("-"*30)
    print(f">>> Project root: {project_root}")
    print(f">>> Database URL: {app.config['DATABASE_URL']}")
    print(f">>> Environment: {app.config['FLASK_ENV']}")
    print("-"*30)

    print("\n>>> CONFIGURATION COMPLETE")
    print("*"*50 + "\n")

    return env_loaded


# Configure the app before any routes are defined
configure_app(app)


@app.route("/api/health")
def health_check():
    """Health check endpoint that verifies system and database status."""
    database_url = app.config.get("DATABASE_URL", "not configured")
    print(f"\n>>> Health Check - Using database URL: {database_url}")
    
    health_status = {
        "status": "online",
        "environment": app.config["FLASK_ENV"],
        "database": "connected",
        "database_url": database_url
    }
    
    try:
        print(">>> Attempting database connection...")
        engine = get_db_engine()
        with Session(engine) as session:
            # Just open and close a session to verify connection
            print(">>> Executing test query...")
            session.execute(text("SELECT 1"))
            print(">>> Database connection successful")
    except Exception as e:
        print(f">>> Database connection failed: {str(e)}")
        print(f">>> Full exception: {repr(e)}")
        health_status["database"] = "disconnected"
        health_status["error"] = str(e)
        return jsonify(health_status), 503
        
    return jsonify(health_status)


@app.route("/api/timepoints")
def get_timepoints():
    """Get all timepoint names from the database."""
    engine = get_db_engine()
    with Session(engine) as session:
        timepoints = session.query(Timepoint.id, Timepoint.name).all()
        return jsonify([{"id": t.id, "name": t.name} for t in timepoints])


if __name__ == "__main__":
    # App is already configured at import time
    port = int(os.environ.get("FLASK_PORT", 5555))
    app.run(host="0.0.0.0", port=port, debug=True)
