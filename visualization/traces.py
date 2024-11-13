# File: traces.py
# Author: Peter Shaw
#

"""Node trace creation functionality"""

from typing import Dict, List, Set, Tuple
import plotly.graph_objs as go
from .node_info import NodeInfo


def create_node_traces(
    node_info: NodeInfo,
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    biclique_colors: List[str],
) -> List[go.Scatter]:
    """Create node traces with proper styling based on node type."""
    traces = []

    # Create DMR nodes trace
    dmr_x = []
    dmr_y = []
    dmr_text = []
    dmr_colors = []

    # Create gene nodes trace
    gene_x = []
    gene_y = []
    gene_text = []
    gene_colors = []

    for node_id, (x, y) in node_positions.items():
        color = "gray"
        label = node_labels.get(node_id, str(node_id))
        if (
            node_id in node_biclique_map and biclique_colors
        ):  # Check if colors list is not empty
            biclique_idx = node_biclique_map[node_id][0]  # Use the first biclique index
            if biclique_idx < len(biclique_colors):  # Check if index is valid
                color = biclique_colors[biclique_idx]
            else:
                color = "gray"  # Use gray for invalid biclique numbers

        if node_id in node_info.dmr_nodes:
            dmr_x.append(x)
            dmr_y.append(y)
            dmr_text.append(label)
            dmr_colors.append(color)
        else:
            gene_x.append(x)
            gene_y.append(y)
            gene_text.append(label)
            gene_colors.append(color)

    # Add DMR nodes
    if dmr_x:
        traces.append(
            go.Scatter(
                x=dmr_x,
                y=dmr_y,
                mode="markers+text",
                marker=dict(
                    size=10,
                    color=dmr_colors,
                    symbol="circle",
                    line=dict(color="black", width=1),
                ),
                text=dmr_text,
                textposition="middle left",
                hoverinfo="text",
                name="DMRs",
                showlegend=True,
            )
        )

    # Add gene nodes
    if gene_x:
        traces.append(
            go.Scatter(
                x=gene_x,
                y=gene_y,
                mode="markers+text",
                marker=dict(
                    size=10,
                    color=gene_colors,
                    symbol="diamond",
                    line=dict(color="black", width=1),
                ),
                text=gene_text,
                textposition="middle right",
                hoverinfo="text",
                name="Genes",
                showlegend=True,
            )
        )

    return traces


def create_edge_traces(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_positions: Dict[int, Tuple[float, float]],
    edge_type: str = "biclique",  # Add this parameter
    edge_style: Dict = None  # Add this parameter
) -> List[go.Scatter]:
    """Create edge traces with configurable style."""
    traces = []
    default_style = {
        "width": 1,
        "color": "gray",
        "dash": "solid"
    }
    style = {**default_style, **(edge_style or {})}
    
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                if dmr in node_positions and gene in node_positions:
                    traces.append(
                        go.Scatter(
                            x=[node_positions[dmr][0], node_positions[gene][0]],
                            y=[node_positions[dmr][1], node_positions[gene][1]],
                            mode="lines",
                            line=dict(**style),
                            hoverinfo="none",
                            showlegend=False,
                        )
                    )
    return traces


def create_biclique_boxes(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_positions: Dict[int, Tuple[float, float]],
    biclique_colors: List[str],
) -> List[go.Scatter]:
    """Create box traces around bicliques."""
    traces = []
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        nodes = dmr_nodes | gene_nodes
        if not nodes:
            continue

        positions = []
        for node in nodes:
            if node in node_positions:
                positions.append(node_positions[node])
            else:
                print(f"Position not found for node {node}")
        if not positions:
            continue  # Skip if no positions are found
        x_coords, y_coords = zip(*positions)

        padding = 0.05
        x_min, x_max = min(x_coords) - padding, max(x_coords) + padding
        y_min, y_max = min(y_coords) - padding, max(y_coords) + padding

        traces.append(
            go.Scatter(
                x=[x_min, x_max, x_max, x_min, x_min],
                y=[y_min, y_min, y_max, y_max, y_min],
                mode="lines",
                line=dict(color=biclique_colors[biclique_idx], width=2, dash="dot"),
                fill="toself",
                fillcolor=biclique_colors[biclique_idx],
                opacity=0.1,
                name=f"Biclique {biclique_idx + 1}",
                showlegend=True,
            )
        )
    return traces




