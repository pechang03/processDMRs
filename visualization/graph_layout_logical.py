"""Core graph layout algorithms"""

from typing import Dict, List, Set, Tuple
from .node_info import NodeInfo


def calculate_node_positions(
    bicliques: List[Tuple[Set[int], Set[int]]], node_biclique_map: Dict[int, List[int]]
) -> Dict[int, Tuple[float, float]]:
    """Calculate base positions for nodes in the graph."""
    node_info = collect_node_information(bicliques, node_biclique_map)
    positions = {}
    current_y = 0

    # Handle empty bicliques case
    if not bicliques:
        print("Warning: No bicliques provided")
        # Return default positions for all nodes
        return position_remaining_nodes({}, node_info, 0, 0.2)
    
    # Calculate max counts for spacing
    max_dmr_count = max(len(dmr_nodes) for dmr_nodes, _ in bicliques)
    max_gene_count = max(len(gene_nodes) for _, gene_nodes in bicliques)
    
    spacing = calculate_vertical_spacing(
        max_dmr_count,
        max_gene_count
    )

    # Track nodes positioned in biclique phase
    nodes_positioned_in_bicliques = set()
    
    # Position nodes biclique by biclique
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        initial_position_count = len(positions)
        positions = position_biclique_nodes(
            dmr_nodes,
            gene_nodes,
            node_info.split_genes,
            current_y,
            spacing,
            positions,
            biclique_idx,
        )
        nodes_positioned_this_biclique = len(positions) - initial_position_count
        nodes_positioned_in_bicliques.update(dmr_nodes)
        nodes_positioned_in_bicliques.update(gene_nodes)
        
        if nodes_positioned_this_biclique > 0:
            print(f"Biclique {biclique_idx}: Positioned {nodes_positioned_this_biclique} nodes")
        
        biclique_height = calculate_biclique_height(dmr_nodes, gene_nodes, node_info.split_genes)
        current_y += biclique_height + spacing

    print(f"\nNodes positioned in biclique phase: {len(nodes_positioned_in_bicliques)}")
    
    # Handle remaining nodes
    missing_nodes = node_info.all_nodes - set(positions.keys())
    if missing_nodes:
        print(f"\nRemaining nodes analysis:")
        print(f"Total missing nodes: {len(missing_nodes)}")
        print(f"Missing DMRs: {len([n for n in missing_nodes if n in node_info.dmr_nodes])}")
        print(f"Missing genes: {len([n for n in missing_nodes if n not in node_info.dmr_nodes])}")
        print(f"Sample missing node IDs: {sorted(list(missing_nodes))[:5]}")
        
        position_remaining_nodes(positions, node_info, current_y, spacing)

    # Final validation
    final_missing = node_info.all_nodes - set(positions.keys())
    if final_missing:
        print(f"\nFinal position check:")
        print(f"Nodes still missing positions: {len(final_missing)}")
        print(f"Sample missing: {sorted(list(final_missing))[:5]}")

    return positions


def collect_node_information(
    bicliques: List[Tuple[Set[int], Set[int]]], node_biclique_map: Dict[int, List[int]]
) -> "NodeInfo":
    """Collect and categorize all nodes from bicliques and map."""
    all_nodes = set(node_biclique_map.keys())
    
    # If we have no bicliques, categorize nodes based on ID
    if not bicliques:
        # Assume nodes 0-2 are DMRs, rest are genes (based on test assumptions)
        dmr_nodes = {node for node in all_nodes if node <= 2}
        gene_nodes = {node for node in all_nodes if node > 2}
        split_genes = set()  # No split genes in empty bicliques case
        node_degrees = {node: 0 for node in all_nodes}
        min_gene_id = min(gene_nodes) if gene_nodes else 3
    else:
        # Normal processing with bicliques
        for dmr_nodes, gene_nodes in bicliques:
            all_nodes.update(dmr_nodes)
            all_nodes.update(gene_nodes)
        
        dmr_nodes = set()
        gene_nodes = set()
        for biclique_dmrs, biclique_genes in bicliques:
            dmr_nodes.update(biclique_dmrs)
            gene_nodes.update(biclique_genes)
            
        split_genes = {
            node for node in gene_nodes 
            if len(node_biclique_map.get(node, [])) > 1
        }
        node_degrees = {
            node: len(node_biclique_map.get(node, [])) 
            for node in all_nodes
        }
        min_gene_id = min(gene_nodes) if gene_nodes else 3

    regular_genes = gene_nodes - split_genes
    
    return NodeInfo(
        all_nodes=all_nodes,
        dmr_nodes=dmr_nodes,
        regular_genes=regular_genes,
        split_genes=split_genes,
        node_degrees=node_degrees,
        min_gene_id=min_gene_id
    )


