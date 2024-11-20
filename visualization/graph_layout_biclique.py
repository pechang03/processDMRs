from typing import Dict, Tuple, Set
import networkx as nx
from .base_layout import BaseLogicalLayout
from .node_info import NodeInfo

class CircularBicliqueLayout(BaseLogicalLayout):
    """Circular layout algorithm for biclique visualization."""
    
    def calculate_positions(self,
                          graph: nx.Graph,
                          node_info: NodeInfo,
                          **kwargs) -> Dict[int, Tuple[float, float]]:
        """Calculate positions for biclique visualization."""
        # Get initial positions using circular layout
        initial_pos = nx.circular_layout(graph)
        
        # Apply logical constraints
        return self.position_nodes(
            node_info.dmr_nodes,
            node_info.regular_genes,
            node_info.split_genes,
            initial_positions=initial_pos,
            **kwargs
        )
    
    def position_nodes(self,
                      dmr_nodes: Set[int],
                      gene_nodes: Set[int],
                      split_genes: Set[int],
                      initial_positions: Dict[int, Tuple[float, float]] = None,
                      **kwargs) -> Dict[int, Tuple[float, float]]:
        """Position nodes in circular layout with logical constraints."""
        positions = {}
        
        # Use initial positions as base
        if initial_positions:
            positions.update(initial_positions)
            
        # Adjust positions to maintain DMR/gene separation
        for node in positions:
            x, y = positions[node]
            
            # Normalize angle
            angle = (y + 1) * 3.14159  # Convert to radians
            
            # Adjust radius based on node type
            if node in dmr_nodes:
                radius = 1.0  # DMRs on inner circle
            elif node in split_genes:
                radius = 2.5  # Split genes on outer circle
            else:
                radius = 1.75  # Regular genes on middle circle
                
            # Calculate new position
            new_x = radius * x
            new_y = radius * y
            
            positions[node] = (new_x, new_y)
            
        return positions
from typing import Dict, Tuple, Set
import networkx as nx
from .base_layout import BaseLogicalLayout
from .node_info import NodeInfo

class CircularBicliqueLayout(BaseLogicalLayout):
    """Circular layout algorithm for biclique visualization."""
    
    def calculate_positions(self,
                          graph: nx.Graph,
                          node_info: NodeInfo,
                          **kwargs) -> Dict[int, Tuple[float, float]]:
        """Calculate positions for biclique visualization."""
        # Get initial positions using circular layout
        initial_pos = nx.circular_layout(graph)
        
        # Apply logical constraints
        return self.position_nodes(
            node_info.dmr_nodes,
            node_info.regular_genes,
            node_info.split_genes,
            initial_positions=initial_pos,
            **kwargs
        )
    
    def position_nodes(self,
                      dmr_nodes: Set[int],
                      gene_nodes: Set[int],
                      split_genes: Set[int],
                      initial_positions: Dict[int, Tuple[float, float]] = None,
                      **kwargs) -> Dict[int, Tuple[float, float]]:
        """Position nodes in circular layout with logical constraints."""
        positions = {}
        
        # Use initial positions as base
        if initial_positions:
            positions.update(initial_positions)
            
        # Adjust positions to maintain DMR/gene separation
        for node in positions:
            x, y = positions[node]
            
            # Normalize angle
            angle = (y + 1) * 3.14159  # Convert to radians
            
            # Adjust radius based on node type
            if node in dmr_nodes:
                radius = 1.0  # DMRs on inner circle
            elif node in split_genes:
                radius = 2.5  # Split genes on outer circle
            else:
                radius = 1.75  # Regular genes on middle circle
                
            # Calculate new position
            new_x = radius * x
            new_y = radius * y
            
            positions[node] = (new_x, new_y)
            
        return positions
