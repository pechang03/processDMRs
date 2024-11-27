"""Utilities package"""

from flask import Blueprint

# Create blueprints for different route categories
main_bp = Blueprint("main", __name__)
stats_bp = Blueprint("stats", __name__, url_prefix="/statistics")
components_bp = Blueprint("components", __name__, url_prefix="/components")

def register_blueprints(app):
    """Register all blueprints with the app."""
    app.register_blueprint(main_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(components_bp)

# Import routes after blueprint creation to avoid circular imports
from . import main_routes
from . import component_routes
from . import stats_routes
