# Author: Peter Shaw

from typing import Tuple, Set

class EdgeInfo:
    """Container for edge information and metadata."""

    def __init__(
        self,
        edge: Tuple[int, int],
        label: str = "permanent",  # 'permanent', 'false_positive', 'false_negative'
        sources: Set[str] = None,  # E.g., {'Gene_Symbol_Nearby', 'ENCODE_Enhancer_Interaction(BingRen_Lab)'}
    ):
        """
        Initialize EdgeInfo.

        Args:
            edge: A tuple representing the edge (node1, node2)
            label: Classification label for the edge
            sources: Set of sources where the edge comes from
        """
        self.edge = edge
        self.label = label
        self.sources = sources or set()

    def add_source(self, source: str):
        """Add a source to the edge."""
        self.sources.add(source)

    def to_dict(self):
        """Convert EdgeInfo to a dictionary (useful for JSON serialization)."""
        return {
            "edge": self.edge,
            "label": self.label,
            "sources": list(self.sources),
        }
