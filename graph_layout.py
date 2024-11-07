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
    sorted_dmrs = sorted(all_dmr_nodes, 
                        key=lambda n: min(node_biclique_map.get(n, [float('inf')])))
    sorted_genes = sorted(all_gene_nodes,
                         key=lambda n: min(node_biclique_map.get(n, [float('inf')])))
    
    # Position DMRs on left side
    dmr_spacing = 1.0 / (len(sorted_dmrs) + 1)
    for i, dmr in enumerate(sorted_dmrs):
        positions[dmr] = (0, (i + 1) * dmr_spacing)
        
    # Position genes on right side
    gene_spacing = 1.0 / (len(sorted_genes) + 1)
    for i, gene in enumerate(sorted_genes):
        positions[gene] = (1, (i + 1) * gene_spacing)
    
    # Position DMRs on left side
    for i, dmr in enumerate(dmr_nodes):
        positions[dmr] = (0, i)
        
    # Position genes on right side, sorted by biclique number
    gene_nodes.sort(key=lambda g: min(node_biclique_map[g]))
    for i, gene in enumerate(gene_nodes):
        positions[gene] = (1, i)
    
    return positions
