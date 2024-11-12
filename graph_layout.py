"""Core graph layout algorithms"""

from typing import Dict, List, Set, Tuple
from visualization.node_info import NodeInfo

def calculate_node_positions(
    bicliques: List[Tuple[Set[int], Set[int]]], 
    node_biclique_map: Dict[int, List[int]]
) -> Dict[int, Tuple[float, float]]:
    """Calculate base positions for nodes in the graph."""
    node_info = collect_node_information(bicliques, node_biclique_map)
    positions = position_nodes_by_biclique(bicliques, node_info)
    validate_positions(positions, node_info.all_nodes)
    return positions

def collect_node_information(
    bicliques: List[Tuple[Set[int], Set[int]]], 
    node_biclique_map: Dict[int, List[int]]
) -> "NodeInfo":
    """Collect and categorize all nodes from bicliques and map."""
    all_nodes = get_all_nodes(bicliques, node_biclique_map)
    node_degrees = calculate_node_degrees(all_nodes, node_biclique_map)
    min_gene_id = find_min_gene_id(bicliques)

    dmr_nodes, regular_genes, split_genes = categorize_nodes(
        all_nodes, node_biclique_map, min_gene_id
    )

    return NodeInfo(
        all_nodes=all_nodes,
        dmr_nodes=dmr_nodes,
        regular_genes=regular_genes,
        split_genes=split_genes,
        node_degrees=node_degrees,
        min_gene_id=min_gene_id,
    )

def get_all_nodes(
    bicliques: List[Tuple[Set[int], Set[int]]], 
    node_biclique_map: Dict[int, List[int]]
) -> Set[int]:
    """Collect all unique nodes from bicliques and map."""
    all_nodes = set(node_biclique_map.keys())
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        all_nodes.update(dmr_nodes)
        all_nodes.update(gene_nodes)
    return all_nodes

def calculate_node_degrees(
    nodes: Set[int], 
    node_biclique_map: Dict[int, List[int]]
) -> Dict[int, int]:
    """Calculate degree (number of bicliques) for each node."""
    return {node: len(node_biclique_map.get(node, [])) for node in nodes}

def find_min_gene_id(bicliques: List[Tuple[Set[int], Set[int]]]) -> int:
    """Find the minimum gene ID to separate DMRs from genes."""
    min_gene_id = float("inf")
    for _, gene_nodes in bicliques:
        if gene_nodes:
            min_gene_id = min(min_gene_id, min(gene_nodes))
    return min_gene_id

def categorize_nodes(
    all_nodes: Set[int], 
    node_biclique_map: Dict[int, List[int]], 
    min_gene_id: int
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
    bicliques: List[Tuple[Set[int], Set[int]]], 
    node_info: "NodeInfo"
) -> Dict[int, Tuple[float, float]]:
    """Position nodes biclique by biclique, maintaining vertical grouping."""
    positions = {}
    spacing = calculate_vertical_spacing(bicliques)
    current_y = spacing

    # Position nodes in bicliques
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        current_y = position_biclique_nodes(
            dmr_nodes, gene_nodes, node_info.split_genes, current_y, spacing, positions, biclique_idx
        )

    # Handle any remaining unpositioned nodes
    position_remaining_nodes(positions, node_info, current_y, spacing)

    return positions

def calculate_vertical_spacing(bicliques: List[Tuple[Set[int], Set[int]]]) -> float:
    """Calculate vertical spacing between nodes."""
    # Handle empty bicliques case
    if not bicliques:
        return 0.2  # Default spacing for empty case

    # For a single biclique with one node on each side, use 0.5
    if len(bicliques) == 1 and len(bicliques[0][0]) == 1 and len(bicliques[0][1]) == 1:
        return 0.5

    # For multiple bicliques, use fixed spacing of 0.2
    if len(bicliques) > 1:
        return 0.2

    # Calculate max nodes on either side (DMRs vs genes)
    max_side_nodes = max(
        max(len(dmr_nodes) for dmr_nodes, _ in bicliques),  # Max DMRs in any biclique
        max(
            len(gene_nodes) for _, gene_nodes in bicliques
        ),  # Max genes in any biclique
    )

    # Calculate spacing based on maximum nodes on either side
    return 1.0 / (max_side_nodes + 1) if max_side_nodes > 0 else 0.5

def position_biclique_nodes(
    dmr_nodes: Set[int],
    gene_nodes: Set[int],
    split_genes: Set[int],
    current_y: float,
    spacing: float,
    positions: Dict[int, Tuple[float, float]],
    biclique_idx: int
) -> float:
    """Position nodes for a single biclique and return new y position."""
    sorted_dmrs = sorted(dmr_nodes)
    sorted_genes = sorted(gene_nodes)

    # Position DMRs and genes with matching y-coordinates when possible
    max_len = max(len(dmr_nodes), len(gene_nodes))
    for i in range(max_len):
        # Position DMR if available
        if i < len(sorted_dmrs):
            dmr = sorted_dmrs[i]
            positions[dmr] = (0, current_y + i * spacing)

        # Position gene if available
        if i < len(sorted_genes):
            gene = sorted_genes[i]
            x_pos = 1.1 if gene in split_genes else 1
            positions[gene] = (x_pos, current_y + i * spacing)

    # Return position for next biclique
    return current_y + max_len * spacing

def position_remaining_nodes(
    positions: Dict[int, Tuple[float, float]],
    node_info: "NodeInfo",
    current_y: float,
    spacing: float,
) -> None:
    """Position any nodes that weren't in bicliques."""
    missing_nodes = node_info.all_nodes - set(positions.keys())
    if missing_nodes:
        print(f"Assigning positions to {len(missing_nodes)} remaining nodes")
        for node in missing_nodes:
            x_pos = get_x_position(node, node_info)
            positions[node] = (x_pos, current_y)
            current_y += spacing

def get_x_position(node: int, node_info: "NodeInfo") -> float:
    """Determine x-coordinate based on node type."""
    if node in node_info.dmr_nodes:
        return 0
    if node in node_info.split_genes:
        return 1.1
    return 1

def validate_positions(
    positions: Dict[int, Tuple[float, float]], 
    all_nodes: Set[int]
) -> None:
    """Validate that all nodes have been positioned."""
    if len(positions) != len(all_nodes):
        missing = all_nodes - set(positions.keys())
        print(f"Warning: Missing positions for nodes: {missing}")
