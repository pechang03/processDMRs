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
    
    
    if not all_dmr_nodes and not all_gene_nodes:
        return {}

    # Special case for single biclique with one DMR and one gene
    if len(all_dmr_nodes) == 1 and len(all_gene_nodes) == 1:
        dmr = next(iter(all_dmr_nodes))
        gene = next(iter(all_gene_nodes))
        positions[dmr] = (0, 0.5)
        positions[gene] = (1, 0.5)
        return positions

    # Identify split genes (genes that appear in multiple bicliques)
    split_genes = {gene for gene in all_gene_nodes 
                  if len(node_biclique_map.get(gene, [])) > 1}
    regular_genes = all_gene_nodes - split_genes
    
    # Calculate y-spacing based on total number of nodes
    total_nodes = len(all_dmr_nodes) + len(regular_genes) + sum(len(node_biclique_map[g]) for g in split_genes)
    spacing = 1.0 / (total_nodes + 1)
    
    # Position DMR nodes at x=0
    current_y = spacing
    for dmr in sorted(all_dmr_nodes):
        positions[dmr] = (0, current_y)
        current_y += spacing
    
    # Position regular genes at x=1
    for gene in sorted(regular_genes):
        positions[gene] = (1, current_y)
        current_y += spacing
    
    # Position split genes at x=1.1, with one position per biclique appearance
    split_positions = {}  # New dictionary for split gene positions
    for gene in sorted(split_genes):
        split_positions[gene] = []  # Initialize list of positions for this gene
        for _ in range(len(node_biclique_map[gene])):
            split_positions[gene].append((1.1, current_y))
            current_y += spacing
    
    # Combine regular positions with first position of split genes
    positions.update({gene: positions[0] for gene, positions in split_positions.items()})
    
    
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
