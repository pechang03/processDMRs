# visualization/base_layout.py
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Set
import networkx as nx
from backend.app.utils.node_info import NodeInfo


class BaseLayout(ABC):
    """Base class for layout algorithms."""

    @abstractmethod
    def calculate_positions(
        self, graph: nx.Graph, node_info: NodeInfo, **kwargs
    ) -> Dict[int, Tuple[float, float]]:
        """Calculate node positions."""
        pass


class BaseLogicalLayout(BaseLayout):
    """Base class for logical layout algorithms."""

    @abstractmethod
    def position_nodes(
        self, dmr_nodes: Set[int], gene_nodes: Set[int], split_genes: Set[int], **kwargs
    ) -> Dict[int, Tuple[float, float]]:
        """Position nodes according to logical rules."""
        pass
