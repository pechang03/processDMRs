# File: traces.py
# Author: Peter Shaw
#

"""Node trace creation functionality"""

import os
from typing import Dict, List, Set, Tuple
from biclique_analysis.edge_info import EdgeInfo  # Import EdgeInfo
import plotly.graph_objs as go
import networkx as nx  # Add this line
from .node_info import NodeInfo


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
    """Create node traces with proper styling based on node type."""
    if os.getenv('DEBUG'):
        print("\nNode trace creation debug:")
        print(f"Total nodes to position: {len(node_positions)}")
        print(f"DMR nodes: {len(node_info.dmr_nodes)}")
        print(f"Regular genes: {len(node_info.regular_genes)}")
        print(f"Split genes: {len(node_info.split_genes)}")
        print(f"Dominating set size: {len(dominating_set) if dominating_set else 0}")

    traces = []
    
    # Separate DMR nodes into dominating and non-dominating
    dominating_dmrs = set()
    non_dominating_dmrs = set()
    if dominating_set:
        dominating_dmrs = {n for n in node_info.dmr_nodes if n in dominating_set}
        non_dominating_dmrs = node_info.dmr_nodes - dominating_dmrs
    else:
        non_dominating_dmrs = node_info.dmr_nodes

    # Create traces for each node category
    node_categories = [
        ("Dominating DMRs", dominating_dmrs, "star", "red"),
        ("Regular DMRs", non_dominating_dmrs, "circle", "gray"),
        ("Regular Genes", node_info.regular_genes, "diamond", "gray"),
        ("Split Genes", node_info.split_genes, "diamond-cross", "gray")
    ]

    for category_name, nodes, symbol, default_color in node_categories:
        x = []
        y = []
        text = []
        hover_text = []
        colors = []

        for node_id in nodes:
            # Validate position exists and is a proper tuple
            position = node_positions.get(node_id)
            if not position or not isinstance(position, tuple) or len(position) != 2:
                print(f"Warning: Invalid position for node {node_id}: {position}")
                continue

            x_pos, y_pos = position
            x.append(x_pos)
            y.append(y_pos)

            # Set node color
            if node_id in node_biclique_map and biclique_colors:
                biclique_idx = node_biclique_map[node_id][0]
                color = biclique_colors[biclique_idx] if biclique_idx < len(biclique_colors) else default_color
            else:
                color = default_color
            colors.append(color)

            # Create label and hover text
            label = node_labels.get(node_id, str(node_id))
            text.append(label)

            # Add metadata to hover text
            if node_id in node_info.dmr_nodes and dmr_metadata:
                meta = dmr_metadata.get(label, {})
                hover = f"{label}<br>Area: {meta.get('area', 'N/A')}<br>Description: {meta.get('description', 'N/A')}"
            elif gene_metadata:
                gene_name = node_labels.get(node_id)
                if gene_name in gene_metadata:
                    meta = gene_metadata[gene_name]
                    hover = f"{gene_name}<br>Description: {meta.get('description', 'N/A')}"
                else:
                    hover = label
            else:
                hover = label

            # Add dominating set status to hover text if applicable
            if dominating_set and node_id in dominating_set:
                hover += "<br>(Dominating Set Member)"

            hover_text.append(hover)

        if x:  # Only create trace if we have nodes to show
            traces.append(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="markers+text",
                    marker=dict(
                        size=15 if category_name == "Dominating DMRs" else 10,
                        color=colors,
                        symbol=symbol,
                        line=dict(color="black", width=1),
                    ),
                    text=text,
                    hovertext=hover_text,
                    textposition="middle right" if "Genes" in category_name else "middle left",
                    hoverinfo="text",
                    name=category_name,
                    showlegend=True,
                )
            )

    return traces


