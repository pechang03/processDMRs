from typing import Dict, Tuple, Set, List
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
        node_biclique_map: Dict[int, List[int]] = None,
        **kwargs,
    ) -> Dict[int, Tuple[float, float]]:
        """Position nodes in concentric circles with biclique-based angular positioning."""
        positions = {}
        import math
        
        # Group nodes by their primary biclique
        biclique_groups = {}
        for node in (dmr_nodes | gene_nodes):
            if node in node_biclique_map and node_biclique_map[node]:
                primary_biclique = min(node_biclique_map[node])  # Use first biclique as primary
                if primary_biclique not in biclique_groups:
                    biclique_groups[primary_biclique] = {
                        'dmrs': set(),
                        'genes': set(),
                        'split_genes': set()
                    }
                
                if node in dmr_nodes:
                    biclique_groups[primary_biclique]['dmrs'].add(node)
                elif node in split_genes:
                    biclique_groups[primary_biclique]['split_genes'].add(node)
                else:
                    biclique_groups[primary_biclique]['genes'].add(node)

        # Calculate angular ranges for each biclique
        num_bicliques = len(biclique_groups)
        angle_per_biclique = 2 * math.pi / num_bicliques
        
        # Position nodes for each biclique
        for biclique_idx, group in biclique_groups.items():
            # Calculate base angle for this biclique
            base_angle = biclique_idx * angle_per_biclique
            
            # Position DMRs in middle circle
            dmr_count = len(group['dmrs'])
            for i, node in enumerate(sorted(group['dmrs'])):
                angle = base_angle + (i / max(1, dmr_count - 1)) * (angle_per_biclique * 0.8)
                radius = 1.75  # Middle circle (unchanged)
                positions[node] = (
                    radius * math.cos(angle),
                    radius * math.sin(angle)
                )
            
            # Position regular genes in outer circle
            gene_count = len(group['genes'])
            for i, node in enumerate(sorted(group['genes'])):
                angle = base_angle + (i / max(1, gene_count - 1)) * (angle_per_biclique * 0.8)
                radius = 2.5  # Outer circle (was 1.0)
                positions[node] = (
                    radius * math.cos(angle),
                    radius * math.sin(angle)
                )
        
        # Position split genes in inner circle
        for node in split_genes:
            if node in node_biclique_map:
                bicliques = node_biclique_map[node]
                if len(bicliques) > 1:
                    # Calculate average angle between involved bicliques
                    angles = [biclique_idx * angle_per_biclique for biclique_idx in bicliques]
                    avg_angle = sum(angles) / len(angles)
                    radius = 1.0  # Inner circle (was 2.5)
                    positions[node] = (
                        radius * math.cos(avg_angle),
                        radius * math.sin(avg_angle)
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
        node_biclique_map: Dict[int, List[int]] = None,
        **kwargs,
    ) -> Dict[int, Tuple[float, float]]:
        """Position nodes in concentric circles with biclique-based angular positioning."""
        positions = {}
        import math
        
        # Initialize empty node_biclique_map if None
        if node_biclique_map is None:
            node_biclique_map = {}
        
        # Add debug logging
        print(f"Positioning {len(dmr_nodes)} DMRs, {len(gene_nodes)} genes, {len(split_genes)} split genes")
        
        # Group nodes by their primary biclique
        biclique_groups = {}
        for node in (dmr_nodes | gene_nodes):
            # Get bicliques for this node, defaulting to [0] if none found
            node_bicliques = node_biclique_map.get(node, [0])
            primary_biclique = min(node_bicliques)
            
            if primary_biclique not in biclique_groups:
                biclique_groups[primary_biclique] = {
                    'dmrs': set(),
                    'genes': set(),
                    'split_genes': set()
                }
            
            if node in dmr_nodes:
                biclique_groups[primary_biclique]['dmrs'].add(node)
            elif node in split_genes:
                biclique_groups[primary_biclique]['split_genes'].add(node)
            else:
                biclique_groups[primary_biclique]['genes'].add(node)

        # Ensure we have at least one biclique group
        if not biclique_groups:
            biclique_groups[0] = {
                'dmrs': dmr_nodes,
                'genes': gene_nodes - split_genes,
                'split_genes': split_genes
            }

        # Calculate angular ranges for each biclique
        num_bicliques = max(1, len(biclique_groups))
        angle_per_biclique = 2 * math.pi / num_bicliques

        # Position nodes for each biclique
        for biclique_idx, group in biclique_groups.items():
            # Calculate base angle for this biclique
            base_angle = biclique_idx * angle_per_biclique
            
            # Position DMRs in middle circle
            dmr_count = len(group['dmrs'])
            for i, node in enumerate(sorted(group['dmrs'])):
                angle = base_angle + (i / max(1, dmr_count - 1)) * (angle_per_biclique * 0.8)
                radius = 1.75  # Middle circle (unchanged)
                positions[node] = (
                    radius * math.cos(angle),
                    radius * math.sin(angle)
                )
            
            # Position regular genes in outer circle
            gene_count = len(group['genes'])
            for i, node in enumerate(sorted(group['genes'])):
                angle = base_angle + (i / max(1, gene_count - 1)) * (angle_per_biclique * 0.8)
                radius = 2.5  # Outer circle (was 1.0)
                positions[node] = (
                    radius * math.cos(angle),
                    radius * math.sin(angle)
                )
        
        # Position split genes in inner circle
        for node in split_genes:
            if node in node_biclique_map:
                bicliques = node_biclique_map[node]
                if len(bicliques) > 1:
                    # Calculate average angle between involved bicliques
                    angles = [biclique_idx * angle_per_biclique for biclique_idx in bicliques]
                    avg_angle = sum(angles) / len(angles)
                    radius = 1.0  # Inner circle (was 2.5)
                    positions[node] = (
                        radius * math.cos(avg_angle),
                        radius * math.sin(avg_angle)
                    )
        
        return positions
