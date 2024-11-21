# File : classifier.py
# Description : This file defines the edge classifier module
#
"""Classification functionality for bicliques and components"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Set, List, Tuple, Dict

# Private constants
_MIN_INTERESTING_SIZE = 3  # Single source of truth

class BicliqueSizeCategory(Enum):
    """Hierarchical categories for bicliques/components"""
    EMPTY = auto()      # No nodes
    SIMPLE = auto()     # Basic biclique (1 DMR, 1 gene)
    INTERESTING = auto() # ≥3 DMRs and ≥3 genes
    COMPLEX = auto()    # Interesting with split genes (multiple interesting bicliques)

@dataclass
class BicliqueSizes:
    """Container for biclique size thresholds"""
    min_interesting: int = _MIN_INTERESTING_SIZE
    min_dmrs: int = 1
    min_genes: int = 1

    def to_tuple(self) -> Tuple[int, int, int]:
        """Get sizes as tuple for unpacking"""
        return (self.min_interesting, self.min_dmrs, self.min_genes)

def get_size_thresholds() -> BicliqueSizes:
    """Get the size thresholds used for classification."""
    return BicliqueSizes()

def classify_biclique(dmr_nodes: Set[int], gene_nodes: Set[int]) -> BicliqueSizeCategory:
    """Classify a single biclique based on size."""
    if not dmr_nodes or not gene_nodes:
        return BicliqueSizeCategory.EMPTY
    if len(dmr_nodes) == 1 and len(gene_nodes) == 1:
        return BicliqueSizeCategory.SIMPLE
    if len(dmr_nodes) >= _MIN_INTERESTING_SIZE and len(gene_nodes) >= _MIN_INTERESTING_SIZE:
        return BicliqueSizeCategory.INTERESTING
    return BicliqueSizeCategory.SIMPLE  # Default to simple if not empty/interesting

def classify_component(
    dmr_nodes: Set[int],
    gene_nodes: Set[int],
    bicliques: List[Tuple[Set[int], Set[int]]]
) -> BicliqueSizeCategory:
    """Classify a component based on its bicliques."""
    if not dmr_nodes or not gene_nodes:
        return BicliqueSizeCategory.EMPTY
        
    # Count interesting bicliques
    interesting_bicliques = [
        b for b in bicliques 
        if classify_biclique(b[0], b[1]) == BicliqueSizeCategory.INTERESTING
    ]
    
    if not interesting_bicliques:
        if len(dmr_nodes) == 1 and len(gene_nodes) == 1:
            return BicliqueSizeCategory.SIMPLE
        return BicliqueSizeCategory.SIMPLE
    
    # If we have multiple interesting bicliques, it's complex
    if len(interesting_bicliques) > 1:
        return BicliqueSizeCategory.COMPLEX
        
    return BicliqueSizeCategory.INTERESTING

def is_complex(bicliques: List[Tuple[Set[int], Set[int]]]) -> bool:
    """Helper to check if a set of bicliques forms a complex component."""
    interesting_count = sum(
        1 for b in bicliques 
        if classify_biclique(b[0], b[1]) == BicliqueSizeCategory.INTERESTING
    )
    return interesting_count > 1

