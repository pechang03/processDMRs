# File biclique visualization.py
# Author: Peter Shaw
# Date: 5/6/2019
#

import plotly.graph_objs as go
import json
from plotly.utils import PlotlyJSONEncoder
import plotly.colors
from typing import Dict, List, Set, Tuple

"""
 Functions for creating biclique visualizations using Plotly
"""

from node_info import NodeInfo  # Add this line

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
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        color = biclique_colors[biclique_idx]

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


def generate_biclique_colors(num_bicliques: int) -> List[str]:
    """Generate distinct colors for bicliques"""

    colors = plotly.colors.qualitative.Set3 * (
        num_bicliques // len(plotly.colors.qualitative.Set3) + 1
    )
    return colors[:num_bicliques]
"""
Functions for creating interactive biclique visualizations
"""
from typing import Dict, List, Set, Tuple
import plotly.graph_objs as go
import json
from plotly.utils import PlotlyJSONEncoder
from graph_layout import calculate_node_positions, position_single_biclique, position_nodes_evenly

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
    """Create interactive Plotly visualization with colored bicliques."""
    biclique_colors = generate_biclique_colors(len(bicliques))
    
    # Create traces
    edge_traces = create_edge_traces(bicliques, node_positions)
    box_traces = create_box_traces(bicliques, node_positions, biclique_colors)
    node_traces = create_node_traces(bicliques, node_positions, node_labels, biclique_colors)
    hub_traces = create_hub_traces(dominating_set, node_positions, node_labels) if dominating_set else []
    
    # Combine all traces
    plot_data = box_traces + edge_traces + node_traces + hub_traces
    
    # Add metadata tables if provided
    if dmr_metadata:
        plot_data.append(create_dmr_table(dmr_metadata))
    if gene_metadata and gene_id_mapping:
        plot_data.append(create_gene_table(gene_metadata, gene_id_mapping, node_biclique_map))

    # Create layout
    layout = create_plot_layout()
    
    # Create figure and convert to JSON
    fig = {'data': plot_data, 'layout': layout}
    return json.dumps(fig, cls=PlotlyJSONEncoder)

def create_dmr_table(dmr_metadata: Dict[str, Dict]) -> go.Table:
    """Create a Plotly table for DMR metadata."""
    headers = ["DMR", "Area", "Bicliques"]
    rows = [
        [
            dmr,
            metadata.get("area", "N/A"),
            ", ".join(map(str, metadata.get("bicliques", []))),
        ]
        for dmr, metadata in dmr_metadata.items()
    ]
    return go.Table(header=dict(values=headers), cells=dict(values=list(zip(*rows))))

def create_gene_table(
    gene_metadata: Dict[str, Dict],
    gene_id_mapping: Dict[str, int],
    node_biclique_map: Dict[int, List[int]],
) -> go.Table:
    """Create a Plotly table for gene metadata."""
    headers = ["Gene", "Description", "Bicliques"]
    rows = [
        [
            gene,
            metadata.get("description", "N/A"),
            ", ".join(map(str, node_biclique_map.get(gene_id_mapping[gene], []))),
        ]
        for gene, metadata in gene_metadata.items()
    ]
    return go.Table(header=dict(values=headers), cells=dict(values=list(zip(*rows))))

def create_edge_traces(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_positions: Dict[int, Tuple[float, float]]
) -> List[go.Scatter]:
    """Create edge traces for all bicliques."""
    traces = []
    for dmr_nodes, gene_nodes in bicliques:
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                traces.append(go.Scatter(
                    x=[node_positions[dmr][0], node_positions[gene][0]],
                    y=[node_positions[dmr][1], node_positions[gene][1]],
                    mode="lines",
                    line=dict(width=1, color="gray"),
                    hoverinfo="none",
                    showlegend=False
                ))
    return traces

def create_box_traces(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_positions: Dict[int, Tuple[float, float]],
    biclique_colors: List[str]
) -> List[go.Scatter]:
    """Create box traces around bicliques."""
    traces = []
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        nodes = dmr_nodes | gene_nodes
        if not nodes:
            continue
            
        x_coords = [node_positions[n][0] for n in nodes]
        y_coords = [node_positions[n][1] for n in nodes]
        
        padding = 0.05
        x_min, x_max = min(x_coords) - padding, max(x_coords) + padding
        y_min, y_max = min(y_coords) - padding, max(y_coords) + padding
        
        traces.append(go.Scatter(
            x=[x_min, x_max, x_max, x_min, x_min],
            y=[y_min, y_min, y_max, y_max, y_min],
            mode="lines",
            line=dict(color=biclique_colors[biclique_idx], width=2, dash="dot"),
            fill="toself",
            fillcolor=biclique_colors[biclique_idx],
            opacity=0.1,
            name=f"Biclique {biclique_idx + 1}",
            showlegend=True
        ))
    return traces

def create_node_traces(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    biclique_colors: List[str]
) -> List[go.Scatter]:
    """Create node traces for DMRs and genes."""
    node_colors = get_node_colors(bicliques, biclique_colors)
    dmr_data, gene_data = separate_node_data(bicliques, node_positions, node_colors, node_labels)
    
    traces = []
    traces.append(create_dmr_trace(*dmr_data))
    traces.append(create_gene_trace(*gene_data))
    return traces

