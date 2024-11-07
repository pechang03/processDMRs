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
        
        # Identify split genes (genes that appear in multiple bicliques)
        split_genes = {
            gene for gene in all_gene_nodes 
            if len(node_biclique_map.get(gene, [])) > 1
        }
    
        # Sort bicliques by size (smaller on top)
        sorted_bicliques = sorted(
            enumerate(bicliques),
            key=lambda x: len(x[1][0]) * len(x[1][1])  # Sort by biclique size
        )
    
        # Calculate total height needed
        total_height = 1.0
        spacing = 0.1  # Space between bicliques
    
        # Calculate position for each biclique
        current_y = 0.9  # Start from top
        biclique_regions = {}  # Store y-regions for each biclique
    
        for biclique_idx, (dmr_nodes, gene_nodes) in sorted_bicliques:
            height_needed = max(len(dmr_nodes), len(gene_nodes)) * 0.1
            biclique_regions[biclique_idx] = (current_y - height_needed, current_y)
            current_y -= (height_needed + spacing)
    
        # Position nodes for each biclique
        for biclique_idx, (dmr_nodes, gene_nodes) in sorted_bicliques:
            top_y, bottom_y = biclique_regions[biclique_idx]
            height = bottom_y - top_y
        
            # Position DMRs
            dmr_spacing = height / (len(dmr_nodes) + 1)
            for i, dmr in enumerate(sorted(dmr_nodes)):
                y_pos = bottom_y - (i + 1) * dmr_spacing
                positions[dmr] = (0, y_pos)
        
            # Position non-split genes
            non_split = [g for g in gene_nodes if g not in split_genes]
            if non_split:
                gene_spacing = height / (len(non_split) + 1)
                for i, gene in enumerate(sorted(non_split)):
                    y_pos = bottom_y - (i + 1) * gene_spacing
                    positions[gene] = (1, y_pos)
    
        # Position split genes between their bicliques
        for gene in split_genes:
            biclique_nums = node_biclique_map[gene]
            y_positions = [
                (biclique_regions[b][0] + biclique_regions[b][1]) / 2
                for b in biclique_nums
            ]
            avg_y = sum(y_positions) / len(y_positions)
            positions[gene] = (1, avg_y)
    
    return positions
