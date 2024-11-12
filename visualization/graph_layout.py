"""Visualization-specific layout functionality"""

from typing import Dict, List, Set, Tuple
from .graph_layout_logical import (  # Updated import
    calculate_node_positions as core_calculate_positions,
    collect_node_information,
)
from .node_info import NodeInfo


def calculate_node_positions(
    bicliques: List[Tuple[Set[int], Set[int]]], node_biclique_map: Dict[int, List[int]]
) -> Dict[int, Tuple[float, float]]:
    """Calculate visualization-ready positions for nodes."""
    # Get base positions from core layout
    base_positions = core_calculate_positions(bicliques, node_biclique_map)

    # Apply visualization-specific transformations
    return adjust_positions_for_display(base_positions)


def adjust_positions_for_display(
    base_positions: Dict[int, Tuple[float, float]],
) -> Dict[int, Tuple[float, float]]:
    """Adjust node positions for display requirements."""
    display_positions = {}

    # Add padding and adjust coordinates for display
    padding = 0.1
    for node, (x, y) in base_positions.items():
        display_positions[node] = (
            x + padding,  # Add padding to x coordinate
            y * 1.2,  # Scale y coordinates for better spacing
        )

    return display_positions


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
