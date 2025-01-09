from flask import Flask

app = Flask(__name__)

from .app import configure_app, register_routes

configure_app(app)
register_routes(app)

__all__ = ["app"]
