"""Core visualization functionality"""

import json
from typing import Dict, List, Set, Tuple
from plotly.utils import PlotlyJSONEncoder
import plotly.graph_objs as go
import plotly.colors

from .traces import (
    create_node_traces,
    create_edge_traces,
    create_biclique_boxes,
)

from .layout import create_visual_layout
from .traces import (
    create_node_traces,
    create_edge_traces,
    create_biclique_boxes,
)
from .node_info import NodeInfo


def generate_biclique_colors(num_bicliques: int) -> List[str]:
    """Generate distinct colors for bicliques"""
    colors = plotly.colors.qualitative.Set3 * (
        num_bicliques // len(plotly.colors.qualitative.Set3) + 1
    )
    return colors[:num_bicliques]


def create_biclique_visualization(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_labels: Dict[int, str],
    node_positions: Dict[int, Tuple[float, float]],
    node_biclique_map: Dict[int, List[int]],
    false_positive_edges: Set[Tuple[int, int]] = None,
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None,
) -> str:
    """Create interactive Plotly visualization with colored bicliques."""
    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(bicliques))

    traces = []

    # 1. Add biclique boxes first (background)
    box_traces = create_biclique_boxes(bicliques, node_positions, biclique_colors)
    traces.extend(box_traces)

    # 2. Add regular biclique edges
    edge_traces = create_edge_traces(
        bicliques, 
        node_positions, 
        edge_type="biclique",
        edge_style={"color": "gray", "width": 1}
    )
    traces.extend(edge_traces)

    # 3. Add false positive edges if provided
    if false_positive_edges:
        fp_traces = create_edge_traces(
            [(set([n1]), set([n2])) for n1, n2 in false_positive_edges],
            node_positions,
            edge_type="false_positive",
            edge_style={"color": "red", "width": 1, "dash": "dash"}
        )
        traces.extend(fp_traces)

    # 4. Create NodeInfo object for node categorization
    all_nodes = set().union(*[dmr_nodes | gene_nodes for dmr_nodes, gene_nodes in bicliques])
    dmr_nodes = set().union(*[dmr_nodes for dmr_nodes, _ in bicliques])
    gene_nodes = all_nodes - dmr_nodes
    split_genes = {node for node in gene_nodes if len(node_biclique_map.get(node, [])) > 1}
    regular_genes = gene_nodes - split_genes

    node_info = NodeInfo(
        all_nodes=all_nodes,
        dmr_nodes=dmr_nodes,
        regular_genes=regular_genes,
        split_genes=split_genes,
        node_degrees={node: len(node_biclique_map.get(node, [])) for node in all_nodes},
        min_gene_id=min(gene_nodes, default=0)
    )

    # 5. Add nodes with proper styling
    node_traces = create_node_traces(
        node_info, 
        node_positions, 
        node_labels, 
        node_biclique_map, 
        biclique_colors,
        dominating_set
    )
    traces.extend(node_traces)

    # Create layout
    layout = create_visual_layout(node_positions, node_info)

    # Create figure and convert to JSON
    fig = {"data": traces, "layout": layout}
    return json.dumps(fig, cls=PlotlyJSONEncoder)
