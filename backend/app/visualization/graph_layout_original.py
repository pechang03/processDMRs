# File : graph_layout_original.py
# visualization/graph_layout_original.py
#

from typing import Dict, Tuple, Set
import networkx as nx
from .base_layout import BaseLayout
from utils.node_info import NodeInfo
from utils.edge_info import EdgeInfo


class OriginalGraphLayout(BaseLayout):
    """Layout algorithm for original graph visualization."""

    def calculate_positions(
        self,
        graph: nx.Graph,
        node_info: NodeInfo,
        layout_type: str = "spring",
        **kwargs,
    ) -> Dict[int, Tuple[float, float]]:
        """Calculate positions using specified layout algorithm."""
        if layout_type == "spring":
            return self._spring_layout(graph, **kwargs)
        elif layout_type == "circular":
            return self._circular_layout(graph, node_info, **kwargs)
        else:
            raise ValueError(f"Unsupported layout type: {layout_type}")

    def _spring_layout(
        self, graph: nx.Graph, k: float = None, iterations: int = 50, **kwargs
    ) -> Dict[int, Tuple[float, float]]:
        """Calculate spring layout positions."""
        k = k or 1 / pow(len(graph), 0.5)  # Default k value
        return nx.spring_layout(graph, k=k, iterations=iterations)

    def _circular_layout(
        self, graph: nx.Graph, node_info: NodeInfo, **kwargs
    ) -> Dict[int, Tuple[float, float]]:
        """Calculate circular layout positions."""
        # Separate DMRs and genes into two concentric circles
        positions = {}
        dmr_radius = 1.0
        gene_radius = 2.0

        # Position DMRs in inner circle
        dmr_positions = nx.circular_layout(graph.subgraph(node_info.dmr_nodes))
        for node, pos in dmr_positions.items():
            positions[node] = (pos[0] * dmr_radius, pos[1] * dmr_radius)

        # Position genes in outer circle
        gene_positions = nx.circular_layout(
            graph.subgraph(node_info.regular_genes | node_info.split_genes)
        )
        for node, pos in gene_positions.items():
            positions[node] = (pos[0] * gene_radius, pos[1] * gene_radius)

        return positions
