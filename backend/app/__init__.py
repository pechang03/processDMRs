from .core.data_loader import validate_bipartite_graph, create_bipartite_graph
from .core.data_loader import process_enhancer_info
from .routes import graph_routes
# from .routes.graph_routes import graph_bp

app.register_blueprint(graph_bp)

__all__ = [
    "create_bipartite_graph",
    "process_enhancer_info",
    "validate_bipartite_graph",
    "graph_routes",
]
