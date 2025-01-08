from .core.data_loader import validate_bipartite_graph, create_bipartite_graph
from .core.data_loader import process_enhancer_info
from .routes import graph_routes
from .core.graph_manager import GraphManager

# Add graph_manager to __all__
__all__ = [
    "create_bipartite_graph",
    "process_enhancer_info",
    "validate_bipartite_graph",
    "graph_routes",
    "graph_manager",
]

# Create global graph manager instance
graph_manager = GraphManager()
