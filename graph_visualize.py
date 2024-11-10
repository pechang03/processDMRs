"""
Functions for visualizing bicliques using Matplotlib and TikZplotlib
"""
import matplotlib.pyplot as plt
import tikzplotlib
import networkx as nx
from typing import Dict, List, Set, Tuple
import plotly.graph_objs as go
import json
from plotly.utils import PlotlyJSONEncoder

def create_biclique_visualization(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_labels: Dict[int, str],
    node_positions: Dict[int, Tuple[float, float]],
    node_biclique_map: Dict[int, List[int]],
    split_positions: Dict[int, List[Tuple[float, float]]] = None,  # Make optional
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None
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
    # First ensure all nodes have positions
    all_nodes = set()
    for dmr_nodes, gene_nodes in bicliques:
        all_nodes.update(dmr_nodes)
        all_nodes.update(gene_nodes)
    
    # Add default positions for any missing nodes
    for node in all_nodes:
        if node not in node_positions:
            # Determine if node is DMR or gene based on bicliques structure
            is_dmr = any(node in dmr_nodes for dmr_nodes, _ in bicliques)
            node_positions[node] = (0, 0.5) if is_dmr else (1, 0.5)
    
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
    
    # Create DMR nodes (now split between hub and non-hub)
    hub_dmr_x = []
    hub_dmr_y = []
    hub_dmr_text = []
    
    regular_dmr_x = []
    regular_dmr_y = []
    regular_dmr_text = []
    
    dmr_nodes_set = set(node_biclique_map.keys())
    for node_id, pos in node_positions.items():
        if node_id in dmr_nodes_set:  # Use the passed DMR node set
            biclique_nums = node_biclique_map.get(node_id, [])
            label = node_labels.get(node_id, f"DMR_{node_id}")
            label = f"{label}<br>Bicliques: {', '.join(map(str, biclique_nums))}"
            
            if dominating_set and node_id in dominating_set:  # Hub DMR
                hub_dmr_x.append(pos[0])
                hub_dmr_y.append(pos[1])
                hub_dmr_text.append(f"{label}<br>(Hub)")
            else:  # Regular DMR
                regular_dmr_x.append(pos[0])
                regular_dmr_y.append(pos[1])
                regular_dmr_text.append(label)
    
    # Add regular DMR nodes
    node_traces.append(
        go.Scatter(
            x=regular_dmr_x,
            y=regular_dmr_y,
            mode='markers+text',
            marker=dict(size=10, color='blue'),
            text=regular_dmr_text,
            textposition='middle left',
            hoverinfo='text',
            name='DMRs'
        )
    )
    
    # Add hub DMR nodes with special styling
    node_traces.append(
        go.Scatter(
            x=hub_dmr_x,
            y=hub_dmr_y,
            mode='markers+text',
            marker=dict(
                size=15,  # Larger size
                color='gold',  # Distinctive color
                symbol='star',  # Star shape
                line=dict(color='orange', width=2)  # Orange border
            ),
            text=hub_dmr_text,
            textposition='middle left',
            hoverinfo='text',
            name='Hub DMRs'
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
            base_label = node_labels.get(node_id, f"Gene_{node_id}")
            
            if len(biclique_nums) > 1:  # Split gene - use split positions
                for idx, split_pos in enumerate(split_positions.get(node_id, [])):
                    split_gene_x.append(split_pos[0])
                    split_gene_y.append(split_pos[1])
                    label = f"{base_label}<br>Biclique: {biclique_nums[idx]}<br>(Split {idx+1}/{len(biclique_nums)})"
                    split_gene_text.append(label)
            else:  # Regular gene
                regular_gene_x.append(pos[0])
                regular_gene_y.append(pos[1])
                label = f"{base_label}<br>Biclique: {biclique_nums[0]}" if biclique_nums else base_label
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
    if split_gene_x:  # Only add if there are split genes
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
                [d.get('area', 'N/A') for d in dmr_metadata.values()],
                # Use node_biclique_map to get bicliques for each DMR
                [','.join(map(str, node_biclique_map.get(int(dmr.split('_')[1])-1, []))) 
                 for dmr in dmr_metadata.keys()]
            ])
        )
        
    if gene_metadata and gene_id_mapping:
        gene_table = go.Table(
            domain=dict(x=[0.7, 1], y=[0, 1]),
            header=dict(values=['Gene', 'Description', 'Bicliques']),
            cells=dict(values=[
                list(gene_metadata.keys()),
                [d.get('description', 'N/A') for d in gene_metadata.values()],
                # Use node_biclique_map and gene_id_mapping to get bicliques
                [','.join(map(str, node_biclique_map.get(
                    next((gene_id for gene, gene_id in gene_id_mapping.items() 
                         if gene.lower() == g.lower()), 'N/A'), [])))
                 for g in gene_metadata.keys()]
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
