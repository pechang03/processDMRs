# File biclique visualization.py
# Author: Peter Shaw 
# Date: 5/6/2019
#

"""
 Functions for creating biclique visualizations using Plotly
"""

import plotly.graph_objs as go
import json
from plotly.utils import PlotlyJSONEncoder
from typing import Dict, List, Set, Tuple

def create_biclique_visualization(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_labels: Dict[int, str],
    node_positions: Dict[int, Tuple[float, float]],
    node_biclique_map: Dict[int, List[int]],
    split_positions: Dict[int, List[Tuple[float, float]]] = None,
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None,
) -> str:

    """
    Create interactive Plotly visualization with colored bicliques.
    """
    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(bicliques))

    edge_traces = []
    node_traces = []
    box_traces = []  # For biclique boxes

    # Track node colors based on biclique membership
    node_colors = {}

    # Process each biclique
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques color = biclique_colors[biclique_idx]

        # Create edges
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                edge_traces.append(
                    go.Scatter(
                        x=[node_positions[dmr][0], node_positions[gene][0]],
                        y=[node_positions[dmr][1], node_positions[gene][1]],
                        mode="lines",
                        line=dict(width=1, color="gray"),
                        hoverinfo="none",
                        showlegend=False,
                    )
                )

        # Update node colors
        for node in dmr_nodes | gene_nodes:
            node_colors[node] = color

        # Create box around biclique
        nodes = dmr_nodes | gene_nodes
        if nodes:
            x_coords = [node_positions[n][0] for n in nodes]
            y_coords = [node_positions[n][1] for n in nodes]

            # Add padding around the box
            padding = 0.05
            x_min, x_max = min(x_coords) - padding, max(x_coords) + padding
            y_min, y_max = min(y_coords) - padding, max(y_coords) + padding

            box_traces.append(
                go.Scatter(
                    x=[x_min, x_max, x_max, x_min, x_min],
                    y=[y_min, y_min, y_max, y_max, y_min],
                    mode="lines",
                    line=dict(color=color, width=2, dash="dot"),
                    fill="toself",
                    fillcolor=color,
                    opacity=0.1,
                    name=f"Biclique {biclique_idx + 1}",
                    showlegend=True,
                )
            )

    # Create node traces with biclique colors
    dmr_x, dmr_y, dmr_colors, dmr_text = [], [], [], []
    gene_x, gene_y, gene_colors, gene_text = [], [], [], []

    for node_id, pos in node_positions.items():
        color = node_colors.get(node_id, "gray")
        if node_id in node_biclique_map:  # It's a valid node
            is_dmr = any(node_id in dmr_nodes for dmr_nodes, _ in
bicliques)
            if is_dmr:
                dmr_x.append(pos[0])
                dmr_y.append(pos[1])
                dmr_colors.append(color)
                dmr_text.append(node_labels.get(node_id,
f"DMR_{node_id}"))
            else:
                gene_x.append(pos[0])
                gene_y.append(pos[1])
                gene_colors.append(color)
                gene_text.append(node_labels.get(node_id,
f"Gene_{node_id}"))

    # Add DMR nodes
    node_traces.append(
        go.Scatter(
            x=dmr_x,
            y=dmr_y,
            mode="markers+text",
            marker=dict(size=10, color=dmr_colors, line=dict(color="black", width=1)),
            text=dmr_text,
            textposition="middle left",
            hoverinfo="text",
            name="DMRs",
        )
    )

    # Add gene nodes
    node_traces.append(
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
        )
    )

    # Add hub nodes if provided
    if dominating_set:
        hub_x, hub_y, hub_text = [], [], []
        for node in dominating_set:
            if node in node_positions:
                hub_x.append(node_positions[node][0])
                hub_y.append(node_positions[node][1])
                hub_text.append(f"{node_labels.get(node, f'DMR_{node}')} (Hub)")

        node_traces.append(
            go.Scatter(
                x=hub_x,
                y=hub_y,
                mode="markers+text",
                marker=dict(
                    size=15,
                    color="gold",
                    symbol="star",
                    line=dict(color="orange", width=2),
                ),
                text=hub_text,
                textposition="middle left",
                hoverinfo="text",
                name="Hub DMRs",
            )
        )

    # Combine all traces in the right order (boxes first, then edges then nodes)
    plot_data = box_traces + edge_traces + node_traces
    layout = go.Layout(
        showlegend=True,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h")
    )

    fig = go.Figure(data=plot_data, layout=layout)
    return json.dumps(fig, cls=PlotlyJSONEncoder)

def generate_biclique_colors(num_bicliques: int) -> List[str]:
    """Generate distinct colors for bicliques"""
    import plotly.colors

    colors = plotly.colors.qualitative.Set3 * (
        num_bicliques // len(plotly.colors.qualitative.Set3) + 1
    )
    return colors[:num_bicliques]
"""
Functions for creating biclique visualizations using Plotly
"""

import plotly.graph_objs as go
import json
from plotly.utils import PlotlyJSONEncoder
from typing import Dict, List, Set, Tuple


def generate_biclique_colors(num_bicliques: int) -> List[str]:
    """Generate distinct colors for bicliques"""
    import plotly.colors

    colors = plotly.colors.qualitative.Set3 * (
        num_bicliques // len(plotly.colors.qualitative.Set3) + 1
    )
    return colors[:num_bicliques]
