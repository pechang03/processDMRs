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
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None
) -> List[go.Scatter]:
    """Create node traces with proper styling based on node type."""
    if os.getenv('DEBUG'):
        print("\nNode trace creation debug:")
        print(f"Total nodes to position: {len(node_positions)}")
        print(f"DMR nodes: {len(node_info.dmr_nodes)}")
        print(f"Regular genes: {len(node_info.regular_genes)}")
        print(f"Split genes: {len(node_info.split_genes)}")
        print(f"Sample DMR IDs: {sorted(list(node_info.dmr_nodes))[:5]}")
        print(f"Sample gene IDs: {sorted(list(node_info.regular_genes))[:5]}")
        print(f"Sample split gene IDs: {sorted(list(node_info.split_genes))[:5]}")
    
    traces = []

    # Create DMR nodes trace
    dmr_x = []
    dmr_y = []
    dmr_text = []
    dmr_hover_text = []  # Separate hover text from display text
    dmr_colors = []

    # Create gene nodes trace
    gene_x = []
    gene_y = []
    gene_text = []
    gene_hover_text = []  # Separate hover text from display text
    gene_colors = []

    for node_id, (x, y) in node_positions.items():
        color = "gray"
        label = node_labels.get(node_id, str(node_id))
        display_text = label  # This will be shown on the graph
        hover_text = label   # This will be shown on hover
        
        # Add metadata to hover text
        if node_id in node_info.dmr_nodes and dmr_metadata:
            meta = dmr_metadata.get(label, {})
            hover_text = f"{label}<br>Area: {meta.get('area', 'N/A')}<br>Description: {meta.get('description', 'N/A')}"
        elif gene_metadata:
            gene_name = node_labels.get(node_id)
            if gene_name in gene_metadata:
                meta = gene_metadata[gene_name]
                hover_text = f"{gene_name}<br>Description: {meta.get('description', 'N/A')}"

        if node_id in node_biclique_map and biclique_colors:
            biclique_idx = node_biclique_map[node_id][0]
            if biclique_idx < len(biclique_colors):
                color = biclique_colors[biclique_idx]
            else:
                color = "gray"

        if dominating_set and node_id in dominating_set:
            color = "red"

        if node_id in node_info.dmr_nodes:
            dmr_x.append(x)
            dmr_y.append(y)
            dmr_text.append(display_text)  # Use display text for node label
            dmr_hover_text.append(hover_text)  # Use hover text for hover info
            dmr_colors.append(color)
        else:
            gene_x.append(x)
            gene_y.append(y)
            gene_text.append(display_text)  # Use display text for node label
            gene_hover_text.append(hover_text)  # Use hover text for hover info
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
                text=dmr_text,  # Use text for display
                hovertext=dmr_hover_text,  # Use hovertext for hover
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
                text=gene_text,  # Use text for display
                hovertext=gene_hover_text,  # Use hovertext for hover
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
    print("\nEdge trace creation debug:")
    print(f"Number of bicliques: {len(bicliques)}")
    print("Sample biclique sizes:")
    for i, (dmrs, genes) in enumerate(bicliques[:3]):
        print(f"Biclique {i}: {len(dmrs)} DMRs, {len(genes)} genes")

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




