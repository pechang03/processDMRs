from flask import Flask
from .app import configure_app, register_routes

app = Flask(__name__)

configure_app(app)
register_routes(app)

__all__ = ["app"]