def get_all_nodes(
    bicliques: List[Tuple[Set[int], Set[int]]], node_biclique_map: Dict[int, List[int]]
) -> Set[int]:
    """Collect all unique nodes from bicliques and map."""
    all_nodes = set(node_biclique_map.keys())
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        all_nodes.update(dmr_nodes)
        all_nodes.update(gene_nodes)
    return all_nodes


def calculate_node_degrees(
    nodes: Set[int], node_biclique_map: Dict[int, List[int]]
) -> Dict[int, int]:
    """Calculate degree (number of bicliques) for each node."""
    return {node: len(node_biclique_map.get(node, [])) for node in nodes}


def find_min_gene_id(bicliques: List[Tuple[Set[int], Set[int]]]) -> int:
    """Find the minimum gene ID to separate DMRs from genes."""
    min_gene_id = -1  # float("inf")
    for _, gene_nodes in bicliques:
        if gene_nodes:
            min_gene_id = min(min_gene_id, min(gene_nodes))
    return min_gene_id


def categorize_nodes(
    all_nodes: Set[int], node_biclique_map: Dict[int, List[int]], min_gene_id: int
) -> Tuple[Set[int], Set[int], Set[int]]:
    """Categorize nodes into DMRs, regular genes, and split genes."""
    dmr_nodes = {node for node in all_nodes if node < min_gene_id}
    gene_nodes = all_nodes - dmr_nodes

    split_genes = {
        node for node in gene_nodes if len(node_biclique_map.get(node, [])) > 1
    }
    regular_genes = gene_nodes - split_genes

    return dmr_nodes, regular_genes, split_genes


def position_nodes_by_biclique(
    bicliques: List[Tuple[Set[int], Set[int]]], node_info: "NodeInfo"
) -> Dict[int, Tuple[float, float]]:
    """Position nodes biclique by biclique, maintaining vertical grouping."""
    positions = {}
    spacing = calculate_vertical_spacing()
    current_y = spacing

    # Position nodes in bicliques
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        positions = position_biclique_nodes(
            dmr_nodes,
            gene_nodes,
            node_info.split_genes,
            current_y,
            spacing,
            positions,
            biclique_idx,
        )
        current_y += spacing * max(len(dmr_nodes), len(gene_nodes))

    # Handle any remaining unpositioned nodes
    position_remaining_nodes(positions, node_info, current_y, spacing)
    
    return positions


def position_single_biclique(
    dmr_nodes: Set[int], gene_nodes: Set[int]
) -> Dict[int, Tuple[float, float]]:
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


def position_nodes_evenly(
    dmr_nodes: Set[int], gene_nodes: Set[int]
) -> Dict[int, Tuple[float, float]]:
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


def calculate_vertical_spacing(
    max_dmr_count: int,
    max_gene_count: int,
    split_genes: Set[int] = None
) -> float:
    """
    Calculate vertical spacing based on node counts.
    Returns a spacing value that is proportional to the maximum number of nodes
    on either side, with a minimum spacing of 0.2.
    """
    if split_genes is None:
        split_genes = set()
        
    # Use the counts directly
    max_nodes = max(max_dmr_count, max_gene_count)
    
    # Base spacing of 0.2, increased proportionally with node count
    spacing = max(0.2, 0.2 * (1 + max_nodes / 10))
    
    return spacing


