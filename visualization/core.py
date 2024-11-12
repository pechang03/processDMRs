"""Core visualization functionality"""

import json
from typing import Dict, List, Set, Tuple
from plotly.utils import PlotlyJSONEncoder
import plotly.graph_objs as go

from .traces import create_node_traces, create_edge_traces
from .layout import create_plot_layout
import plotly.colors
from .traces import create_node_traces, create_biclique_boxes, create_biclique_edges, create_false_positive_edges
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
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None,
) -> str:
    """Create interactive Plotly visualization with colored bicliques."""
    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(bicliques))

    # Create NodeInfo object
    all_nodes = set().union(*[dmr_nodes | gene_nodes for dmr_nodes, gene_nodes in bicliques])
    dmr_nodes = set().union(*[dmr_nodes for dmr_nodes, _ in bicliques])
    regular_genes = set().union(*[gene_nodes for _, gene_nodes in bicliques])
    split_genes = {node for node in regular_genes 
                  if len(node_biclique_map.get(node, [])) > 1}
    regular_genes -= split_genes
    
    node_degrees = {node: len(node_biclique_map.get(node, [])) 
                   for node in all_nodes}
    min_gene_id = min(regular_genes | split_genes, default=0)

    node_info = NodeInfo(
        all_nodes=all_nodes,
        dmr_nodes=dmr_nodes,
        regular_genes=regular_genes,
        split_genes=split_genes,
        node_degrees=node_degrees,
        min_gene_id=min_gene_id
    )

    # Create all visualization elements
    traces = []
    
    # Add edges first (background)
    for dmr_nodes, gene_nodes in bicliques:
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                traces.append(go.Scatter(
                    x=[node_positions[dmr][0], node_positions[gene][0]],
                    y=[node_positions[dmr][1], node_positions[gene][1]],
                    mode="lines",
                    line=dict(color="gray", width=1),
                    hoverinfo="none",
                    showlegend=False
                ))
    
    # Add biclique boxes
    traces.extend(create_biclique_boxes(bicliques, node_positions, biclique_colors))
    
    # Add edges first (background)
    traces.extend(create_edge_traces(bicliques, node_positions))
    
    # Add nodes with proper styling
    traces.extend(create_node_traces(
        node_info,
        node_positions,
        node_labels,
        node_biclique_map,
        biclique_colors
    ))

    # Create layout with proper spacing
    layout = {
        "showlegend": True,
        "hovermode": "closest",
        "margin": dict(b=40, l=40, r=40, t=40),
        "xaxis": dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.2, 1.3]  # Adjust range to prevent cutoff
        ),
        "yaxis": dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1
        ),
        "height": max(400, len(all_nodes) * 30),  # Dynamic height based on node count
        "width": 800
    }

    # Create figure and convert to JSON
    fig = {"data": traces, "layout": layout}
    return json.dumps(fig, cls=PlotlyJSONEncoder)
