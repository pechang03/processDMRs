from typing import Dict, Tuple, Set
import networkx as nx
from .base_layout import BaseLogicalLayout
from backend.app.utils.node_info import NodeInfo
from .graph_layout_logical import (
    calculate_node_positions,
    collect_node_information,
    position_nodes_by_biclique,
)
from .graph_layout import (
    adjust_positions_for_display,
    create_visual_layout,
    create_axis_layout,
    calculate_plot_height,
)


class CircularBicliqueLayout(BaseLogicalLayout):
    """Circular layout algorithm for biclique visualization."""

    def calculate_positions(
        self, graph: nx.Graph, node_info: NodeInfo, **kwargs
    ) -> Dict[int, Tuple[float, float]]:
        """Calculate positions for biclique visualization."""
        # Create a subgraph containing only the nodes we want to position
        nodes_to_position = node_info.all_nodes
        subgraph = graph.subgraph(nodes_to_position)
        
        # Get initial positions using circular layout for the subgraph
        initial_pos = nx.circular_layout(subgraph)

        # Apply logical constraints
        positions = self.position_nodes(
            node_info.dmr_nodes,
            node_info.regular_genes,
            node_info.split_genes,
            initial_positions=initial_pos,
            **kwargs,
        )

        return positions

    def position_nodes(
        self,
        dmr_nodes: Set[int],
        gene_nodes: Set[int],
        split_genes: Set[int],
        initial_positions: Dict[int, Tuple[float, float]] = None,
        **kwargs,
    ) -> Dict[int, Tuple[float, float]]:
        """Position nodes in three concentric circles."""
        positions = {}
        
        # Calculate angles based on initial positions
        for node, (x, y) in initial_positions.items():
            # Calculate angle from initial position
            import math
            angle = math.atan2(y, x)
            
            # Determine radius based on node type
            if node in split_genes:
                radius = 2.5  # Outer circle
            elif node in dmr_nodes:
                radius = 1.75  # Middle circle
            else:
                radius = 1.0  # Inner circle (regular genes)
                
            # Calculate new position
            positions[node] = (
                radius * math.cos(angle),
                radius * math.sin(angle)
            )
        
        return positions


class RectangularBicliqueLayout(BaseLogicalLayout):
    """Circular layout algorithm for biclique visualization."""

    def calculate_positions(
        self, graph: nx.Graph, node_info: NodeInfo, **kwargs
    ) -> Dict[int, Tuple[float, float]]:
        """Calculate positions for biclique visualization."""
        # Get initial positions using circular layout
        initial_pos = nx.circular_layout(graph)

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
        """Position nodes in circular layout with logical constraints."""
        base_positions = {}

        # Use initial positions as base
        if initial_positions:
            base_positions.update(initial_positions)

        return adjust_positions_for_display(base_positions)
