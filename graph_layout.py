"""
Functions for calculating node layouts in biclique visualizations
"""
import networkx as nx
from typing import Dict, List, Set, Tuple

def calculate_node_positions(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_biclique_map: Dict[int, List[int]]
) -> Dict[int, Tuple[float, float]]:
    """Calculate positions for nodes in the biclique visualization."""
    positions = {}
    
    # 1. First collect all nodes and their biclique memberships
    all_nodes = set(node_biclique_map.keys())
    for dmr_nodes, gene_nodes in bicliques:
        all_nodes.update(dmr_nodes)
        all_nodes.update(gene_nodes)

    # Track node degrees for high-degree node handling
    node_degrees = {}
    for node in all_nodes:
        node_degrees[node] = len(node_biclique_map.get(node, []))

    # 2. Identify node types and split genes
    all_dmr_nodes = set()
    regular_genes = set()
    split_genes = set()
    
    min_gene_id = float('inf')
    for biclique in bicliques:
        dmr_nodes, gene_nodes = biclique
        all_dmr_nodes.update(dmr_nodes)
        for gene in gene_nodes:
            min_gene_id = min(min_gene_id, gene)
            if len(node_biclique_map.get(gene, [])) > 1:
                split_genes.add(gene)
            else:
                regular_genes.add(gene)

    # 3. Handle unassigned nodes (error handling)
    unassigned = all_nodes - (all_dmr_nodes | regular_genes | split_genes)
    if unassigned:
        print(f"Found {len(unassigned)} unassigned nodes")
        for node in unassigned:
            if node < min_gene_id:
                all_dmr_nodes.add(node)
            else:
                regular_genes.add(node)

    # 4. Calculate vertical spacing based on bicliques
    total_height = sum(len(dmr_nodes) + len(gene_nodes) for dmr_nodes, gene_nodes in bicliques)
    spacing = 1.0 / (total_height + 1) if total_height > 0 else 0.5
    current_y = spacing

    # 5. Position nodes biclique by biclique
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        # Position DMRs
        for dmr in sorted(dmr_nodes):
            if dmr not in positions:  # Only position if not already positioned
                positions[dmr] = (0, current_y)
                current_y += spacing

        # Position regular genes
        for gene in sorted(gene_nodes - split_genes):
            if gene not in positions:
                positions[gene] = (1, current_y)
                current_y += spacing

        # Position split genes
        for gene in sorted(gene_nodes & split_genes):
            if gene not in positions:
                positions[gene] = (1.1, current_y)
                current_y += spacing

    # Handle any remaining unpositioned nodes (error handling)
    missing_nodes = all_nodes - set(positions.keys())
    if missing_nodes:
        print(f"Assigning positions to {len(missing_nodes)} remaining nodes")
        for node in missing_nodes:
            if node in all_dmr_nodes:
                positions[node] = (0, current_y)
            elif node in split_genes:
                positions[node] = (1.1, current_y)
            else:
                positions[node] = (1, current_y)
            current_y += spacing

    # Validation step
    if len(positions) != len(all_nodes):
        print(f"Warning: Not all nodes positioned. Expected {len(all_nodes)}, got {len(positions)}")
        missing = all_nodes - set(positions.keys())
        print(f"Missing positions for nodes: {missing}")

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
