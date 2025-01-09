from flask import jsonify, current_app
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database.connection import get_db_engine
from .database.models import Timepoint
from .core.graph_manager import GraphManager
from flask import Flask
from flask_cors import CORS

from .routes.graph_routes import graph_bp
from .routes.component_routes import component_bp


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
    data_dir = os.getenv("DATA_DIR", os.path.join(project_root, "data"))
    graph_data_dir = os.getenv("GRAPH_DATA_DIR", os.path.join(data_dir, "graphs"))

    # Set configuration
    app.config.update(
        DATABASE_URL=f"sqlite:///{db_path}",
        FLASK_ENV=os.getenv("FLASK_ENV", "development"),
        DATA_DIR=data_dir,
        GRAPH_DATA_DIR=graph_data_dir,
        SECRET_KEY=os.getenv("SECRET_KEY", "dev"),
        DEBUG=os.getenv("DEBUG", "true").lower() == "true",
        CORS_ORIGINS=os.getenv("CORS_ORIGINS", "http://localhost:3000"),
    )

    # Ensure required directories exist
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    os.makedirs(app.config["GRAPH_DATA_DIR"], exist_ok=True)
    # database_url = f"sqlite:///{db_path}"

    # Set configuration
    app.graph_manager = GraphManager(config=app.config)

    # Initialize CORS
    CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})

    print("\n>>> FINAL CONFIGURATION:")
    print("-" * 30)
    print(f">>> Project root: {project_root}")
    print(f">>> Database URL: {app.config['DATABASE_URL']}")
    print(f">>> Environment: {app.config['FLASK_ENV']}")
    print(f">>> Data directory: {app.config['DATA_DIR']}")
    print(f">>> Graph data directory: {app.config['GRAPH_DATA_DIR']}")
    print("-" * 30)
    """Configure application settings"""

    # Initialize graph manager with app config
    print("\n>>> CONFIGURATION COMPLETE")
    print("*" * 50 + "\n")

    return env_loaded



def create_app(test_config=None):
    """Application factory function"""
    app = Flask(__name__)

    # Load environment variables from .env file if it exists
    # load_dotenv()

    # Configure the app
    configure_app(app)

    # Initialize extensions
    # CORS(
    #    app,
    #    resources={
    #        r"/*": {"origins": os.getenv("CORS_ORIGINS", "http://localhost:3000")}
    #    },
    # )

    # Register routes
    register_routes(app)

    return app


def register_routes(app):
    """Register application routes"""
    # Register all blueprints
    app.register_blueprint(graph_bp)
    app.register_blueprint(component_bp)

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

    @app.route("/api/graph-manager/status")
    def graph_manager_status():
        """Check GraphManager status"""
        try:
            graph_manager = current_app.graph_manager
            return jsonify(
                {
                    "status": "ok",
                    "initialized": graph_manager.is_initialized(),
                    "data_dir": graph_manager.data_dir,
                    "loaded_timepoints": list(graph_manager.original_graphs.keys()),
                }
            )
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500

    @app.route("/api/timepoints")
    def get_timepoints():
        """Get all timepoint names from the database."""
        engine = get_db_engine()
        with Session(engine) as session:
            timepoints = session.query(Timepoint.id, Timepoint.name).all()
            return jsonify([{"id": t.id, "name": t.name} for t in timepoints])

    @app.route("/api/dmr/analysis")
    def get_dmr_analysis():
        """Placeholder for DMR analysis endpoint"""
        return jsonify({"results": [{"id": 1, "status": "complete", "data": {}}]})


