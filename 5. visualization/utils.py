"""Utility functions for visualization"""

from typing import Dict, List, Set, Tuple

def create_node_biclique_map(
    bicliques: List[Tuple[Set[int], Set[int]]],
) -> Dict[int, List[int]]:
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
