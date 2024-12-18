"""Flask application for DMR analysis database visualization."""

import os
import argparse

# from extensions import app
from flask import Flask, send_from_directory, jsonify
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database.connection import get_db_engine
from database.models import (
    Component,
    Biclique,
    Timepoint,
)
from visualization.core import create_component_visualization
from routes import register_blueprints

# Version constant
__version__ = "0.0.5-alpha"

# Initialize Flask app
from extensions import app


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)


@app.route("/api/timepoints")
def get_timepoints():
    """Get list of all timepoints."""
    engine = get_db_engine()
    with Session(engine) as session:
        timepoints = session.query(Timepoint).all()
        return jsonify(
            [
                {"id": t.id, "name": t.name, "description": t.description}
                for t in timepoints
            ]
        )


@app.route("/api/timepoint/<int:timepoint_id>/components")
def get_timepoint_components(timepoint_id):
    """Get components for a specific timepoint."""
    engine = get_db_engine()
    with Session(engine) as session:
        components = session.query(Component).filter_by(timepoint_id=timepoint_id).all()
        return jsonify(
            [
                {
                    "id": c.id,
                    "graph_type": c.graph_type,
                    "category": c.category,
                    "size": c.size,
                    "dmr_count": c.dmr_count,
                    "gene_count": c.gene_count,
                    "edge_count": c.edge_count,
                    "density": c.density,
                }
                for c in components
            ]
        )


@app.route("/api/component/<int:component_id>")
def get_component(component_id):
    """Get detailed information about a specific component."""
    engine = get_db_engine()
    with Session(engine) as session:
        component = session.query(Component).get(component_id)
        if not component:
            return jsonify({"error": "Component not found"}), 404

        bicliques = session.query(Biclique).filter_by(component_id=component_id).all()

        return jsonify(
            {
                "id": component.id,
                "graph_type": component.graph_type,
                "category": component.category,
                "size": component.size,
                "dmr_count": component.dmr_count,
                "gene_count": component.gene_count,
                "edge_count": component.edge_count,
                "density": component.density,
                "bicliques": [
                    {
                        "id": b.id,
                        "category": b.category,
                        "dmr_count": len(b.dmr_ids),
                        "gene_count": len(b.gene_ids),
                    }
                    for b in bicliques
                ],
            }
        )


@app.route("/api/component/<int:component_id>/visualization")
def get_component_visualization(component_id):
    """Get visualization data for a specific component."""
    try:
        engine = get_db_engine()
        with Session(engine) as session:
            vis_data = create_component_visualization(
                component_id=component_id,
                session=session,
                layout_type="circular",  # Could make this configurable via query param
            )
            return jsonify({"visualization": vis_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def validate_data_files(data_dir: str) -> bool:
    """Validate that required data files exist."""
    dss1_path = os.path.join(data_dir, "DSS1.xlsx")
    pairwise_path = os.path.join(data_dir, "DSS_PAIRWISE.xlsx")

    files_exist = True
    if not os.path.exists(dss1_path):
        print(f"Error: DSS1.xlsx not found in {data_dir}")
        files_exist = False
    if not os.path.exists(pairwise_path):
        print(f"Error: DSS_PAIRWISE.xlsx not found in {data_dir}")
        files_exist = False

    return files_exist


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DMR Analysis Database Visualization",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Port to run the web server on"
    )
    parser.add_argument(
        "--format",
        choices=["gene-name", "number"],
        default="gene-name",
        help="Format for biclique file parsing (gene-name or number)",
    )
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="Directory containing DSS1.xlsx and DSS_PAIRWISE.xlsx",
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    return parser.parse_args()


def configure_data_paths(data_dir: str):
    """Configure data file paths in the application."""
    global DSS1_FILE, DSS_PAIRWISE_FILE
    DSS1_FILE = os.path.join(data_dir, "DSS1.xlsx")
    DSS_PAIRWISE_FILE = os.path.join(data_dir, "DSS_PAIRWISE.xlsx")

    app.config["DSS1_FILE"] = DSS1_FILE
    app.config["DSS_PAIRWISE_FILE"] = DSS_PAIRWISE_FILE
    app.config["DATA_DIR"] = data_dir


def configure_app(app):
    """Configure Flask application."""
    # First try sample.env, then fall back to .env files
    env_files = ["sample.env", "../sample.env", "../../sample.env"]
    env_loaded = False

    # for env_file in env_files:
    #    if os.path.exists(env_file):
    #        print(f"Loading configuration from {env_file}")
    #        load_dotenv(env_file)
    #        env_loaded = True
    #        break

    if not env_loaded:
        print("Warning: No environment file found, using defaults")

    # Set default configuration
    app.config.setdefault("DATABASE_URL", "sqlite:///dmr_analysis.db")
    app.config.setdefault("FLASK_ENV", "development")
    app.config.setdefault("DATA_DIR", "./data")

    # Override with environment variables if they exist
    app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", app.config["DATABASE_URL"])
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", app.config["FLASK_ENV"])
    app.config["DATA_DIR"] = os.getenv("DATA_DIR", app.config["DATA_DIR"])

    # Set data file paths from environment variables, using DATA_DIR
    data_dir = app.config["DATA_DIR"]
    app.config["DSS1_FILE"] = os.getenv(
        "DSS1_FILE", os.path.join(data_dir, "DSS1.xlsx")
    )
    app.config["DSS_PAIRWISE_FILE"] = os.getenv(
        "DSS_PAIRWISE_FILE", os.path.join(data_dir, "DSS_PAIRWISE.xlsx")
    )

    print(f"Configured data files:")
    print(f"DSS1_FILE: {app.config['DSS1_FILE']}")
    print(f"DSS_PAIRWISE_FILE: {app.config['DSS_PAIRWISE_FILE']}")

    # Configure static files path
    app.static_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "static"
    )

    # Add MIME type handling
    app.config["MIME_TYPES"] = {".css": "text/css", ".js": "application/javascript"}


load_dotenv("processDMR.env")


def main():
    """Main entry point for the application."""
    args = parse_arguments()

    # Validate and configure data paths
    if not validate_data_files(args.data_dir):
        print("Error: Required data files not found. Please check your data directory.")
        return 1

    # Configure data paths
    configure_data_paths(args.data_dir)

    # Store format in app config
    app.config["BICLIQUE_FORMAT"] = args.format

    # Configure the Flask app
    configure_app(app)

    # Add this line to configure static files path
    app.static_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "static"
    )
    # Register blueprints
    register_blueprints(app)

    # Debug: Print registered routes
    print("\nRegistered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

    # Add MIME type handling
    app.config["MIME_TYPES"] = {".css": "text/css", ".js": "application/javascript"}

    # Run the Flask app
    app.run(debug=args.debug, port=args.port)
    return 0


if __name__ == "__main__":
    exit(main())
