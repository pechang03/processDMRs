# File: classifier.py
#

from typing import Set, List, Tuple, Dict




def get_biclique_type_counts(
    bicliques: List[Tuple[Set[int], Set[int]]],
) -> Dict[str, int]:
    """
    Count bicliques of each type.

    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples

    Returns:
        Dict mapping classification to count
    """
    counts = {"trivial": 0, "small": 0, "interesting": 0}
    for dmr_nodes, gene_nodes in bicliques:
        classification = classify_biclique(dmr_nodes, gene_nodes)
        counts[classification] += 1
    return counts
