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
    
    # Get all DMR and gene nodes from bicliques
    all_dmr_nodes = set()
    all_gene_nodes = set()
    for dmr_nodes, gene_nodes in bicliques:
        all_dmr_nodes.update(dmr_nodes)
        all_gene_nodes.update(gene_nodes)
    
    # Sort nodes by their smallest biclique number
    sorted_dmrs = sorted(list(all_dmr_nodes), 
                        key=lambda n: min(node_biclique_map.get(n, [float('inf')])))
    sorted_genes = sorted(list(all_gene_nodes),
                         key=lambda n: min(node_biclique_map.get(n, [float('inf')])))
    
    # Calculate spacing based on number of nodes
    max_nodes = max(len(sorted_dmrs), len(sorted_genes))
    
    if not bicliques:
        return {}
    
    # For single biclique, use simple positioning
    if len(bicliques) == 1:
        dmr_nodes, gene_nodes = bicliques[0]
        return position_single_biclique(dmr_nodes, gene_nodes)
    
    # For multiple bicliques, combine all nodes
    all_dmr_nodes = set()
    all_gene_nodes = set()
    for dmr_nodes, gene_nodes in bicliques:
        all_dmr_nodes.update(dmr_nodes)
        all_gene_nodes.update(gene_nodes)
    
    # Sort nodes by their smallest biclique number
    sorted_dmrs = sorted(list(all_dmr_nodes))
    sorted_genes = sorted(list(all_gene_nodes))
    
    return position_nodes_evenly(set(sorted_dmrs), set(sorted_genes))
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
