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
        self, 
        graph: nx.Graph, 
        node_info: NodeInfo, 
        node_biclique_map: Dict[int, List[int]] = None,
        **kwargs
    ) -> Dict[int, Tuple[float, float]]:
        """Calculate positions for biclique visualization."""
        # Create a subgraph containing only the nodes we want to position
        nodes_to_position = node_info.all_nodes
        subgraph = graph.subgraph(nodes_to_position)
        
        # Get initial positions using circular layout for the subgraph
        initial_pos = nx.circular_layout(subgraph)

        # Apply logical constraints with biclique information
        positions = self.position_nodes(
            node_info.dmr_nodes,
            node_info.regular_genes,
            node_info.split_genes,
            initial_positions=initial_pos,
            node_biclique_map=node_biclique_map,
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
                primary_biclique = min(node_biclique_map[node])
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
        
        # Position DMRs and regular genes for each biclique
        for biclique_idx, group in biclique_groups.items():
            base_angle = biclique_idx * angle_per_biclique
            
            # Position DMRs in middle circle
            dmr_count = len(group['dmrs'])
            for i, node in enumerate(sorted(group['dmrs'])):
                angle = base_angle + (i / max(1, dmr_count - 1)) * (angle_per_biclique * 0.8)
                radius = 1.75
                positions[node] = (
                    radius * math.cos(angle),
                    radius * math.sin(angle)
                )
            
            # Position regular genes in outer circle
            gene_count = len(group['genes'])
            for i, node in enumerate(sorted(group['genes'])):
                angle = base_angle + (i / max(1, gene_count - 1)) * (angle_per_biclique * 0.8)
                radius = 2.5
                positions[node] = (
                    radius * math.cos(angle),
                    radius * math.sin(angle)
                )
    
        # Group split genes by their biclique combinations
        split_gene_groups = {}
        for node in split_genes:
            if node in node_biclique_map:
                bicliques = tuple(sorted(node_biclique_map[node]))
                if bicliques not in split_gene_groups:
                    split_gene_groups[bicliques] = []
                split_gene_groups[bicliques].append(node)
    
        # Position split genes
        for bicliques, nodes in split_gene_groups.items():
            # Calculate angles for all involved bicliques
            angles = [idx * angle_per_biclique for idx in bicliques]
        
            # For each pair of consecutive bicliques in the set
            for i in range(len(bicliques) - 1):
                start_biclique = bicliques[i]
                end_biclique = bicliques[i + 1]
            
                # Calculate start and end angles
                start_angle = start_biclique * angle_per_biclique
                end_angle = end_biclique * angle_per_biclique
            
                # Handle case where angles cross the 2π boundary
                if end_angle < start_angle:
                    end_angle += 2 * math.pi
            
                # Calculate total angular range
                angle_range = end_angle - start_angle
            
                # Calculate number of nodes to position in this range
                nodes_in_range = len(nodes)
            
                # Distribute nodes evenly across the full range
                for j, node in enumerate(sorted(nodes)):
                    angle = start_angle + (j / max(1, nodes_in_range - 1)) * angle_range
                    # Normalize angle back to [0, 2π]
                    angle = angle % (2 * math.pi)
                    radius = 1.0  # Inner circle
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
        node_biclique_map: Dict[int, List[int]] = None,
        **kwargs,
    ) -> Dict[int, Tuple[float, float]]:
        """Position nodes in concentric circles with biclique-based angular positioning."""
        positions = {}
        import math
        
        # Initialize empty node_biclique_map if None
        if node_biclique_map is None:
            node_biclique_map = {}
        
        # First, calculate split gene weights for each biclique
        split_gene_weights = {}  # biclique_id -> weight
        for gene in split_genes:
            bicliques = node_biclique_map.get(gene, [])
            if bicliques:
                weight = 1.0 / len(bicliques)  # Split weight across bicliques
                for b in bicliques:
                    split_gene_weights[b] = split_gene_weights.get(b, 0) + weight

        # Group nodes by their primary biclique
        biclique_groups = {}
        for node in (dmr_nodes | gene_nodes):
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

        # Calculate angles based on weighted counts
        biclique_angles = {}
        total_angle_needed = 0
        for biclique_idx, group in biclique_groups.items():
            dmr_count = len(group['dmrs'])
            gene_count = len(group['genes'])
            split_count = split_gene_weights.get(biclique_idx, 0)
            
            max_count = max(dmr_count, gene_count, split_count)
            biclique_angles[biclique_idx] = max_count
            total_angle_needed += max_count

        # Calculate angle per unit to distribute full circle
        angle_per_unit = 2 * math.pi / total_angle_needed if total_angle_needed > 0 else 0
        
        # Calculate starting angle for each biclique
        current_angle = 0
        biclique_start_angles = {}
        for biclique_idx in sorted(biclique_groups.keys()):
            biclique_start_angles[biclique_idx] = current_angle
            current_angle += biclique_angles[biclique_idx] * angle_per_unit

        # Position nodes for each biclique
        for biclique_idx, group in biclique_groups.items():
            start_angle = biclique_start_angles[biclique_idx]
            total_angle = biclique_angles[biclique_idx] * angle_per_unit
            
            # Position DMRs in middle circle
            for i, node in enumerate(sorted(group['dmrs'])):
                angle = start_angle + (i / max(1, len(group['dmrs']))) * total_angle
                radius = 1.75
                positions[node] = (
                    radius * math.cos(angle),
                    radius * math.sin(angle)
                )
            
            # Position regular genes in outer circle
            for i, node in enumerate(sorted(group['genes'])):
                angle = start_angle + (i / max(1, len(group['genes']))) * total_angle
                radius = 2.5
                positions[node] = (
                    radius * math.cos(angle),
                    radius * math.sin(angle)
                )

        # Position split genes between their bicliques
        for node in split_genes:
            if node in node_biclique_map:
                bicliques = sorted(node_biclique_map[node])
                if len(bicliques) > 1:
                    # Calculate average angle between involved bicliques
                    angles = [biclique_start_angles[idx] for idx in bicliques]
                    start_angle = min(angles)
                    end_angle = max(angles)
                    avg_angle = (start_angle + end_angle) / 2
                    radius = 1.0  # Inner circle
                    positions[node] = (
                        radius * math.cos(avg_angle),
                        radius * math.sin(avg_angle)
                    )
    
        return positions
