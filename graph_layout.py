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
    
    # Get all unique nodes from node_biclique_map first
    all_nodes = set(node_biclique_map.keys())
    
    # Then add any nodes from bicliques that might not be in the map
    for dmr_nodes, gene_nodes in bicliques:
        all_nodes.update(dmr_nodes)
        all_nodes.update(gene_nodes)
    
    # Determine node types based on bicliques
    all_dmr_nodes = set()
    all_gene_nodes = set()

    # Determine node types based on bicliques
    all_dmr_nodes = set()
    all_gene_nodes = set()
    
    # First pass: collect nodes from bicliques
    for dmr_nodes, gene_nodes in bicliques:
        all_dmr_nodes.update(dmr_nodes)
        all_gene_nodes.update(gene_nodes)
    
    # Second pass: handle any nodes that appear in both sets (prioritize DMR assignment)
    overlap = all_dmr_nodes & all_gene_nodes
    if overlap:
        all_gene_nodes -= overlap  # Remove overlapping nodes from genes
    
    # Third pass: handle remaining nodes based on node_biclique_map patterns
    remaining_nodes = all_nodes - (all_dmr_nodes | all_gene_nodes)
    for node in remaining_nodes:
        # Check biclique patterns to determine if it's more likely a DMR or gene
        appearances = node_biclique_map.get(node, [])
        if appearances:
            # Look at the nodes it appears with in bicliques
            is_dmr = False
            for biclique_idx in appearances:
                if biclique_idx < len(bicliques):
                    dmr_set, gene_set = bicliques[biclique_idx]
                    if node in dmr_set:
                        is_dmr = True
                        break
                else:
                    continue
            if is_dmr:
                all_dmr_nodes.add(node)
            else:
                all_gene_nodes.add(node)
        else:
            # If no pattern available, use ID-based assignment as fallback
            if node < min(all_gene_nodes, default=float('inf')):
                all_dmr_nodes.add(node)
            else:
                all_gene_nodes.add(node)
    
    
    if not all_nodes:
        return {}

    # Special case for single nodes
    if len(all_nodes) == 1:
        node = next(iter(all_nodes))
        positions[node] = (0.5, 0.5)
        return positions

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
    
    # Calculate total vertical positions needed
    total_positions = (
        len(all_dmr_nodes) +  # One position per DMR
        len(regular_genes) +   # One position per regular gene
        sum(len(node_biclique_map.get(g, [])) for g in split_genes)  # Multiple positions per split gene
    )
    
    spacing = 1.0 / (total_positions + 1)
    
    # Position DMR nodes at x=0
    current_y = spacing
    for dmr in sorted(all_dmr_nodes):
        positions[dmr] = (0, current_y)
        current_y += spacing
    
    # Position regular genes at x=1
    for gene in sorted(regular_genes):
        positions[gene] = (1, current_y)
        current_y += spacing
    
    # Position split genes - give each appearance its own y-position
    for gene in sorted(split_genes):
        appearances = len(node_biclique_map.get(gene, []))
        if appearances > 0:  # Only process if we know the appearances
            base_y = current_y
            positions[gene] = (1.1, base_y)  # Main position
            current_y += spacing * appearances  # Move current_y past all positions for this gene
        else:
            # Fallback for split genes with unknown appearances
            positions[gene] = (1.1, current_y)
            current_y += spacing
    
    
    # Final verification - assign default positions to any missing nodes
    missing_nodes = all_nodes - set(positions.keys())
    if missing_nodes:
        print(f"Assigning default positions to nodes: {missing_nodes}")
        for node in missing_nodes:
            is_dmr = node in all_dmr_nodes
            x_pos = 0 if is_dmr else 1
            positions[node] = (x_pos, current_y)
            current_y += spacing
    
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
