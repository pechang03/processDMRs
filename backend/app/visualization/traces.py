# File: traces.py
# Author: Peter Shaw
#

"""Node trace creation functionality"""

import os
from typing import Dict, List, Set, Tuple, Union, Any
from backend.app.utils.edge_info import (
    EdgeInfo,
)  # Changed from biclique_analysis.edge_info
import plotly.graph_objs as go
import networkx as nx  # Add this line
from backend.app.utils.node_info import NodeInfo
# from utils import get_node_position  # Add this import


def create_node_traces(
    node_info: NodeInfo,
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    biclique_colors: List[str],
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
) -> List[go.Scatter]:
    """Create node traces with consistent styling."""
    traces = []
    import math

    # Filter out nodes with degree 0 in original graph
    nodes_to_show = {node for node in node_info.all_nodes 
                     if node_info.get_node_degree(node) > 0}

    def get_text_position(x: float, y: float) -> str:
        """
        Determine text position based on node's quadrant position.

        Quadrants:
        Q2 | Q1     0° is at 3 o'clock position
        ---|---     Q2 & Q3: text on left (x < 0)
        Q3 | Q4     Q1 & Q4: text on right (x > 0)
        """
        # Simply check if x is positive (right half) or negative (left half)
        return "middle right" if x > 0 else "middle left"

    # Helper function to create transparent version of color
    def make_transparent(color: str, alpha: float = 0.6) -> str:
        if color.startswith("#"):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            return f"rgba({r},{g},{b},{alpha})"
        return color

    # Create DMR trace - only for nodes with degree > 0
    dmr_x, dmr_y, dmr_colors, dmr_text_positions = [], [], [], []
    for node in node_info.dmr_nodes:
        if node in node_positions and node in nodes_to_show:  # Added check for nodes_to_show
            x, y = node_positions[node]
            dmr_x.append(x)
            dmr_y.append(y)
            biclique_idx = node_biclique_map.get(node, [0])[0]
            dmr_colors.append(biclique_colors[biclique_idx % len(biclique_colors)])
            dmr_text_positions.append(get_text_position(x, y))

    if dmr_x:
        traces.append(
            go.Scatter(
                x=dmr_x,
                y=dmr_y,
                mode="markers+text",
                marker=dict(
                    size=12,
                    color=dmr_colors,
                    symbol="circle",
                    line=dict(color="black", width=1),
                ),
                text=[
                    node_labels.get(n)
                    for n in node_info.dmr_nodes
                    if n in node_positions
                ],
                textposition=dmr_text_positions,  # Use calculated positions
                name="DMRs",
            )
        )

    # Create gene trace - only for nodes with degree > 0
    gene_x, gene_y, gene_colors, gene_text_positions = [], [], [], []
    for node in node_info.regular_genes | node_info.split_genes:
        if node in node_positions and node in nodes_to_show:  # Added check for nodes_to_show
            x, y = node_positions[node]
            gene_x.append(x)
            gene_y.append(y)
            biclique_idx = node_biclique_map.get(node, [0])[0]
            color = biclique_colors[biclique_idx % len(biclique_colors)]
            gene_colors.append(make_transparent(color))
            gene_text_positions.append(get_text_position(x, y))

    if gene_x:
        traces.append(
            go.Scatter(
                x=gene_x,
                y=gene_y,
                mode="markers+text",
                marker=dict(
                    size=10,
                    color=gene_colors,
                    symbol="circle",
                    line=dict(color="black", width=1),
                ),
                text=[
                    node_labels.get(n)
                    for n in (node_info.regular_genes | node_info.split_genes)
                    if n in node_positions
                ],
                textposition=gene_text_positions,  # Use calculated positions
                name="Genes",
            )
        )

    return traces


