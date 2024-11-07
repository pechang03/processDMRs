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
    
    # Sort nodes by their biclique numbers
    sorted_nodes = sorted(
        node_biclique_map.keys(),
        key=lambda n: min(node_biclique_map[n])  # Sort by smallest biclique number
    )
    
    # Separate DMRs and genes
    dmr_nodes = [n for n in sorted_nodes if n < max(bicliques[0][0])]
    gene_nodes = [n for n in sorted_nodes if n >= min(bicliques[0][1])]
    
    # Position DMRs on left side
    for i, dmr in enumerate(dmr_nodes):
        positions[dmr] = (0, i)
        
    # Position genes on right side, sorted by biclique number
    gene_nodes.sort(key=lambda g: min(node_biclique_map[g]))
    for i, gene in enumerate(gene_nodes):
        positions[gene] = (1, i)
    
    return positions
