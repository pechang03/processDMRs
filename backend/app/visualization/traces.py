# File: traces.py
# Author: Peter Shaw
#

"""Node trace creation functionality"""

# import logging
import matplotlib.colors
from typing import Dict, List, Set, Tuple, Any
from .color_utils import get_rgb_arr, get_rgb_str
from backend.app.utils.edge_info import EdgeInfo
import plotly.graph_objs as go
from backend.app.utils.node_info import NodeInfo
from flask import current_app

# logger = logging.getLogger(__name__)

"""
Node trace creation functionality.
Node shapes are centrally defined in NODE_SHAPES dictionary.
All node shape assignments should reference this dictionary.
"""

# Centralized node shape configuration
NODE_SHAPES = {
    "dmr": {
        "regular": "hexagon",  # Changed from octagon
        "hub": "star",
    },
    "gene": {"regular": "circle", "split": "diamond"},
}


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
    # Helper function to create transparent version of color
    #


def make_transparent(color: str, alpha: float = 0.6) -> str:
    """Convert color to RGB string and handle opacity separately in marker config"""
    current_app.logger.debug("make_transparent")
    try:
        if color.startswith("#"):
            rgb = get_rgb_arr(color)
            return get_rgb_str(rgb)
        elif color.startswith("rgb"):
            rgb = get_rgb_arr(color)
            return get_rgb_str(rgb)
        return get_rgb_str(list(get_rgb_arr([128, 128, 128])))  # Fallback to gray
    except Exception as e:
        current_app.logger.warning(f"Color conversion error: {str(e)}")
        return "rgb(128, 128, 128)"


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

    # Use all component nodes regardless of degree
    nodes_to_show = component["component"]

    # Create DMR trace - only for nodes with degree > 0
    dmr_x, dmr_y, dmr_colors, dmr_text_positions = [], [], [], []
    for node in node_info.dmr_nodes:
        if (
            node in node_positions and node in nodes_to_show
        ):  # Added check for nodes_to_show
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
                hoveron="fills+points",
                marker=dict(
                    size=12,
                    color=dmr_colors,
                    symbol=NODE_SHAPES["dmr"]["regular"],
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
        if (
            node in node_positions and node in nodes_to_show
        ):  # Added check for nodes_to_show
            x, y = node_positions[node]
            gene_x.append(x)
            gene_y.append(y)
            biclique_idx = node_biclique_map.get(node, [0])[0]
            color = biclique_colors[biclique_idx % len(biclique_colors)]
            if isinstance(color, tuple):
                # color is already (r,g,b,a) in [0..1], convert to [0..255]
                arr = [int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)]
            else:
                if isinstance(color, tuple):
                    # color is already (r,g,b,a) in [0..1], convert to [0..255]
                    arr = [
                        int(color[0] * 255),
                        int(color[1] * 255),
                        int(color[2] * 255),
                    ]
                else:
                    if isinstance(color, tuple):
                        # color is already (r,g,b,a) in [0..1], convert to [0..255]
                        arr = [
                            int(color[0] * 255),
                            int(color[1] * 255),
                            int(color[2] * 255),
                        ]
                    else:
                        arr = get_rgb_arr(color)
            gene_colors.append(
                (
                    int(arr[0]) / 255,
                    int(arr[1]) / 255,
                    int(arr[2]) / 255,
                    0.9,  # Increased opacity
                )
            )
            gene_text_positions.append(get_text_position(x, y))

    if gene_x:
        traces.append(
            go.Scatter(
                x=gene_x,
                y=gene_y,
                mode="markers+text",
                hoveron="fills+points",
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

    # def create_edge_trace(x, y, color, name=None):
    """Create an edge trace with lines.

    Args:
        x: List of x coordinates
        y: List of y coordinates
        color: Color for the line
        name: Optional name for the trace

    Returns:
        go.Scatter trace with lines
    """
    """
    trace = go.Scatter(
        x=x, y=y, mode="lines", line=dict(color=color, width=1), hoverinfo="none"
    )
    if name is not None:
        trace.update(name=name)
    return trace
    """

    # def create_node_trace(x, y, symbol, color, text):
    """Create a node trace with markers and text labels.
    Args:
        x: List of x coordinates
        y: List of y coordinates
        symbol: Marker symbol to use
        color: Color for the markers
        text: Text labels for the nodes

    Returns:
        go.Scatter trace with markers and text
    """

    # Ensure that text is a list if given as a string
    """
    if isinstance(text, str):
        text = [text]
    return go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        marker={
            "symbol": symbol,
            "size": 10,
            "color": color,
            "line": {"color": "black", "width": 1},
        },
        text=text,
        textposition="top center",
        hoverinfo="text",
    )
    """


def create_unified_gene_trace(
    gene_nodes: Set[int],
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    biclique_colors: List[str],
    gene_metadata: Dict[str, Dict] = None,
) -> go.Scatter:
    """Unified gene trace creation with split/regular handling based on biclique indices"""
    current_app.logger.debug(f"Creating unified gene trace for {len(gene_nodes)} nodes")
    x, y, colors, texts, textpositions, hovers = [], [], [], [], [], []
    processed_nodes = []  # Keep track of nodes we actually process

    for node_id in sorted(gene_nodes):
        pos = node_positions.get(node_id)
        if not pos:
            continue

        processed_nodes.append(node_id)  # Track which nodes we actually process

        x_pos, y_pos = pos
        x.append(x_pos)
        y.append(y_pos)

        biclique_indices = node_biclique_map.get(node_id, [0])
        is_split = len(biclique_indices) > 1

        # Calculate text position based on node type and position
        if is_split:
            # Split nodes: text opposite to x position
            textpositions.append("middle right" if x_pos < 0 else "middle left")
        else:
            # Regular nodes: text same side as x position
            textpositions.append("middle left" if x_pos < 0 else "middle right")

        # Process colors - ensure full opacity
        color = biclique_colors[biclique_indices[0] % len(biclique_colors)]
        if isinstance(color, tuple):
            r, g, b = color[:3]
            colors.append(f"rgba({int(r*255)},{int(g*255)},{int(b*255)},1)")
        else:
            color_str = str(color)
            if not color_str.startswith("#"):
                color_str = matplotlib.colors.to_hex(color_str).lower()
            rgb = get_rgb_arr(color_str)
            colors.append(f"rgba({rgb[0]},{rgb[1]},{rgb[2]},1)")

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
            size=[
                12 if len(node_biclique_map.get(n, [])) > 1 else 10
                for n in processed_nodes
            ],
            color=colors,
            symbol=[
                (
                    NODE_SHAPES["gene"]["split"]
                    if len(node_biclique_map.get(n, [])) > 1
                    else NODE_SHAPES["gene"]["regular"]
                )
                for n in processed_nodes
            ],
            line=dict(
                width=[
                    2 if len(node_biclique_map.get(n, [])) > 1 else 1
                    for n in processed_nodes
                ]
            ),
        ),
        text=texts,
        textposition=textpositions,
        hovertext=hovers,
        textfont=dict(
            size=[
                14 if len(node_biclique_map.get(n, [])) > 1 else 12
                for n in processed_nodes
            ],
            family=[
                "Arial Black" if len(node_biclique_map.get(n, [])) > 1 else "Arial"
                for n in processed_nodes
            ],
        ),
        name="Gene Nodes",
    )


