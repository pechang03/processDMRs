# visualization/graph_original_spring.py
from typing import Dict, Tuple, Set
import networkx as nx
from .base_layout import BaseLogicalLayout
from backend.app.utils.node_info import NodeInfo


class SpringLogicalLayout(BaseLogicalLayout):
    """Logical layout using spring embedding."""

    def calculate_positions(
        self, graph: nx.Graph, node_info: NodeInfo, **kwargs
    ) -> Dict[int, Tuple[float, float]]:
        """Calculate positions using spring embedding with constraints."""
        # Get initial positions using spring layout
        initial_pos = nx.spring_layout(graph)

        # Apply logical constraints
        return self.position_nodes(
            node_info.dmr_nodes,
            node_info.regular_genes,
            node_info.split_genes,
            initial_positions=initial_pos,
            **kwargs,
        )

    def position_nodes(
        self,
        dmr_nodes: Set[int],
        gene_nodes: Set[int],
        split_genes: Set[int],
        initial_positions: Dict[int, Tuple[float, float]] = None,
        **kwargs,
    ) -> Dict[int, Tuple[float, float]]:
        """Apply logical constraints to spring layout positions."""
        positions = {}

        # Use initial positions as base
        if initial_positions:
            positions.update(initial_positions)

        # Adjust x-coordinates to maintain DMR/gene separation
        min_x = min(pos[0] for pos in positions.values())
        max_x = max(pos[0] for pos in positions.values())
        x_range = max_x - min_x

        for node in positions:
            x, y = positions[node]

            # Normalize x position
            norm_x = (x - min_x) / x_range if x_range > 0 else 0.5

            # Adjust based on node type
            if node in dmr_nodes:
                new_x = norm_x * 0.4  # DMRs in left 40%
            elif node in split_genes:
                new_x = 0.6 + norm_x * 0.4  # Split genes in right 40%
            else:
                new_x = 0.4 + norm_x * 0.2  # Regular genes in middle 20%

            positions[node] = (new_x, y)

        return positions
