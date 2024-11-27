from flask import Blueprint

# Create blueprints for different route categories
main_bp = Blueprint('main', __name__)
stats_bp = Blueprint('stats', __name__)
components_bp = Blueprint('components', __name__)

# Import routes
from .main_routes import *
from .stats_routes import *
from .component_routes import *

# Register blueprints (this will be used in app.py)
def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(stats_bp, url_prefix='/statistics')
    app.register_blueprint(components_bp, url_prefix='/components')
from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
components_bp = Blueprint('components', __name__, url_prefix='/components')

# Import routes
from .main_routes import *
from .component_routes import *

def register_blueprints(app):
    """Register all blueprints with the app."""
    app.register_blueprint(main_bp)
    app.register_blueprint(components_bp)
