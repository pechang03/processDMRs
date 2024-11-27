from flask import Blueprint

main_bp = Blueprint('main', __name__)
components_bp = Blueprint('components', __name__)

# Import routes after blueprint creation to avoid circular imports
from . import main_routes
from . import component_routes
