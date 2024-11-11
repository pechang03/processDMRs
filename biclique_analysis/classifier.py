from typing import Set

def classify_biclique(dmr_nodes: Set[int], gene_nodes: Set[int]) -> str:
    """
    Classify a biclique based on its size and characteristics.
    
    Args:
        dmr_nodes: Set of DMR node IDs
        gene_nodes: Set of gene node IDs
        
    Returns:
        str: Classification ('trivial', 'small', or 'interesting')
    """
    if len(dmr_nodes) == 1 and len(gene_nodes) == 1:
        return "trivial"
    elif len(dmr_nodes) >= 3 and len(gene_nodes) >= 3:
        return "interesting"
    else:
        return "small"

def get_biclique_type_counts(bicliques: List[Tuple[Set[int], Set[int]]]) -> Dict[str, int]:
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
from typing import Set, List, Tuple, Dict

def classify_biclique(dmr_nodes: Set[int], gene_nodes: Set[int]) -> str:
    """
    Classify a biclique based on its size and characteristics.
    
    Args:
        dmr_nodes: Set of DMR node IDs
        gene_nodes: Set of gene node IDs
        
    Returns:
        str: Classification ('trivial', 'small', or 'interesting')
    """
    if len(dmr_nodes) == 1 and len(gene_nodes) == 1:
        return "trivial"
    elif len(dmr_nodes) >= 3 and len(gene_nodes) >= 3:
        return "interesting"
    else:
        return "small"

def get_biclique_type_counts(bicliques: List[Tuple[Set[int], Set[int]]]) -> Dict[str, int]:
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
from typing import Set, List, Tuple, Dict

def classify_biclique(dmr_nodes: Set[int], gene_nodes: Set[int]) -> str:
    """
    Classify a biclique based on its size and characteristics.
    
    Args:
        dmr_nodes: Set of DMR node IDs
        gene_nodes: Set of gene node IDs
        
    Returns:
        str: Classification ('trivial', 'small', or 'interesting')
    """
    if len(dmr_nodes) == 1 and len(gene_nodes) == 1:
        return "trivial"
    elif len(dmr_nodes) >= 3 and len(gene_nodes) >= 3:
        return "interesting"
    else:
        return "small"

def get_biclique_type_counts(bicliques: List[Tuple[Set[int], Set[int]]]) -> Dict[str, int]:
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
