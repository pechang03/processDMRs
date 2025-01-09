from flask import Flask
from flask_cors import CORS

def create_app(test_config=None):
    """Application factory function"""
    app = Flask(__name__)
    
    # Import configuration function after app creation
    from .app import configure_app, register_routes
    
    # Configure app
    configure_app(app)
    
    # Register routes
    register_routes(app)
    
    return app

# Create default app instance
app = create_app()

__all__ = ["app", "create_app"]
