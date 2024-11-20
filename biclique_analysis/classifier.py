# File: classifier.py
#

from typing import Set, List, Tuple, Dict

def classify_biclique(dmr_nodes: Set[int], gene_nodes: Set[int]) -> str:
    """
    Classify a biclique based on its size and structure.

    Args:
        dmr_nodes: Set of DMR node IDs
        gene_nodes: Set of gene node IDs

    Returns:
        str: Classification ('trivial', 'small', or 'interesting')
    """
    if len(dmr_nodes) <= 1 or len(gene_nodes) <= 1:
        return "trivial"
    elif len(dmr_nodes) < 3 or len(gene_nodes) < 3:
        return "small"
    else:
        return "interesting"

def classify_biclique_types(bicliques: List[Tuple[Set[int], Set[int]]]) -> Dict[str, int]:
    """
    Classify all bicliques and count occurrences of each type.

    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples

    Returns:
        Dict mapping classification to count
    """
    type_counts = {
        "trivial": 0,
        "small": 0,
        "interesting": 0
    }
    
    for dmr_nodes, gene_nodes in bicliques:
        classification = classify_biclique(dmr_nodes, gene_nodes)
        type_counts[classification] += 1
        
    return type_counts

def classify_component(dmr_count: int, gene_count: int, bicliques: List[Tuple[Set[int], Set[int]]]) -> str:
    """
    Classify a component based on its size and biclique structure.

    Args:
        dmr_count: Number of DMR nodes
        gene_count: Number of gene nodes
        bicliques: List of bicliques in the component

    Returns:
        str: Classification ('empty', 'simple', 'normal', 'interesting', or 'complex')
    """
    if not bicliques:
        return "empty"
        
    if len(bicliques) == 1:
        dmrs, genes = bicliques[0]
        if len(dmrs) == 1 and len(genes) == 1:
            return "simple"
        return "normal"
        
    # Count interesting bicliques
    interesting_count = sum(
        1 for dmrs, genes in bicliques 
        if len(dmrs) >= 3 and len(genes) >= 3
    )
    
    if interesting_count > 0:
        return "complex" if len(bicliques) > 2 else "interesting"
        
    return "normal"




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