def create_hub_traces(
    dominating_set: Set[int],
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str]
) -> List[go.Scatter]:
    """Create traces for hub nodes."""
    if not dominating_set:
        return []
        
    hub_x, hub_y, hub_text = [], [], []
    for node in dominating_set:
        if node in node_positions:
            hub_x.append(node_positions[node][0])
            hub_y.append(node_positions[node][1])
            hub_text.append(f"{node_labels.get(node, f'DMR_{node}')} (Hub)")
            
    return [go.Scatter(
        x=hub_x,
        y=hub_y,
        mode="markers+text",
        marker=dict(
            size=15,
            color="gold",
            symbol="star",
            line=dict(color="orange", width=2)
        ),
        text=hub_text,
        textposition="middle left",
        hoverinfo="text",
        name="Hub DMRs"
    )]

def create_plot_layout() -> dict:
    """Create the plot layout configuration."""
    return {
        'showlegend': True,
        'hovermode': 'closest',
        'margin': dict(b=40, l=40, r=40, t=40),
        'xaxis': dict(showgrid=False, zeroline=False, showticklabels=False),
        'yaxis': dict(showgrid=False, zeroline=False, showticklabels=False)
    }

def get_node_colors(
    bicliques: List[Tuple[Set[int], Set[int]]],
    biclique_colors: List[str]
) -> Dict[int, str]:
    """Get color mapping for all nodes based on biclique membership."""
    node_colors = {}
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        color = biclique_colors[biclique_idx]
        for node in dmr_nodes | gene_nodes:
            node_colors[node] = color
    return node_colors

def separate_node_data(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_positions: Dict[int, Tuple[float, float]],
    node_colors: Dict[int, str],
    node_labels: Dict[int, str]
) -> Tuple[Tuple, Tuple]:
    """Separate node data into DMR and gene data."""
    dmr_x, dmr_y, dmr_colors, dmr_text = [], [], [], []
    gene_x, gene_y, gene_colors, gene_text = [], [], [], []
    
    all_dmr_nodes = {n for dmr_nodes, _ in bicliques for n in dmr_nodes}
    
    for node_id, pos in node_positions.items():
        if node_id in node_colors:  # Only process nodes that are in bicliques
            if node_id in all_dmr_nodes:
                dmr_x.append(pos[0])
                dmr_y.append(pos[1])
                dmr_colors.append(node_colors[node_id])
                dmr_text.append(node_labels.get(node_id, f"DMR_{node_id}"))
            else:
                gene_x.append(pos[0])
                gene_y.append(pos[1])
                gene_colors.append(node_colors[node_id])
                gene_text.append(node_labels.get(node_id, f"Gene_{node_id}"))
                
    return (dmr_x, dmr_y, dmr_colors, dmr_text), (gene_x, gene_y, gene_colors, gene_text)

def create_dmr_trace(x, y, colors, text) -> go.Scatter:
    """Create trace for DMR nodes."""
    return go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        marker=dict(size=10, color=colors, line=dict(color="black", width=1)),
        text=text,
        textposition="middle left",
        hoverinfo="text",
        name="DMRs"
    )

def create_gene_trace(x, y, colors, text) -> go.Scatter:
    """Create trace for gene nodes."""
    return go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        marker=dict(
            size=10,
            color=colors,
            symbol="diamond",
            line=dict(color="black", width=1)
        ),
        text=text,
        textposition="middle right",
        hoverinfo="text",
        name="Genes"
    )

def generate_biclique_colors(num_bicliques: int) -> List[str]:
    """Generate distinct colors for bicliques."""
    import plotly.colors
    colors = plotly.colors.qualitative.Set3 * (
        num_bicliques // len(plotly.colors.qualitative.Set3) + 1
    )
    return colors[:num_bicliques]
def create_component_visualization(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_labels: Dict[int, str],
    node_positions: Dict[int, Tuple[float, float]],
    node_biclique_map: Dict[int, List[int]],
    false_positive_edges: Set[Tuple[int, int]],
    node_info: NodeInfo,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None,
) -> str:
    """
    Create visualization for a connected component containing bicliques.
    Includes false positive edges between bicliques.
    """
    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(bicliques))
    
    traces = []
    
    # Add biclique boxes first (background)
    traces.extend(create_biclique_boxes(bicliques, node_positions, biclique_colors))
    
    # Add regular edges within bicliques
    traces.extend(create_biclique_edges(bicliques, node_positions))
    
    # Add false positive edges (red/dotted)
    traces.extend(create_false_positive_edges(false_positive_edges, node_positions))
    
    # Add nodes with proper styling based on type
    traces.extend(create_node_traces(
        node_info,
        node_positions,
        node_labels,
        node_biclique_map,
        biclique_colors
    ))

    # Create layout
    layout = create_plot_layout()
    
    # Create figure and convert to JSON
    fig = {'data': traces, 'layout': layout}
    return json.dumps(fig, cls=PlotlyJSONEncoder)

def create_false_positive_edges(
    false_positive_edges: Set[Tuple[int, int]],
    node_positions: Dict[int, Tuple[float, float]]
) -> List[go.Scatter]:
    """Create traces for false positive edges between bicliques."""
    traces = []
    for dmr, gene in false_positive_edges:
        traces.append(go.Scatter(
            x=[node_positions[dmr][0], node_positions[gene][0]],
            y=[node_positions[dmr][1], node_positions[gene][1]],
            mode="lines",
            line=dict(
                color="red",
                width=1,
                dash="dot"
            ),
            hoverinfo="text",
            hovertext="False positive edge",
            showlegend=False
        ))
    return traces
