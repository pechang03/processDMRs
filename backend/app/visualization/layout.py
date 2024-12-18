# File : layout.py
# Author : Peter Shaw
#
"""
Functions for visual layout of graph elements
"""

from typing import Dict, List, Set, Tuple
from backend.app.utils.node_info import NodeInfo
import plotly.graph_objs as go


def create_plot_layout() -> dict:
    """Create the plot layout configuration."""
    return {
        "showlegend": True,
        "hovermode": "closest",
        "margin": dict(b=40, l=40, r=40, t=40),
        "xaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
        "yaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
    }


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