def create_dmr_trace(
    dmr_nodes: Set[int],
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    biclique_colors: List[str],
    timepoint_id: int,  # New parameter
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
    node_shapes: Dict[str, str] = None,  # Add shape config parameter
) -> go.Scatter:
    # Add default shape configuration
    node_shapes = node_shapes or {"regular": "hexagon", "hub": "star"}
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
    # current_app.logger.debug("Point 5a")

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
        # current_app.logger.debug("Point 5bb")
        if isinstance(color, tuple):
            # Color is already (r,g,b) in [0..1] range, set high opacity
            colors.append(
                f"rgba({int(color[0]*255)},{int(color[1]*255)},{int(color[2]*255)},0.9)"
            )
        else:
            # Convert string color to rgb values
            color_str = str(color)
            if not color_str.startswith("#"):
                color_str = matplotlib.colors.to_hex(color_str).lower()
            arr = get_rgb_arr(color_str)
            colors.append(f"rgba({arr[0]},{arr[1]},{arr[2]},0.9)")
        # current_app.logger.debug("Point 5bc")

        # Convert node_id to int for comparison
        is_hub = int(node_id) in dominating_set  # Explicit conversion

        # Add debug logging
        # current_app.logger.debug(f"DMR {node_id} is_hub: {is_hub}")

        sizes.append(15 if is_hub else 10)
        symbol_type = "hub" if is_hub else "regular"
        symbols.append(NODE_SHAPES["dmr"][symbol_type])

        # Create concise label for node display
        # If dmr_metadata is provided and contains a 'dmr_name', use it;
        # otherwise, fall back to adjusting the raw node id using convert_dmr_id.
        info = dmr_metadata.get(str(node_id)) if dmr_metadata else None
        if info and "dmr_name" in info and info["dmr_name"]:
            label = f'dd {info["dmr_name"]}'
        else:
            from backend.app.utils.id_mapping import convert_dmr_id

            #label = f"DMR_{node_id+1}"
            label = f"DMR_{(convert_dmr_id(dmr_num=node_id, timepoint=timepoint_id))}"
        text.append(label)

        # Create detailed hover text
        meta = dmr_metadata.get(node_id, {}) if dmr_metadata else {}
        hover = [f"DMR {node_id}"]

        if is_hub:
            hover.append("(Hub Node)")

        hover.append(f"Area: {meta.get('area', 'N/A')}")

        # Add edge details if available
        if meta.get("edge_details"):
            hover.append("<br>Edge Details:")
            for edge in meta["edge_details"]:
                edge_text = (
                    f"→ {edge.get('gene_name', 'N/A')} | "
                    f"Type: {edge.get('edge_type', '-')} | "
                    f"TSS: {edge.get('distance_from_tss', '-')} | "
                    f"Edit: {edge.get('edit_type', '-')}"
                )
                hover.append(edge_text)

        hover_text.append("<br>".join(hover))

    if not x:
        return None

    # Add debug logging
    """
    current_app.logger.debug(
        "DMR trace marker configuration: %s",
        {
            "symbols": symbols,
            "marker_config": {
                "size": sizes,
                "color": colors,
                "symbol": symbols,
                "line": dict(color="black", width=1),
            },
        },
    )
    """

    return go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        hoveron="fills+points",
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
        showlegend=False,  # Let legend traces handle the legend
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
    # Centralized edge style configuration
    style_map = {
        "permanent": {
            "color": get_rgb_str([119, 119, 119]),
            "dash": "solid",
            "width": 1.5,
            "opacity": 1.0,
        },
        "false_positive": {
            "color": get_rgb_str([255, 0, 0]),
            "dash": "dash",
            "width": 0.75,
            "opacity": 0.4,
        },
        "false_negative": {
            "color": get_rgb_str([0, 0, 255]),
            "dash": "dash",
            "width": 0.75,
            "opacity": 0.4,
        },
        "split_gene_edge": {
            "color": get_rgb_str([150, 150, 150]),
            "dash": "dot",
            "width": 0.5,
            "opacity": 0.3,
        },
        # Default style for any unrecognized edge types
        "default": {"color": "gray", "dash": "solid", "width": 1.0, "opacity": 1.0},
    }

    # Process each edge classification type
    for edge_type, edges in edge_classifications.items():
        # Get style for this edge type
        style = style_map.get(
            edge_type, {"color": "gray", "dash": "solid", "opacity": 1.0, "width": 1.0}
        )
        # Initialize separate lists for normal and split-incident edges
        normal_x_coords, normal_y_coords, normal_hover_texts = [], [], []
        split_x_coords, split_y_coords, split_hover_texts = [], [], []

        for edge_info in edges:
            if not isinstance(edge_info, EdgeInfo):
                continue
            u, v = edge_info.edge
            if u not in component_nodes or v not in component_nodes:
                continue
            x0, y0 = node_positions[u]
            x1, y1 = node_positions[v]
            sources = ", ".join(edge_info.sources) if edge_info.sources else "Unknown"
            hover_text = f"Edge: {node_labels.get(u, u)} - {node_labels.get(v, v)}<br>Type: {edge_type}<br>Sources: {sources}"

            if (u in split_genes) or (v in split_genes):
                split_x_coords.extend([x0, x1, None])
                split_y_coords.extend([y0, y1, None])
                split_hover_texts.extend([hover_text, hover_text, None])
            else:
                normal_x_coords.extend([x0, x1, None])
                normal_y_coords.extend([y0, y1, None])
                normal_hover_texts.extend([hover_text, hover_text, None])

        # Create a trace for normal edges (if any)
        if normal_x_coords:
            traces.append(
                go.Scatter(
                    x=normal_x_coords,
                    y=normal_y_coords,
                    mode="lines",
                    opacity=style.get("opacity", 1.0),  # use base opacity
                    line=dict(
                        color=style["color"],
                        width=edge_style.get("width", style.get("width", 1)),
                        dash=style["dash"],
                    ),
                    hoverinfo="text",
                    text=normal_hover_texts,
                    name=f"{edge_type.replace('_', ' ').title()} Edges",
                    legendgroup="edges",
                    showlegend=False,
                )
            )

        # Create a trace for edges incident to split nodes (if any) with reduced opacity
        if split_x_coords:
            reduced_opacity = (
                style.get("opacity", 1.0) * 0.5
            )  # adjust factor as desired
            traces.append(
                go.Scatter(
                    x=split_x_coords,
                    y=split_y_coords,
                    mode="lines",
                    opacity=reduced_opacity,
                    line=dict(
                        color=style["color"],
                        width=edge_style.get("width", style.get("width", 1)),
                        dash=style["dash"],
                    ),
                    hoverinfo="text",
                    text=split_hover_texts,
                    name=f"{edge_type.replace('_', ' ').title()} Edges",
                    legendgroup="edges",
                    showlegend=False,
                )
            )

    return traces