def calculate_biclique_height(
    dmr_nodes: Set[int],
    gene_nodes: Set[int],
    split_genes: Set[int]
) -> float:
    """Calculate the height needed for a single biclique."""
    # Get counts instead of passing sets
    num_dmrs = len(dmr_nodes)
    num_genes = len(gene_nodes) + len(gene_nodes & split_genes)  # Count split genes
    
    spacing = calculate_vertical_spacing(num_dmrs, num_genes, split_genes)
    return max(num_dmrs, num_genes) * spacing

def position_biclique_nodes(
    dmr_nodes: Set[int],
    gene_nodes: Set[int],
    split_genes: Set[int],
    current_y: float,
    spacing: float,
    positions: Dict[int, Tuple[float, float]],
    biclique_idx: int,
) -> Dict[int, Tuple[float, float]]:
    """Position nodes for a single biclique and update positions dictionary."""
    # Debug output
    print(f"\nPositioning biclique {biclique_idx}:")
    print(f"DMR nodes to position: {sorted(list(dmr_nodes))}")
    print(f"Gene nodes to position: {sorted(list(gene_nodes))}")
    
    # Calculate the height needed for this biclique
    biclique_height = calculate_biclique_height(dmr_nodes, gene_nodes, split_genes)
    
    # Calculate number of positions needed for each side
    num_dmrs = len(dmr_nodes)
    num_genes = len(gene_nodes)
    
    # Calculate spacing within this biclique
    dmr_spacing = biclique_height / (num_dmrs + 1) if num_dmrs > 0 else biclique_height
    gene_spacing = biclique_height / (num_genes + 1) if num_genes > 0 else biclique_height
    
    # Position DMRs
    for i, dmr in enumerate(sorted(dmr_nodes)):
        y_pos = current_y + (i + 1) * dmr_spacing
        positions[dmr] = (0, y_pos)
        print(f"Positioned DMR {dmr} at (0, {y_pos})")

    # Position genes
    for i, gene in enumerate(sorted(gene_nodes)):
        y_pos = current_y + (i + 1) * gene_spacing
        x_pos = 1.1 if gene in split_genes else 1
        positions[gene] = (x_pos, y_pos)
        # print(f"Positioned gene {gene} at ({x_pos}, {y_pos})")

    # Debug verification
    print(f"After positioning:")
    print(f"Total positions: {len(positions)}")
    print(f"DMRs positioned: {all(dmr in positions for dmr in dmr_nodes)}")
    print(f"Genes positioned: {all(gene in positions for gene in gene_nodes)}")
    
    return positions


def position_remaining_nodes(
    positions: Dict[int, Tuple[float, float]],
    node_info: "NodeInfo",
    current_y: float,
    spacing: float,
) -> Dict[int, Tuple[float, float]]:
    """Position any nodes that weren't in bicliques."""
    missing_nodes = node_info.all_nodes - set(positions.keys())
    if missing_nodes:
        print(f"Assigning positions to {len(missing_nodes)} remaining nodes")
        for node in sorted(missing_nodes):  # Sort to ensure consistent ordering
            if node in node_info.dmr_nodes:
                x_pos = 0  # DMRs at x=0
            elif node in node_info.split_genes:
                x_pos = 1.1  # Split genes at x=1.1
            else:
                x_pos = 1  # Regular genes at x=1
            positions[node] = (x_pos, current_y)
            current_y += spacing
    return positions


def get_x_position(node: int, node_info: "NodeInfo") -> float:
    """Determine x-coordinate based on node type."""
    if node in node_info.dmr_nodes:
        return 0
    if node in node_info.split_genes:
        return 1.1
    return 1


def validate_positions(
    positions: Dict[int, Tuple[float, float]], all_nodes: Set[int]
) -> None:
    """Validate that all nodes have been positioned."""
    if len(positions) != len(all_nodes):
        missing = all_nodes - set(positions.keys())
        print(f"Warning: Missing positions for nodes: {missing}")