def create_gene_trace(
    gene_nodes: Set[int],
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    biclique_colors: List[str],
    gene_metadata: Dict[str, Dict] = None,
    textposition: str = "middle right",
) -> go.Scatter:
    """Create trace for regular gene nodes."""
    # Add at start of function:
    if not gene_nodes or not node_positions:
        return None

    x = []
    y = []
    text = []
    hover_text = []
    colors = []

    # Process regular genes
    for node_id in sorted(gene_nodes):
        position = node_positions.get(node_id)
        if not position or not isinstance(position, tuple) or len(position) != 2:
            continue

        x_pos, y_pos = position
        x.append(x_pos)
        y.append(y_pos)

        # Set node color based on biclique membership
        if node_id in node_biclique_map and node_biclique_map[node_id]:
            biclique_idx = node_biclique_map[node_id][0]  # Use first biclique for color
            color = biclique_colors[biclique_idx % len(biclique_colors)]
        else:
            color = "gray"
        colors.append(color)

        # Create label and hover text
        label = node_labels.get(node_id, str(node_id))
        text.append(label)

        # Add metadata to hover text
        meta = gene_metadata.get(label, {}) if gene_metadata else {}
        hover = f"{label}<br>Description: {meta.get('description', 'N/A')}"
        hover_text.append(hover)

    if not x:  # Return None if no nodes to show
        return None

    return go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        marker=dict(
            size=10,
            color=colors,
            symbol="circle",
            line=dict(color="black", width=1),
        ),
        text=text,
        hovertext=hover_text,
        textposition=textposition,
        hoverinfo="text",
        name="Regular Genes",
        showlegend=True,
    )


def create_split_gene_trace(
    split_genes: Set[int],
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    biclique_colors: List[str],
    gene_metadata: Dict[str, Dict] = None,
    textposition: str = "middle right",
) -> go.Scatter:
    """Create trace for split gene nodes."""
    x = []
    y = []
    text = []
    hover_text = []
    colors = []

    # Process split genes
    for node_id in sorted(split_genes):
        position = node_positions.get(node_id)
        if not position or not isinstance(position, tuple) or len(position) != 2:
            continue

        x_pos, y_pos = position
        x.append(x_pos)
        y.append(y_pos)

        # Set node color based on first biclique membership
        if node_id in node_biclique_map and node_biclique_map[node_id]:
            biclique_idx = node_biclique_map[node_id][0]
            base_color = biclique_colors[biclique_idx % len(biclique_colors)]
            # Convert to rgba with transparency
            if base_color.startswith("#"):
                r = int(base_color[1:3], 16)
                g = int(base_color[3:5], 16)
                b = int(base_color[5:7], 16)
                color = f"rgba({r},{g},{b},0.6)"
            else:
                color = base_color
        else:
            color = "rgba(128,128,128,0.6)"  # transparent gray
        colors.append(color)

        # Create label and hover text
        label = node_labels.get(node_id, str(node_id))
        text.append(label)

        # Add metadata to hover text
        meta = gene_metadata.get(label, {}) if gene_metadata else {}
        bicliques_str = ", ".join(map(str, node_biclique_map.get(node_id, [])))
        hover = f"{label}<br>Description: {meta.get('description', 'N/A')}<br>Bicliques: {bicliques_str}"
        hover_text.append(hover)

    if not x:  # Return None if no nodes to show
        return None

    return go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        marker=dict(
            size=12,  # Slightly larger than regular genes
            color=colors,
            symbol=NODE_SHAPES["gene"]["split"],  # Use centralized shape config
            line=dict(color="black", width=2),  # Thicker border
        ),
        text=text,
        hovertext=hover_text,
        textposition=textposition,
        hoverinfo="text",
        name="Split Genes",
        showlegend=True,
    )


# Centralized node shape configuration
NODE_SHAPES = {
    "dmr": {
        "regular": "octagon",  # Changed from "circle" to "octagon"
        "hub": "star"
    },
    "gene": {
        "regular": "circle",
        "split": "diamond"
    }
}