def create_biclique_boxes(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_positions: Dict[int, Tuple[float, float]],
    biclique_colors: List[str],
) -> List[Dict]:
    """Create border shapes (rectangles) around bicliques."""
    shapes = []
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        nodes = dmr_nodes | gene_nodes
        if not nodes:
            continue
        positions = [node_positions[node] for node in nodes if node in node_positions]
        if not positions:
            continue
        x_coords, y_coords = zip(*positions)
        padding = 0.05
        x_min, x_max = min(x_coords) - padding, max(x_coords) + padding
        y_min, y_max = min(y_coords) - padding, max(y_coords) + padding

        # Compute a fillcolor string with low opacity
        r, g, b, _ = biclique_colors[biclique_idx]
        fill_color = f"rgba({int(r*255)},{int(g*255)},{int(b*255)},0.1)"
        shape = {
            "type": "rect",
            "xref": "x",
            "yref": "y",
            "x0": x_min,
            "y0": y_min,
            "x1": x_max,
            "y1": y_max,
            "line": {
                "color": biclique_colors[biclique_idx],  # leaving border as is
                "width": 0,
                "dash": "dot",
            },
            "fillcolor": fill_color,  # Use our computed fill color
            "opacity": 1.0,  # Let the fillcolor encode transparency, so set overall opacity to 1
            "layer": "below",  # Ensures the shapes are rendered behind other traces
        }
        shapes.append(shape)
    return shapes


