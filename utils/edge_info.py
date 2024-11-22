# Author: Peter Shaw

from typing import Tuple, Set

class EdgeInfo:
    """Container for edge information and metadata."""

    VALID_LABELS = {
        "permanent",           # Edge present in both graphs
        "false_positive",      # Edge in original but not biclique
        "false_negative",      # Edge in biclique but not original
        "bridge_false_positive", # Bridge edge likely to be noise
        "potential_true_bridge", # Bridge edge that may be legitimate
    }

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
        if label not in self.VALID_LABELS:
            raise ValueError(f"Invalid label: {label}")
            
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
