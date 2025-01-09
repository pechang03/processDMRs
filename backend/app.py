import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

def configure_app(app, test_config=None):
    """Configure application settings"""
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        GRAPH_DATA_DIR=os.getenv('GRAPH_DATA_DIR', './data/graphs'),
        DATABASE_URI=os.getenv('DATABASE_URI', 'sqlite:///data.db'),
        DEBUG=os.getenv('DEBUG', 'true').lower() == 'true'
    )
    
    # Override with test config if provided
    if test_config:
        app.config.from_mapping(test_config)
    
    # Ensure graph data directory exists
    os.makedirs(app.config['GRAPH_DATA_DIR'], exist_ok=True)
    
    # Initialize graph manager
    from backend.app.core.graph_manager import GraphManager
    app.graph_manager = GraphManager()
    
    # Initialize CORS
    CORS(app, resources={r"/*": {"origins": os.getenv('CORS_ORIGINS', 'http://localhost:3000')}})

def register_routes(app):
    """Register application routes"""
    from backend.app.routes.graph_routes import graph_bp
    from backend.app.routes.component_routes import component_bp
    
    # Register all blueprints
    app.register_blueprint(graph_bp)
    app.register_blueprint(component_bp)

    @app.route('/api/health')
    def health_check():
        return jsonify({"status": "healthy"})

    @app.route('/api/dmr/analysis')
    def get_dmr_analysis():
        return jsonify({
            "results": [
                {"id": 1, "status": "complete", "data": {}}
            ]
        })

