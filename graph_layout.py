"""
Functions for calculating node layouts in biclique visualizations
"""
import networkx as nx
from typing import Dict, List, Set, Tuple

def calculate_node_positions(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_biclique_map: Dict[int, List[int]]
) -> Dict[int, Tuple[float, float]]:
    """
    Calculate positions for nodes in the biclique visualization.
    
    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples
        node_biclique_map: Maps node IDs to list of biclique numbers they belong to
    
    Returns:
        Dictionary mapping node IDs to (x,y) positions
    """
    positions = {}
    
    # Get all unique nodes from bicliques and node_biclique_map
    all_dmr_nodes = set()
    all_gene_nodes = set()
    
    # Add nodes from bicliques
    for dmr_nodes, gene_nodes in bicliques:
        all_dmr_nodes.update(dmr_nodes)
        all_gene_nodes.update(gene_nodes)
    
    # Add any additional nodes from node_biclique_map
    for node in node_biclique_map:
        if node < min(all_gene_nodes):  # If node ID is less than minimum gene ID, it's a DMR
            all_dmr_nodes.add(node)
        else:
            all_gene_nodes.add(node)
    
    # Calculate y-positions based on total number of nodes
    total_dmrs = len(all_dmr_nodes)
    total_genes = len(all_gene_nodes)
    max_nodes = max(total_dmrs, total_genes)
    
    if max_nodes == 0:
        return {}
    
    spacing = 1.0 / (max_nodes + 1) if max_nodes > 1 else 0.5
    
    # Position DMR nodes on the left (x=0)
    for i, dmr in enumerate(sorted(all_dmr_nodes)):
        y_pos = spacing * (i + 1)
        positions[dmr] = (0, y_pos)
    
    # Position gene nodes on the right (x=1)
    for i, gene in enumerate(sorted(all_gene_nodes)):
        y_pos = spacing * (i + 1)
        positions[gene] = (1, y_pos)
    
    # Add default positions for any nodes in node_biclique_map that weren't positioned
    min_gene_id = min(all_gene_nodes) if all_gene_nodes else float('inf')
    for node in node_biclique_map:
        if node not in positions:
            is_dmr = node < min_gene_id
            positions[node] = (0, 0.5) if is_dmr else (1, 0.5)
    
    return positions
def position_single_biclique(dmr_nodes: Set[int], gene_nodes: Set[int]) -> Dict[int, Tuple[float, float]]:
    """Position nodes for a single biclique."""
    positions = {}
    
    # Single DMR and gene case
    if len(dmr_nodes) == 1 and len(gene_nodes) == 1:
        dmr = next(iter(dmr_nodes))
        gene = next(iter(gene_nodes))
        positions[dmr] = (0, 0.5)  # Fixed y-position at 0.5
        positions[gene] = (1, 0.5)  # Fixed y-position at 0.5
        return positions
    
    # Two DMRs and two genes case (overlapping)
    if len(dmr_nodes) == 2 and len(gene_nodes) == 2:
        dmr_nodes_sorted = sorted(dmr_nodes)
        gene_nodes_sorted = sorted(gene_nodes)
        
        positions[dmr_nodes_sorted[0]] = (0, 0.25)
        positions[dmr_nodes_sorted[1]] = (0, 0.75)
        positions[gene_nodes_sorted[0]] = (1, 0.25)
        positions[gene_nodes_sorted[1]] = (1, 0.75)
        return positions
    
    return position_nodes_evenly(dmr_nodes, gene_nodes)

def position_nodes_evenly(dmr_nodes: Set[int], gene_nodes: Set[int]) -> Dict[int, Tuple[float, float]]:
    """Position nodes evenly spaced on left and right sides."""
    positions = {}
    max_nodes = max(len(dmr_nodes), len(gene_nodes))
    
    # For multiple nodes, space them evenly between 0 and 1
    if max_nodes > 1:
        spacing = 1.0 / (max_nodes + 1)
        
        # Position DMRs on left side
        for i, dmr in enumerate(sorted(dmr_nodes)):
            y_pos = spacing * (i + 1)
            positions[dmr] = (0, y_pos)
        
        # Position genes on right side
        for i, gene in enumerate(sorted(gene_nodes)):
            y_pos = spacing * (i + 1)
            positions[gene] = (1, y_pos)
    else:
        # Single node case - position at 0.5
        if dmr_nodes:
            positions[next(iter(dmr_nodes))] = (0, 0.5)
        if gene_nodes:
            positions[next(iter(gene_nodes))] = (1, 0.5)
    
    return positions
