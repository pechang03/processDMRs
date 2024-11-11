"""Component visualization functionality"""

from typing import Dict, List, Set, Tuple
import json
from plotly.utils import PlotlyJSONEncoder

from .traces import create_node_traces, create_biclique_boxes, create_biclique_edges, create_false_positive_edges
from .layout import create_plot_layout
from .core import generate_biclique_colors
from node_info import NodeInfo

def create_component_visualization(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_labels: Dict[int, str],
    node_positions: Dict[int, Tuple[float, float]],
    node_biclique_map: Dict[int, List[int]],
    false_positive_edges: Set[Tuple[int, int]],
    node_info: NodeInfo,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None,
) -> str:
    """Create visualization for a component including false positive edges."""
    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(bicliques))

    traces = []
    
    # Add biclique boxes first (background)
    traces.extend(create_biclique_boxes(bicliques, node_positions, biclique_colors))
    
    # Add regular biclique edges
    traces.extend(create_biclique_edges(bicliques, node_positions))
    
    # Add false positive edges
    traces.extend(create_false_positive_edges(false_positive_edges, node_positions))
    
    # Add nodes with proper styling
    traces.extend(create_node_traces(
        node_info,
        node_positions,
        node_labels,
        node_biclique_map,
        biclique_colors
    ))

    # Create layout
    layout = create_plot_layout()

    # Create figure and convert to JSON
    fig = {"data": traces, "layout": layout}
    return json.dumps(fig, cls=PlotlyJSONEncoder)
