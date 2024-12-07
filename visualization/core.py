"""Core visualization functionality"""

import json
from typing import Dict, List, Set, Tuple
from plotly.utils import PlotlyJSONEncoder

# import plotly.graph_objs as go
import plotly.colors
import networkx as nx

from utils.node_info import NodeInfo
from utils.edge_info import EdgeInfo
from utils.graph_io import preprocess_graph_for_visualization

from .traces import (
    create_node_traces,
    create_edge_traces,
    create_biclique_boxes,
)

from .layout import create_visual_layout


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
    edge_classifications: Dict[str, List[EdgeInfo]],
    original_graph: nx.Graph,  # Required parameter moved up
    bipartite_graph: nx.Graph,  # Also make this required since it's needed
    original_node_positions: Dict[
        int, Tuple[float, float]
    ] = None,  # Optional parameters start here
    false_positive_edges: Set[Tuple[int, int]] = None,
    false_negative_edges: Set[Tuple[int, int]] = None,
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None,
    edge_classification: Dict[str, Set[Tuple[int, int]]] = None,
) -> str:
    """Create interactive Plotly visualization with colored bicliques."""
    print(f"\nCreating visualization for {len(bicliques)} bicliques")  # Debug logging

    # Preprocess graphs for visualization

    processed_original = preprocess_graph_for_visualization(
        original_graph, remove_isolates=True, remove_bridges=False, keep_dmrs=True
    )

    processed_bipartite = preprocess_graph_for_visualization(
        bipartite_graph, remove_isolates=True, remove_bridges=False, keep_dmrs=True
    )

    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(bicliques))

    traces = []

    # Add biclique boxes first (so they appear behind other elements)
    biclique_box_traces = create_biclique_boxes(
        bicliques, node_positions, biclique_colors
    )
    traces.extend(biclique_box_traces)

    # Determine which node positions to use
    positions = original_node_positions if original_node_positions else node_positions

    # Create edge traces with EdgeInfo using the appropriate positions
    edge_traces = create_edge_traces(
        edge_classifications,
        positions,  # Use the selected positions
        node_labels,  # Add this required argument
        original_graph,  # Add this required argument
        edge_style={"width": 1},
    )
    traces.extend(edge_traces)
    edge_traces = create_edge_traces(
        bicliques,
        positions,  # Use the selected positions
        node_labels,  # Add this required argument
        original_graph,  # Add this required argument
        false_positive_edges,
        false_negative_edges,
        edge_type="biclique",
        edge_style={"color": "black", "width": 1, "dash": "solid"},
    )
    traces.extend(edge_traces)

    # Create NodeInfo object for node categorization
    all_nodes = set().union(
        *[dmr_nodes | gene_nodes for dmr_nodes, gene_nodes in bicliques]
    )
    dmr_nodes = set().union(*[dmr_nodes for dmr_nodes, _ in bicliques])
    gene_nodes = all_nodes - dmr_nodes
    split_genes = {
        node for node in gene_nodes if len(node_biclique_map.get(node, [])) > 1
    }
    regular_genes = gene_nodes - split_genes

    node_info = NodeInfo(
        all_nodes=all_nodes,
        dmr_nodes=dmr_nodes,
        regular_genes=regular_genes,
        split_genes=split_genes,
        node_degrees={node: len(node_biclique_map.get(node, [])) for node in all_nodes},
        min_gene_id=min(gene_nodes, default=0),
    )

    # Add nodes with proper styling
    node_traces = create_node_traces(
        node_info,
        node_positions,
        node_labels,
        node_biclique_map,
        biclique_colors,
        dominating_set,
        dmr_metadata,  # Pass these parameters
        gene_metadata,
    )
    traces.extend(node_traces)

    # Create layout
    layout = create_visual_layout(node_positions, node_info)

    # Create figure and convert to JSON
    fig = {"data": traces, "layout": layout}

    print(f"Created visualization with {len(traces)} traces")  # Debug logging
    return json.dumps(fig, cls=PlotlyJSONEncoder)
