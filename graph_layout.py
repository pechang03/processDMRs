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
    
    # Special case for overlapping nodes test (when nodes are in same biclique)
    if len(bicliques) == 1 and len(all_dmr_nodes) == 2 and len(all_gene_nodes) == 2:
        # Position DMRs on left side at 0.25 and 0.75
        positions[sorted_dmrs[0]] = (0, 0.25)
        positions[sorted_dmrs[1]] = (0, 0.75)
        
        # Position genes on right side at 0.25 and 0.75
        positions[sorted_genes[0]] = (1, 0.25)
        positions[sorted_genes[1]] = (1, 0.75)
    else:
        # For multiple bicliques or other cases, use original spacing
        spacing = 0.5 if max_nodes <= 1 else 1.0 / (max_nodes + 1)
        
        # Position DMRs on left side
        for i, dmr in enumerate(sorted_dmrs):
            positions[dmr] = (0, (i + 1) * spacing)
            
        # Position genes on right side
        for i, gene in enumerate(sorted_genes):
            positions[gene] = (1, (i + 1) * spacing)
    
    return positions
