"""
Functions for visualizing bicliques using Plotly
"""
import plotly.graph_objs as go
from typing import Dict, List, Set, Tuple
import json
from plotly.utils import PlotlyJSONEncoder

def create_biclique_visualization(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_labels: Dict[int, str],
    node_positions: Dict[int, Tuple[float, float]],
    node_biclique_map: Dict[int, List[int]],
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None
) -> str:
    """
    Create interactive Plotly visualization of bicliques with metadata tables.
    
    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples
        node_labels: Maps node IDs to display labels
        node_positions: Maps node IDs to (x,y) positions
        node_biclique_map: Maps node IDs to list of biclique numbers
        dmr_metadata: Dictionary of DMR metadata for tables
        gene_metadata: Dictionary of gene metadata for tables
    """
    # Create main visualization as before
    edge_traces = []
    node_traces = []
    
    # Create edges for each biclique
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                edge_traces.append(
                    go.Scatter(
                        x=[node_positions[dmr][0], node_positions[gene][0]],
                        y=[node_positions[dmr][1], node_positions[gene][1]],
                        mode='lines',
                        line=dict(width=1),
                        hoverinfo='none'
                    )
                )
    
    # Create DMR nodes
    dmr_x = []
    dmr_y = []
    dmr_text = []
    
    for node_id, pos in node_positions.items():
        if node_id < max(next(iter(bicliques))[0]):  # Is DMR node
            dmr_x.append(pos[0])
            dmr_y.append(pos[1])
            biclique_nums = node_biclique_map[node_id]
            biclique_nums = node_biclique_map.get(node_id, [])
            label = node_labels.get(node_id, f"DMR_{node_id}")
            label = f"{label}<br>Bicliques: {', '.join(map(str, biclique_nums))}"
            dmr_text.append(label)
    
    node_traces.append(
        go.Scatter(
            x=dmr_x,
            y=dmr_y,
            mode='markers+text',
            marker=dict(size=10, color='blue'),
            text=dmr_text,
            textposition='middle left',
            hoverinfo='text'
        )
    )
    
    # Create gene nodes (split and non-split separately)
    regular_gene_x = []
    regular_gene_y = []
    regular_gene_text = []
    
    split_gene_x = []
    split_gene_y = []
    split_gene_text = []
    
    for node_id, pos in node_positions.items():
        if node_id >= min(next(iter(bicliques))[1]):  # Is gene node
            biclique_nums = node_biclique_map.get(node_id, [])
            label = node_labels.get(node_id, f"Gene_{node_id}")
            label = f"{label}<br>Bicliques: {', '.join(map(str, biclique_nums))}"
            
            if len(biclique_nums) > 1:  # Split gene
                split_gene_x.append(pos[0])
                split_gene_y.append(pos[1])
                split_gene_text.append(label)
            else:  # Regular gene
                regular_gene_x.append(pos[0])
                regular_gene_y.append(pos[1])
                regular_gene_text.append(label)
    
    # Add regular gene nodes
    node_traces.append(
        go.Scatter(
            x=regular_gene_x,
            y=regular_gene_y,
            mode='markers+text',
            marker=dict(size=10, color='red'),
            text=regular_gene_text,
            textposition='middle right',
            hoverinfo='text',
            name='Regular Genes'
        )
    )
    
    # Add split gene nodes with different color and style
    node_traces.append(
        go.Scatter(
            x=split_gene_x,
            y=split_gene_y,
            mode='markers+text',
            marker=dict(
                size=12,
                color='purple',
                line=dict(color='black', width=1),
                symbol='diamond'
            ),
            text=split_gene_text,
            textposition='middle right',
            hoverinfo='text',
            name='Split Genes'
        )
    )
    
    # Add metadata tables
    if dmr_metadata:
        dmr_table = go.Table(
            domain=dict(x=[0, 0.3], y=[0, 1]),
            header=dict(values=['DMR', 'Area', 'Bicliques']),
            cells=dict(values=[
                list(dmr_metadata.keys()),
                [d['area'] for d in dmr_metadata.values()],
                [','.join(map(str, d['bicliques'])) for d in dmr_metadata.values()]
            ])
        )
        
    if gene_metadata:
        gene_table = go.Table(
            domain=dict(x=[0.7, 1], y=[0, 1]),
            header=dict(values=['Gene', 'Description', 'Bicliques']),
            cells=dict(values=[
                list(gene_metadata.keys()),
                [d['description'] for d in gene_metadata.values()],
                [','.join(map(str, d['bicliques'])) for d in gene_metadata.values()]
            ])
        )
    
    # Combine visualization with tables
    layout = go.Layout(
        showlegend=True,
        hovermode='closest',
        grid=dict(columns=3, rows=1),
        margin=dict(b=20, l=5, r=5, t=40),
        legend=dict(
            x=0.5,
            y=1.1,
            xanchor='center',
            orientation='h'
        )
    )
    
    fig = go.Figure(
        data=edge_traces + node_traces + [dmr_table, gene_table] if dmr_metadata else edge_traces + node_traces,
        layout=layout
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)

def create_node_biclique_map(bicliques: List[Tuple[Set[int], Set[int]]]) -> Dict[int, List[int]]:
    """
    Create mapping of nodes to their biclique numbers.
    
    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples
    
    Returns:
        Dictionary mapping node IDs to list of biclique numbers they belong to
    """
    node_biclique_map = {}
    
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        for node in dmr_nodes | gene_nodes:
            if node not in node_biclique_map:
                node_biclique_map[node] = []
            node_biclique_map[node].append(biclique_idx + 1)
    
    return node_biclique_map
