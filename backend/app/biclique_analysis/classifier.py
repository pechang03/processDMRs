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

    EMPTY = auto()  # No nodes
    SIMPLE = auto()  # Basic biclique (1 DMR, 1 gene)
    INTERESTING = auto()  # ≥3 DMRs and ≥3 genes
    COMPLEX = auto()  # Interesting with split genes (multiple interesting bicliques)

    def get_complexity_score(self) -> int:
        """Get numeric complexity score for sorting."""
        # Values are 0-based, so EMPTY=1, SIMPLE=2, etc.
        return self.value - 1

    @classmethod
    def from_string(cls, category: str) -> 'BicliqueSizeCategory':
        """Convert string category name to enum."""
        return cls[category.upper()]


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


def classify_biclique(
    dmr_nodes: Set[int], gene_nodes: Set[int]
) -> BicliqueSizeCategory:
    """Classify a single biclique based on size."""
    if not dmr_nodes or not gene_nodes:
        return BicliqueSizeCategory.EMPTY
    if len(dmr_nodes) == 1 and len(gene_nodes) == 1:
        return BicliqueSizeCategory.SIMPLE
    if (
        len(dmr_nodes) >= _MIN_INTERESTING_SIZE
        and len(gene_nodes) >= _MIN_INTERESTING_SIZE
    ):
        return BicliqueSizeCategory.INTERESTING
    # Note you can't have a complex biclique ona complex component
    return BicliqueSizeCategory.SIMPLE  # Default to simple if not empty/interesting


def classify_component(
    dmr_nodes: Set[int],
    gene_nodes: Set[int],
    bicliques: List[Tuple[Set[int], Set[int]]],
) -> BicliqueSizeCategory:
    """Classify a component based on its bicliques."""
    if not dmr_nodes or not gene_nodes:
        return BicliqueSizeCategory.EMPTY

    # Count interesting bicliques
    interesting_bicliques = [
        b
        for b in bicliques
        if classify_biclique(b[0], b[1]) == BicliqueSizeCategory.INTERESTING
    ]

    if not interesting_bicliques:
        if len(dmr_nodes) == 1 and len(gene_nodes) == 1:
            return BicliqueSizeCategory.SIMPLE
        return BicliqueSizeCategory.SIMPLE

    # If we have multiple bicliques, and at least one is is interesting it's complex
    if len(interesting_bicliques) >= 1 and len(bicliques) > 1:
        return BicliqueSizeCategory.COMPLEX

    return BicliqueSizeCategory.INTERESTING


def is_complex(bicliques: List[Tuple[Set[int], Set[int]]]) -> bool:
    """Helper to check if a set of bicliques forms a complex component."""
    interesting_count = sum(
        1
        for b in bicliques
        if classify_biclique(b[0], b[1]) == BicliqueSizeCategory.INTERESTING
    )
    return interesting_count > 1


def classify_biclique_types(
    bicliques: List[Tuple[Set[int], Set[int]]],
) -> Dict[str, int]:
    """
    Classify all bicliques and return count of each type.

    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples

    Returns:
        Dictionary mapping category names to counts
    """
    type_counts = {cat.name.lower(): 0 for cat in BicliqueSizeCategory}

    for dmr_nodes, gene_nodes in bicliques:
        category = classify_biclique(dmr_nodes, gene_nodes)
        type_counts[category.name.lower()] += 1

    return type_counts
