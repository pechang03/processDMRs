"""Visualization-specific layout functionality"""

from typing import Dict, List, Set, Tuple
from .graph_layout_logical import (  # Updated import
    calculate_node_positions as core_calculate_positions,
    collect_node_information,
    # position_nodes_by_biclique,  # Add this import
)
from backend.app.utils.node_info import NodeInfo


def calculate_node_positions(
    bicliques: List[Tuple[Set[int], Set[int]]], 
    node_biclique_map: Dict[int, List[int]],
    layout_type: str = "circular"
) -> Dict[int, Tuple[float, float]]:
    """Calculate visualization-ready positions for nodes."""
    # Get node information
    node_info = collect_node_information(bicliques, node_biclique_map)

    # Choose positioning method based on layout type
    if layout_type == "spring":
        # Use NetworkX spring layout for more dynamic positioning
        import networkx as nx
        import numpy as np
        
        # Create a graph from the bicliques
        G = nx.Graph()
        for dmr_nodes, gene_nodes in bicliques:
            G.add_nodes_from(dmr_nodes)
            G.add_nodes_from(gene_nodes)
            G.add_edges_from((dmr, gene) for dmr in dmr_nodes for gene in gene_nodes)
        
        # Use spring layout with seed for reproducibility
        base_positions = nx.spring_layout(
            G, 
            dim=2, 
            k=1/np.sqrt(len(G.nodes())),  # Adjust spacing
            iterations=50,
            seed=42  # For reproducibility
        )
    else:
        # Default to core positioning logic
        base_positions = core_calculate_positions(bicliques, node_biclique_map)

    # Apply any visualization-specific adjustments
    return adjust_positions_for_display(base_positions)


def adjust_positions_for_display(
    base_positions: Dict[int, Tuple[float, float]],
) -> Dict[int, Tuple[float, float]]:
    """Adjust node positions for display requirements."""
    # Return positions unchanged to preserve spacing
    return base_positions.copy()


def create_visual_layout(
    node_positions: Dict[int, Tuple[float, float]], node_info: NodeInfo
) -> Dict:
    """Create visual layout configuration for plotting."""
    return {
        "showlegend": True,
        "hovermode": "closest",
        "margin": dict(b=20, l=5, r=5, t=40),
        "annotations": [],
        "xaxis": create_axis_layout(),
        "yaxis": create_axis_layout(),
        "height": calculate_plot_height(node_positions),
        "width": 800,
    }


def create_axis_layout() -> Dict:
    """Create axis layout configuration."""
    return {
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "showline": False,
    }


def calculate_plot_height(node_positions: Dict[int, Tuple[float, float]]) -> int:
    """Calculate appropriate plot height based on node distribution."""
    if not node_positions:
        return 400
    y_positions = [y for _, y in node_positions.values()]
    y_range = max(y_positions) - min(y_positions)
    return max(400, int(y_range * 300))
