from flask import Flask
from .app import configure_app, register_routes

def create_app(test_config=None):
    """Application factory function"""
    app = Flask(__name__)
    
    # Configure app
    configure_app(app)
    
    # Apply test config if provided
    if test_config:
        app.config.update(test_config)
    
    # Register routes
    register_routes(app)
    
    return app

# Create default app instance
app = create_app()

__all__ = ["app", "create_app"]
