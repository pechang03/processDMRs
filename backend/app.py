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
        DEBUG=os.getenv('DEBUG', 'true').lower() == 'true'
    )
    
    # Override with test config if provided
    if test_config:
        app.config.from_mapping(test_config)
    
    # Ensure graph data directory exists
    os.makedirs(app.config['GRAPH_DATA_DIR'], exist_ok=True)
    
    # Initialize graph manager
    from .core.graph_manager import GraphManager
    app.graph_manager = GraphManager()

def register_routes(app):
    """Register application routes"""
    from .routes.graph_routes import graph_bp
    app.register_blueprint(graph_bp)

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

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], port=int(os.getenv('PORT', 5000)))

