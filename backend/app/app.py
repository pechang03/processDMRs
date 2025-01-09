from flask import jsonify, current_app
import os
from .utils.extensions import app
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database.connection import get_db_engine
from .database.models import Timepoint
from .routes.component_routes import component_bp

print("\n" + "=" * 50)
print(">>> IMPORTING app.py MODULE")
print("=" * 50 + "\n")


def configure_app(app):
    print("\n" + "*" * 50)
    print(">>> STARTING APP CONFIGURATION")
    print("*" * 50)

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
        print("\n" + "!" * 50)
        print(f">>> ERROR: processDMR.env not found at {env_file}")
        print("!" * 50 + "\n")
        env_loaded = False
        exit(1)

    # Get database path from environment or use default in project root
    db_path = os.getenv("DATABASE_PATH", os.path.join(project_root, "dmr_analysis.db"))
    database_url = f"sqlite:///{db_path}"

    # Set configuration
    app.config["DATABASE_URL"] = database_url
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "development")
    # Add DATA_DIR to app config
    app.config["DATA_DIR"] = os.getenv("DATA_DIR", os.path.join(project_root, "data"))
    # Add DATA_DIR to app config
    app.config["DATA_DIR"] = os.getenv("DATA_DIR", os.path.join(project_root, "data"))

    print("\n>>> FINAL CONFIGURATION:")
    print("-" * 30)
    print(f">>> Project root: {project_root}")
    print(f">>> Database URL: {app.config['DATABASE_URL']}")
    print(f">>> Environment: {app.config['FLASK_ENV']}")
    print(f">>> Data directory: {app.config['DATA_DIR']}")
    print("-" * 30)

    print("\n>>> CONFIGURATION COMPLETE")
    print("*" * 50 + "\n")

    return env_loaded


# Configure the app before any routes are defined
configure_app(app)

# Initialize GraphManager
from backend.app.core.graph_manager import GraphManager
with app.app_context():
    app.graph_manager = GraphManager()

# Register blueprints
app.register_blueprint(component_bp)

@app.route("/api/graph-manager/status")
def graph_manager_status():
    """Check GraphManager status"""
    try:
        graph_manager = current_app.graph_manager
        return jsonify({
            "status": "ok",
            "initialized": graph_manager.is_initialized(),
            "data_dir": graph_manager.data_dir,
            "loaded_timepoints": list(graph_manager.original_graphs.keys())
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Import and register routes


@app.route("/api/health")
def health_check():
    """Health check endpoint that verifies system and database status."""
    database_url = app.config.get("DATABASE_URL", "not configured")
    print(f"\n>>> Health Check - Using database URL: {database_url}")

    health_status = {
        "status": "online",
        "environment": app.config["FLASK_ENV"],
        "database": "connected",
        "database_url": database_url,
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
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

def create_app(test_config=None):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Configure the app
    configure_app(app, test_config)
    
    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": os.getenv('CORS_ORIGINS', 'http://localhost:3000')}})
    
    # Register routes
    register_routes(app)
    
    return app

def configure_app(app, test_config=None):
    """Configure application settings"""
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        GRAPH_DATA_DIR=os.getenv('GRAPH_DATA_DIR', './data/graphs'),
        DATABASE_URI=os.getenv('DATABASE_URI', 'sqlite:///data.db'),
        DEBUG=os.getenv('DEBUG', 'true').lower() == 'true',
        DATA_DIR=os.getenv('DATA_DIR', './data')  # Add DATA_DIR config
    )
    
    # Override with test config if provided
    if test_config:
        app.config.from_mapping(test_config)
    
    # Ensure graph data directory exists
    os.makedirs(app.config['GRAPH_DATA_DIR'], exist_ok=True)
    
    # Initialize graph manager with app config
    from .core.graph_manager import GraphManager
    app.graph_manager = GraphManager(config=app.config)

def register_routes(app):
    """Register application routes"""
    from .routes.graph_routes import graph_bp
    from .routes.component_routes import component_bp
    
    # Register all blueprints
    app.register_blueprint(graph_bp)
    app.register_blueprint(component_bp)

    @app.route('/api/health')
    def health_check():
        return jsonify({"status": "healthy"})

    @app.route('/api/dmr/analysis')
    def get_dmr_analysis():
        # Placeholder for DMR analysis endpoint
        return jsonify({
            "results": [
                {"id": 1, "status": "complete", "data": {}}
            ]
        })

if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'], port=int(os.getenv('PORT', 5000)))
