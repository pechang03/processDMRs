# File: traces.py
# Author: Peter Shaw
#

"""Node trace creation functionality"""

import logging
import matplotlib.colors
from typing import Dict, List, Set, Tuple, Any
from backend.app.utils.edge_info import EdgeInfo
import plotly.graph_objs as go
from backend.app.utils.node_info import NodeInfo

logger = logging.getLogger(__name__)


def get_text_position(x: float, y: float) -> str:
    """Determine text position based on node's quadrant with vertical offset."""
    # Calculate buffer zone (10% of plot area)
    x_buffer = 0.1
    y_buffer = 0.1
    
    # Horizontal positioning
    if x < -x_buffer:  # Left side
        horizontal = "right"
    elif x > x_buffer:  # Right side
        horizontal = "left"
    else:  # Center zone
        horizontal = "center"

    # Vertical positioning with offset
    if y < -y_buffer:  # Bottom third
        vertical = "top"
    elif y > y_buffer:  # Top third
        vertical = "bottom"
    else:  # Middle third
        vertical = "middle"

    return f"{vertical} {horizontal}"

def create_node_traces(
    node_info: NodeInfo,
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    biclique_colors: List[str],
    component: Dict,
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
) -> List[go.Scatter]:
    """Create node traces with consistent styling."""
    traces = []
    import math

    # Use all component nodes regardless of degree
    nodes_to_show = component["component"]

    # Helper function to create transparent version of color
    def make_transparent(color: str, alpha: float = 0.6) -> str:
        """Convert color to transparent rgba string"""
        try:
            if color.startswith("#"):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                return f"rgba({r},{g},{b},{alpha})"
            elif color.startswith("rgba"):
                parts = [float(x) for x in color[5:-1].split(',')]
                parts[3] = alpha
                return f"rgba({','.join(map(str, parts))})"
            return f"rgba(128,128,128,{alpha})"  # Fallback to gray
        except Exception as e:
            logger.warning(f"Color conversion error: {str(e)}")
            return f"rgba(128,128,128,{alpha})"

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


def create_unified_gene_trace(
    gene_nodes: Set[int],
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    biclique_colors: List[str],
    gene_metadata: Dict[str, Dict] = None,
    is_split: bool = False
) -> go.Scatter:
    """Unified gene trace creation with split/regular handling"""
    x, y, colors, texts, hovers, x_offsets, y_offsets = [], [], [], [], [], [], []
    
    for node_id in sorted(gene_nodes):
        pos = node_positions.get(node_id)
        if not pos:
            continue
            
        x_pos, y_pos = pos
        x.append(x_pos)
        y.append(y_pos)
        
        # Calculate offsets
        x_offset = 0.12 * (-1 if x_pos > 0 else 1) if is_split else 0.08 * (1 if x_pos > 0 else -1)
        y_offset = 0.08 * (1 if y_pos > 0 else -1) if is_split else 0.05 * (1 if y_pos > 0 else -1)
        
        x_offsets.append(x_offset)
        y_offsets.append(y_offset)
        
        # Color logic
        biclique_idx = node_biclique_map.get(node_id, [0])[0]
        try:
            color = biclique_colors[biclique_idx % len(biclique_colors)]
            if not color.startswith("#"):
                color = matplotlib.colors.to_hex(color).lower()
            colors.append(f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.6)" 
                         if is_split else color)
        except IndexError:
            colors.append("#808080")  # Fallback to gray
        
        # Text and hover
        label = node_labels.get(node_id, str(node_id))
        texts.append(label)
        meta = gene_metadata.get(str(node_id), {})
        hovers.append(f"{label}<br>Description: {meta.get('description','N/A')}")

    return go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        marker=dict(
            size=12 if is_split else 10,
            color=colors,
            symbol="diamond" if is_split else "circle",
            line=dict(width=2 if is_split else 1)
        ),
        text=texts,
        hovertext=hovers,
        textposition=[get_text_position(x[i]+x_offsets[i], y[i]+y_offsets[i]) 
                     for i in range(len(x))],
        textfont=dict(
            size=14 if is_split else 12,
            family="Arial Black" if is_split else None
        ),
        name="Split Genes" if is_split else "Regular Genes"
    )


"""
Node trace creation functionality.
Node shapes are centrally defined in NODE_SHAPES dictionary.
All node shape assignments should reference this dictionary.
"""

# Centralized node shape configuration
NODE_SHAPES = {
    "dmr": {
        "regular": "hexagon",  # Changed from octagon
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
    node_shapes: Dict[str, str] = None  # Add shape config parameter
) -> go.Scatter:
    # Add default shape configuration
    node_shapes = node_shapes or {
        "regular": "hexagon",
        "hub": "star"
    }
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

        # Convert node_id to int for comparison
        is_hub = int(node_id) in dominating_set  # Explicit conversion
        
        # Add debug logging
        logger.debug(f"DMR {node_id} is_hub: {is_hub}")
        
        sizes.append(15 if is_hub else 10)
        symbols.append(NODE_SHAPES["dmr"]["hub" if is_hub else "regular"])

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

    # Add debug logging
    logger.debug("DMR trace marker configuration: %s", {
        "symbols": symbols,
        "marker_config": {
            "size": sizes,
            "color": colors,
            "symbol": symbols,
            "line": dict(color="black", width=1),
        }
    })
    print("Symbols:", symbols)
    print("Marker configuration:", {
        "size": sizes,
        "color": colors,
        "symbol": symbols,
        "line": dict(color="black", width=1),
    })
    
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
    component_nodes: Set[int],
    split_genes: Set[int],
    edge_style: Dict = None,
) -> List[go.Scatter]:
    """Create edge traces with configurable style."""
    traces = []
    edge_style = edge_style or {}
    component_nodes = component_nodes or set()

    # Use parameter directly instead of nested classifications
    style_map = {
        "permanent": {
            "color": "rgba(119, 119, 119, 1.0)",  # Convert list to rgba string
            "dash": "solid",
            "width": 1.5,
        },
        "false_positive": {
            "color": "rgba(255, 0, 0, 0.4)",
            "dash": "dash",
            "width": 0.75,
        },
        "false_negative": {
            "color": "rgba(0, 0, 255, 0.4)",
            "dash": "dash",
            "width": 0.75,
        },
        "split_gene_edge": {
            "color": "rgba(150, 150, 150, 0.3)",
            "dash": "dot",
            "width": 0.5,
        }
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
            if u not in component_nodes or v not in component_nodes:
                continue  # Skip edges not in current component

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
                    legendgroup="edges",  # Add this line
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
                line=dict(
                    color=biclique_colors[biclique_idx],  # Now using CSS string
                    width=2, 
                    dash="dot"
                ),
                fill="toself",
                fillcolor=biclique_colors[biclique_idx],  # Now using CSS string
                opacity=0.1,
                name=f"Biclique {biclique_idx + 1}",
                showlegend=True,
            )
        )
    return traces
