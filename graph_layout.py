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
    
    # Calculate spacing based on number of intervals needed
    # For n nodes, we need n+1 intervals to get positions at 0.25, 0.75 etc.
    max_nodes = max(len(sorted_dmrs), len(sorted_genes))
    spacing = 0.5 if max_nodes <= 1 else 1.0 / (2 * max_nodes)
    
    # Position DMRs on left side
    for i, dmr in enumerate(sorted_dmrs):
        positions[dmr] = (0, (2*i + 1) * spacing)
        
    # Position genes on right side
    for i, gene in enumerate(sorted_genes):
        positions[gene] = (1, (2*i + 1) * spacing)
    
    return positions
