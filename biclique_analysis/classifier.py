# File : classifier.py
# Description : This file defines the edge classifier module
#
"""Classification functionality for bicliques and components"""

from typing import Set, List, Tuple, Dict, NamedTuple
from dataclasses import dataclass
import warnings

# Constants
MIN_INTERESTING_SIZE = (
    3  # Single source of truth for what makes a biclique "interesting"
)


@dataclass
class BicliqueCounts:
    """Container for counts of different biclique types"""

    empty: int = 0
    simple: int = 0
    normal: int = 0
    interesting: int = 0
    complex: int = 0

    def to_dict(self) -> Dict[str, int]:
        """Convert counts to dictionary format"""
        return {
            "empty": self.empty,
            "simple": self.simple,
            "normal": self.normal,
            "interesting": self.interesting,
            "complex": self.complex,
        }


@dataclass
class ClassifiedBicliques:
    """Container for classified bicliques"""

    empty: List[Tuple[Set[int], Set[int]]] = None
    simple: List[Tuple[Set[int], Set[int]]] = None
    normal: List[Tuple[Set[int], Set[int]]] = None
    interesting: List[Tuple[Set[int], Set[int]]] = None
    complex: List[Tuple[Set[int], Set[int]]] = None
    counts: BicliqueCounts = None

    def __post_init__(self):
        """Initialize empty lists if None"""
        self.empty = self.empty or []
        self.simple = self.simple or []
        self.normal = self.normal or []
        self.interesting = self.interesting or []
        self.complex = self.complex or []
        self.counts = self.counts or BicliqueCounts()


def classify_bicliques(
    bicliques: List[Tuple[Set[int], Set[int]]],
) -> ClassifiedBicliques:
    """
    Main public interface for classifying bicliques.
    Returns all classified bicliques and their counts.

    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples

    Returns:
        ClassifiedBicliques object containing categorized lists and counts
    """
    result = ClassifiedBicliques()

    if not bicliques:
        result.counts.empty = 1
        return result

    for dmr_nodes, gene_nodes in bicliques:
        biclique = (dmr_nodes, gene_nodes)
        if len(dmr_nodes) <= 1 and len(gene_nodes) <= 1:
            result.simple.append(biclique)
            result.counts.simple += 1
        elif (
            len(dmr_nodes) >= MIN_INTERESTING_SIZE
            and len(gene_nodes) >= MIN_INTERESTING_SIZE
        ):
            result.interesting.append(biclique)
            result.counts.interesting += 1
            if len(bicliques) > 2:  # Complex if more than 2 bicliques
                result.complex.append(biclique)
                result.counts.complex += 1
        else:
            result.normal.append(biclique)
            result.counts.normal += 1

    return result


def classify_component(
    dmr_nodes: Set[int],
    gene_nodes: Set[int],
    bicliques: List[Tuple[Set[int], Set[int]]],
) -> str:
    """
    Classify a component based on its bicliques.

    Args:
        dmr_nodes: Set of DMR node IDs
        gene_nodes: Set of gene node IDs
        bicliques: List of bicliques in the component

    Returns:
        Classification string: 'empty', 'simple', 'normal', 'interesting', or 'complex'
    """
    classified = classify_bicliques(bicliques)

    if classified.counts.empty > 0:
        return "empty"
    elif classified.counts.complex > 0:
        return "complex"
    elif classified.counts.interesting > 0:
        return "interesting"
    elif classified.counts.simple > 0 and classified.counts.normal == 0:
        return "simple"
    else:
        return "normal"


# Deprecated functions with warnings
def find_interesting_components(
    bicliques: List[Tuple[Set[int], Set[int]]],
) -> List[Tuple[Set[int], Set[int]]]:
    """
    DEPRECATED: Use classify_bicliques() instead to get all component types.
    Will be removed in future version.
    """
    warnings.warn(
        "find_interesting_components() is deprecated. Use classify_bicliques() to get all component types.",
        DeprecationWarning,
        stacklevel=2,
    )
    return classify_bicliques(bicliques).interesting


def classify_biclique(dmr_nodes: Set[int], gene_nodes: Set[int]) -> str:
    """
    DEPRECATED: Use classify_bicliques() instead.
    Will be removed in future version.
    """
    warnings.warn(
        "classify_biclique() is deprecated. Use classify_bicliques() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    result = classify_bicliques([(dmr_nodes, gene_nodes)])
    if result.counts.simple > 0:
        return "simple"
    elif result.counts.interesting > 0:
        return "interesting"
    else:
        return "normal"