def create_edge_traces(
    edge_classifications: Dict[str, List[EdgeInfo]] | List[Tuple[Set[int], Set[int], Set[int]]] | List[Tuple[int, int]],
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    original_graph: nx.Graph,
    false_positive_edges: Set[Tuple[int, int]] = None,
    false_negative_edges: Set[Tuple[int, int]] = None,
    edge_type: str = "biclique",
    edge_style: Dict = None
) -> List[go.Scatter]:
    """Create edge traces with configurable style."""
    traces = []
    edge_style = edge_style or {}

    color_map = {
        "permanent": "green",
        "false_positive": "red",
        "false_negative": "blue",
    }

    # Handle different input types
    if isinstance(edge_classifications, dict):
        # Dictionary case - process classified edges
        for label, edges_info in edge_classifications.items():
            x_coords = []
            y_coords = []
            hover_texts = []

            color = color_map.get(label, "gray")

            for edge_info in edges_info:
                # Handle both EdgeInfo objects and raw tuples
                if isinstance(edge_info, EdgeInfo):
                    u, v = edge_info.edge
                    sources = ', '.join(edge_info.sources) if edge_info.sources else 'Unknown'
                    edge_label = edge_info.label
                else:
                    u, v = edge_info
                    sources = 'Unknown'
                    edge_label = label

                if u in node_positions and v in node_positions:
                    x0, y0 = node_positions[u]
                    x1, y1 = node_positions[v]
                    x_coords.extend([x0, x1, None])
                    y_coords.extend([y0, y1, None])

                    hover_text = f"Edge: {node_labels.get(u, u)} - {node_labels.get(v, v)}<br>Label: {edge_label}<br>Sources: {sources}"
                    hover_texts.extend([hover_text, hover_text, None])

            if x_coords:
                trace = go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode="lines",
                    line=dict(color=color, width=edge_style.get("width", 1)),
                    hoverinfo="text",
                    text=hover_texts,
                    name=f"Edges ({label})",
                )
                traces.append(trace)
    else:
        # List case - handle as biclique edges
        x_coords = []
        y_coords = []
        hover_texts = []
        
        # If input is a list of tuples (DMR nodes, gene nodes, split_genes)
        if isinstance(edge_classifications, list) and len(edge_classifications) > 0:
            if isinstance(edge_classifications[0], tuple):
                if len(edge_classifications[0]) == 3:  # (DMR, genes, split_genes) format
                    # Handle biclique format with split genes
                    for dmr_nodes, gene_nodes, split_genes in edge_classifications:
                        # Create edges between DMRs and regular genes
                        for dmr in dmr_nodes:
                            for gene in (gene_nodes - split_genes):  # Regular genes
                                if dmr in node_positions and gene in node_positions:
                                    x0, y0 = node_positions[dmr]
                                    x1, y1 = node_positions[gene]
                                    x_coords.extend([x0, x1, None])
                                    y_coords.extend([y0, y1, None])
                                    
                                    hover_text = f"Edge: {node_labels.get(dmr, dmr)} - {node_labels.get(gene, gene)}"
                                    hover_texts.extend([hover_text, hover_text, None])

                        # Create edges between DMRs and split genes (different style)
                        for dmr in dmr_nodes:
                            for gene in split_genes:
                                if dmr in node_positions and gene in node_positions:
                                    x0, y0 = node_positions[dmr]
                                    x1, y1 = node_positions[gene]
                                    x_coords.extend([x0, x1, None])
                                    y_coords.extend([y0, y1, None])
                                    
                                    hover_text = f"Edge: {node_labels.get(dmr, dmr)} - {node_labels.get(gene, gene)} (Split Gene)"
                                    hover_texts.extend([hover_text, hover_text, None])

                elif len(edge_classifications[0]) == 2:  # (DMR, genes) format
                    # Handle basic biclique format
                    for dmr_nodes, gene_nodes in edge_classifications:
                        for dmr in dmr_nodes:
                            for gene in gene_nodes:
                                if dmr in node_positions and gene in node_positions:
                                    x0, y0 = node_positions[dmr]
                                    x1, y1 = node_positions[gene]
                                    x_coords.extend([x0, x1, None])
                                    y_coords.extend([y0, y1, None])
                                    
                                    hover_text = f"Edge: {node_labels.get(dmr, dmr)} - {node_labels.get(gene, gene)}"
                                    hover_texts.extend([hover_text, hover_text, None])

        if x_coords:
            # Add permanent edges
            trace = go.Scatter(
                x=x_coords,
                y=y_coords,
                mode="lines",
                line=dict(
                    color=color_map["permanent"],
                    width=edge_style.get("width", 1)
                ),
                hoverinfo="text",
                text=hover_texts,
                name="Permanent Edges",
            )
            traces.append(trace)

            # Add false positive edges if provided
            if false_positive_edges:
                fp_x = []
                fp_y = []
                fp_texts = []
                for u, v in false_positive_edges:
                    if u in node_positions and v in node_positions:
                        x0, y0 = node_positions[u]
                        x1, y1 = node_positions[v]
                        fp_x.extend([x0, x1, None])
                        fp_y.extend([y0, y1, None])
                        hover_text = f"False Positive Edge: {node_labels.get(u, u)} - {node_labels.get(v, v)}"
                        fp_texts.extend([hover_text, hover_text, None])
                
                if fp_x:
                    traces.append(go.Scatter(
                        x=fp_x,
                        y=fp_y,
                        mode="lines",
                        line=dict(
                            color=color_map["false_positive"],
                            width=edge_style.get("width", 1),
                            dash="dash"
                        ),
                        hoverinfo="text",
                        text=fp_texts,
                        name="False Positive Edges"
                    ))

            # Add false negative edges if provided
            if false_negative_edges:
                fn_x = []
                fn_y = []
                fn_texts = []
                for u, v in false_negative_edges:
                    if u in node_positions and v in node_positions:
                        x0, y0 = node_positions[u]
                        x1, y1 = node_positions[v]
                        fn_x.extend([x0, x1, None])
                        fn_y.extend([y0, y1, None])
                        hover_text = f"False Negative Edge: {node_labels.get(u, u)} - {node_labels.get(v, v)}"
                        fn_texts.extend([hover_text, hover_text, None])
                
                if fn_x:
                    traces.append(go.Scatter(
                        x=fn_x,
                        y=fn_y,
                        mode="lines",
                        line=dict(
                            color=color_map["false_negative"],
                            width=edge_style.get("width", 1),
                            dash="dot"
                        ),
                        hoverinfo="text",
                        text=fn_texts,
                        name="False Negative Edges"
                    ))

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




import networkx as nx