def split_genes(
    node_biclique_map: Dict[int, List[int]], gene_nodes: Set[int]
) -> Set[int]:
    """Identify genes that participate in multiple bicliques."""
    return {n for n in gene_nodes if len(node_biclique_map.get(n, [])) > 1}


def create_legend_traces(
    biclique_colors: List[str] = None,
) -> Tuple[List[dict], List[go.Scatter]]:
    """
    Create legend-only traces for nodes and edge types.
    Node shapes for DMRs and genes are taken from NODE_SHAPES.
    """
    legend_nodes = []

    # DMR legend entries:
    legend_nodes.append(
        {
            "x": [None],
            "y": [None],
            "mode": "markers",
            "marker": {
                "symbol": NODE_SHAPES["dmr"]["hub"],
                "size": 13,
                "color": "blue",
            },
            "name": "Hub DMRs",
            "showlegend": True,
            "legendgroup": "dmr",
        }
    )
    legend_nodes.append(
        {
            "x": [None],
            "y": [None],
            "mode": "markers",
            "marker": {
                "symbol": NODE_SHAPES["dmr"]["regular"],
                "size": 12,
                "color": "blue",
            },
            "name": "DMRs",
            "showlegend": True,
            "legendgroup": "dmr",
        }
    )

    # Gene legend entries:
    legend_nodes.append(
        {
            "x": [None],
            "y": [None],
            "mode": "markers",
            "marker": {
                "symbol": NODE_SHAPES["gene"]["split"],
                "size": 12,
                "color": "red",
            },
            "name": "Split Genes",
            "showlegend": True,
            "legendgroup": "gene",
        }
    )
    legend_nodes.append(
        {
            "x": [None],
            "y": [None],
            "mode": "markers",
            "marker": {"symbol": "circle", "size": 10, "color": "red"},
            "name": "Gene Nodes",
            "showlegend": True,
            "legendgroup": "gene",
        }
    )

    # Add biclique legend entries if colors provided
    if biclique_colors:
        for idx, color in enumerate(biclique_colors):
            legend_nodes.append(
                {
                    "x": [None],
                    "y": [None],
                    "mode": "markers",
                    "marker": {
                        "symbol": "circle",
                        "size": 12,
                        "color": color,
                    },
                    "name": f"Biclique {idx + 1}",
                    "showlegend": True,
                    "legendgroup": "biclique",
                }
            )

    # Legend for edge types
    legend_edges = []
    edge_colors = {
        "permanent": "rgb(119,119,119)",
        "false_positive": "rgb(255,0,0)",
        "false_negative": "rgb(0,0,255)",
    }
    for edge_type in ["permanent", "false_positive", "false_negative"]:
        edge_name = edge_type.replace("_", " ").title() + " Edges"
        legend_edges.append(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color=edge_colors.get(edge_type, "gray"), width=1),
                name=edge_name,
                showlegend=True,
                legendgroup="edges",
            )
        )
    return legend_nodes, legend_edges