def create_dmr_trace(
    dmr_nodes: Set[int],
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    biclique_colors: List[str],
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
) -> go.Scatter:
    """Create trace for DMR nodes."""
    if not dmr_nodes or not node_positions:
        return None

    x = []
    y = []
    text = []
    hover_text = []
    colors = []
    sizes = []
    symbols = []

    # Convert dominating_set to empty set if None
    dominating_set = dominating_set or set()

    for node_id in sorted(dmr_nodes):
        if node_id not in node_positions:
            continue

        x_pos, y_pos = node_positions[node_id]
        x.append(x_pos)
        y.append(y_pos)

        # Set node color based on biclique membership
        if node_id in node_biclique_map and node_biclique_map.get(node_id, []):
            biclique_idx = node_biclique_map[node_id][0]
            color = (
                biclique_colors[biclique_idx % len(biclique_colors)]
                if biclique_colors and biclique_idx < len(biclique_colors)
                else "gray"
            )
        else:
            color = "gray"
        colors.append(color)

        # Use centralized shape configuration
        is_hub = node_id in dominating_set
        sizes.append(15 if is_hub else 10)
        symbols.append(NODE_SHAPES["dmr"]["hub"] if is_hub else NODE_SHAPES["dmr"]["regular"])

        # Create label and hover text
        label = node_labels.get(node_id, str(node_id))
        text.append(label)

        # Add metadata to hover text
        meta = dmr_metadata.get(str(node_id), {}) if dmr_metadata else {}
        hover = f"{label}<br>Area: {meta.get('area', 'N/A')}"
        if is_hub:
            hover += "<br>(Hub Node)"
        hover_text.append(hover)

    if not x:
        return None

    return go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        marker=dict(
            size=sizes,
            color=colors,
            symbol=symbols,
            line=dict(color="black", width=1),
        ),
        text=text,
        hovertext=hover_text,
        textposition="middle left",
        hoverinfo="text",
        name="DMR Nodes",
        showlegend=True,
    )


def create_edge_traces(
    edge_classifications: Dict[str, List[EdgeInfo]],
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    original_graph: nx.Graph,
    edge_style: Dict = None,
) -> List[go.Scatter]:
    """Create edge traces with configurable style."""
    traces = []
    edge_style = edge_style or {}

    # Define style mappings
    style_map = {
        "permanent": {
            "color": "#777777",  # Darker grey but not black
            "dash": "solid",
            "width": 1.5,  # Slightly thicker for emphasis
        },
        "false_positive": {
            "color": "rgba(255, 0, 0, 0.4)",  # More transparent red
            "dash": "dash",
            "width": 0.75,  # Thinner line
        },
        "false_negative": {
            "color": "rgba(0, 0, 255, 0.4)",  # More transparent blue
            "dash": "dash",
            "width": 0.75,  # Thinner line
        },
    }

    # Process each edge classification type
    for edge_type, edges in edge_classifications.items():
        x_coords = []
        y_coords = []
        hover_texts = []

        # Get style for this edge type
        style = style_map.get(edge_type, {"color": "gray", "dash": "solid"})

        for edge_info in edges:
            if not isinstance(edge_info, EdgeInfo):
                continue

            u, v = edge_info.edge
            if u not in node_positions or v not in node_positions:
                continue

            x0, y0 = node_positions[u]
            x1, y1 = node_positions[v]
            x_coords.extend([x0, x1, None])
            y_coords.extend([y0, y1, None])

            sources = ", ".join(edge_info.sources) if edge_info.sources else "Unknown"
            hover_text = f"Edge: {node_labels.get(u, u)} - {node_labels.get(v, v)}<br>Type: {edge_type}<br>Sources: {sources}"
            hover_texts.extend([hover_text, hover_text, None])

        if x_coords:
            line_style = dict(
                color=style["color"],
                width=edge_style.get("width", 1),
                dash=style["dash"],
            )

            traces.append(
                go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode="lines",
                    line=line_style,
                    hoverinfo="text",
                    text=hover_texts,
                    name=f"{edge_type.replace('_', ' ').title()} Edges",
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
                continue  # Skip nodes without positions

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
