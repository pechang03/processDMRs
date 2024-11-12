# File: node_info.py
# Author: Peter Shaw

from typing import Set, Dict


class NodeInfo:
    """Container for node categorization information."""

    def __init__(
        self,
        all_nodes: Set[int],
        dmr_nodes: Set[int],
        regular_genes: Set[int],
        split_genes: Set[int],
        node_degrees: Dict[int, int],
        min_gene_id: int,
    ):
        self.all_nodes = all_nodes
        self.dmr_nodes = dmr_nodes
        self.regular_genes = regular_genes
        self.split_genes = split_genes
        self.node_degrees = node_degrees
        self.min_gene_id = min_gene_id

    def is_dmr(self, node: int) -> bool:
        """Check if a node is a DMR."""
        return node in self.dmr_nodes

    def is_split_gene(self, node: int) -> bool:
        """Check if a node is a split gene."""
        return node in self.split_genes

    def get_node_degree(self, node: int) -> int:
        """Get the degree (number of bicliques) for a node."""
        return self.node_degrees.get(node, 0)

    def get_node_type(self, node: int) -> str:
        """Get the type of a node (DMR, split gene, or regular gene)."""
        if self.is_dmr(node):
            return "DMR"
        if self.is_split_gene(node):
            return "split_gene"
        return "regular_gene"
