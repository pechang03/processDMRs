# File: utils.py
# Author: Peter Shaw
#
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
        # Convert to sets if they're lists
        dmr_set = set(dmr_nodes) if isinstance(dmr_nodes, list) else dmr_nodes
        gene_set = set(gene_nodes) if isinstance(gene_nodes, list) else gene_nodes

        # Process DMR nodes
        for node in dmr_set:
            if node not in node_biclique_map:
                node_biclique_map[node] = []
            node_biclique_map[node].append(biclique_idx)

        # Process gene nodes
        for node in gene_set:
            if node not in node_biclique_map:
                node_biclique_map[node] = []
            node_biclique_map[node].append(biclique_idx)

    return node_biclique_map


def get_node_position(
    node_id: int,
    node_positions: Dict[int, Tuple[float, float]],
    default: Tuple[float, float] = None,
) -> Tuple[float, float]:
    """
    Safely get and validate a node's position.

    Args:
        node_id: ID of the node
        node_positions: Dictionary mapping node IDs to (x,y) coordinates
        default: Optional default position to return if position is invalid

    Returns:
        Tuple of (x,y) coordinates or default if position is invalid

    Example:
        >>> positions = {1: (0.5, 1.0), 2: (1.0, 0.5)}
        >>> get_node_position(1, positions)
        (0.5, 1.0)
        >>> get_node_position(3, positions, default=(0,0))
        (0, 0)
    """
    position = node_positions.get(node_id)

    if position is None:
        if default is not None:
            return default
        raise ValueError(f"No position found for node {node_id}")

    if not isinstance(position, tuple) or len(position) != 2:
        if default is not None:
            return default
        raise ValueError(f"Invalid position format for node {node_id}: {position}")

    return position
