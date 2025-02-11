from flask import jsonify, current_app
import os
from .utils.extensions import app
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database.connection import get_db_engine
from .database.models import Timepoint
from .routes.component_routes import component_bp
from .core.graph_manager import GraphManager
from flask_cors import CORS

def configure_app(app):
    """Configure application settings"""
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

    # Get paths from environment file
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
        CORS_ORIGINS=os.getenv("CORS_ORIGINS", "http://localhost:3000")
    )

    # Ensure required directories exist
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    os.makedirs(app.config["GRAPH_DATA_DIR"], exist_ok=True)

    # Initialize graph manager with app config
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

    print("\n>>> CONFIGURATION COMPLETE")
    print("*" * 50 + "\n")

    return env_loaded


def register_routes(app):
    """Register application routes"""
    from .routes.graph_routes import graph_bp
    
    # Register blueprints
    app.register_blueprint(graph_bp)
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
                "loaded_timepoints": list(graph_manager.original_graphs.keys()),
            })
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500

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
        print("\n>>> Accessing /api/timepoints endpoint")
        engine = get_db_engine()
        db_path = app.config["DATABASE_URL"].replace("sqlite:///", "")
        print(f">>> Successfully connected to database at: {db_path}")
        
        with Session(engine) as session:
            # Log the query being executed
            query = session.query(Timepoint.id, Timepoint.name)
            print(f">>> Executing query: {str(query)}")
            
            # Get all timepoints
            timepoints = query.all()
            print(f">>> Found {len(timepoints)} timepoints in database")
            
            # Log details of first timepoint if available
            if timepoints:
                first = timepoints[0]
                print(f">>> First timepoint: id={first.id}, name='{first.name}'")
            else:
                print(">>> No timepoints found in database")
            
            # Create result list
            result = [{"id": t.id, "name": t.name} for t in timepoints]
            print(f">>> Returning: {result}")
            return jsonify(result)

    @app.route("/api/timepoints/<int:timepoint_id>")
    def get_timepoint(timepoint_id):
        """Get a specific timepoint by ID including its associated graph data."""
        engine = get_db_engine()
        with Session(engine) as session:
            timepoint = session.query(Timepoint).filter(Timepoint.id == timepoint_id).first()
            if timepoint is None:
                return jsonify({"error": "Timepoint not found"}), 404
            
            # Get graph data from GraphManager
            response_data = {
                "id": timepoint.id,
                "name": timepoint.name,
                "graph_data": None
            }
            
            try:
                graph_manager = current_app.graph_manager
                if graph_manager and timepoint.name in graph_manager.split_graphs:
                    response_data["graph_data"] = graph_manager.split_graphs[timepoint.name]
            except Exception as e:
                print(f"Error retrieving graph data: {str(e)}")
                # Don't fail the whole request if graph data is unavailable
                response_data["graph_error"] = str(e)
            
            return jsonify(response_data)


# Remove the direct configure_app(app) call from here

if __name__ == "__main__":
    # Create app instance and run
    from . import create_app
    app = create_app()
    port = int(os.getenv("FLASK_PORT", 5555))
    app.run(host="0.0.0.0", port=port, debug=True)

