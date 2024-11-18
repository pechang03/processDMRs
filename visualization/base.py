from abc import ABC, abstractmethod
from typing import Dict, List, Set, Tuple
import networkx as nx
from biclique_analysis import classify_edges
from biclique_analysis import classify_edges


class GraphVisualization(ABC):
    """Abstract base class for graph visualizations."""

    @abstractmethod
    def create_visualization(
        self,
        graph: nx.Graph,
        node_labels: Dict[int, str],
        node_positions: Dict[int, Tuple[float, float]],
        original_node_positions: Dict[int, Tuple[float, float]] = None,  # Original positions
        edge_classifications: Dict[str, Set[Tuple[int, int]]] = None,
        node_metadata: Dict[int, Dict] = None,
        **kwargs,
    ) -> str:
        """
        Create visualization of the graph.

        Args:
            graph: NetworkX graph to visualize
            node_labels: Mapping of node IDs to display labels
            node_positions: Mapping of node IDs to (x,y) coordinates
            edge_classifications: Dict of edge sets (permanent, false_positive, false_negative
            node_metadata: Additional node information for tooltips/display
            **kwargs: Additional visualization-specific parameters

        Returns:
            JSON string containing the visualization data
        """
        pass

    def _get_edge_traces(
        self,
        edges: Set[Tuple[int, int]],
        node_positions: Dict[int, Tuple[float, float]],
    ) -> Tuple[List[float], List[float]]:
        """
        Helper to get x,y coordinates for edges.

        Args:
            edges: Set of (source, target) node pairs
            node_positions: Dict mapping node IDs to (x,y) coordinates

        Returns:
            Tuple of (x_coordinates, y_coordinates) for plotting
        """
        edge_x = []
        edge_y = []

        for edge in edges:
            x0, y0 = node_positions[edge[0]]
            x1, y1 = node_positions[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        return edge_x, edge_y
