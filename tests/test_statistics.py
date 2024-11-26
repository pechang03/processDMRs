import unittest
import networkx as nx
from biclique_analysis.statistics import (
    calculate_coverage_statistics,
    calculate_biclique_statistics,
    calculate_size_distribution,
    calculate_node_participation,
    calculate_edge_coverage,
    InvalidGraphError,
    validate_graph,
)
from biclique_analysis.classifier import BicliqueSizeCategory
from utils.constants import START_GENE_ID


class TestStatistics(unittest.TestCase):
    def setUp(self):
        """Set up test graph with two overlapping K_{3,3} bicliques"""
        self.graph = nx.Graph()

        # First add all nodes to the graph
        self.graph.add_nodes_from(range(6))  # Add DMR nodes 0-5

        # Then set bipartite attributes
        for n in [0, 1, 2, 3, 4, 5]:
            self.graph.nodes[n]["bipartite"] = 0  # DMRs
        for n in range(5):
            self.graph.add_node(START_GENE_ID + n, bipartite=1)  # Genes

        # Add edges for first K_{3,3}
        for n in [0, 1, 2]:
            for m in [START_GENE_ID, START_GENE_ID + 1, START_GENE_ID + 2]:
                self.graph.add_edge(n, m)

        # Add edges for second K_{3,3}
        for n in [3, 4, 5]:
            for m in [START_GENE_ID + 2, START_GENE_ID + 3, START_GENE_ID + 4]:
                self.graph.add_edge(n, m)

        # Update bicliques to match the graph structure
        self.bicliques = [
            (
                {0, 1, 2},
                {START_GENE_ID, START_GENE_ID + 1, START_GENE_ID + 2},
            ),  # First K_{3,3}
            (
                {3, 4, 5},
                {START_GENE_ID + 2, START_GENE_ID + 3, START_GENE_ID + 4},
            ),  # Second K_{3,3}
        ]

    def test_calculate_coverage_statistics(self):
        coverage_stats = calculate_coverage_statistics(self.bicliques, self.graph)
        self.assertEqual(coverage_stats["dmrs"]["covered"], 3)
        self.assertEqual(coverage_stats["dmrs"]["total"], 3)
        self.assertEqual(coverage_stats["dmrs"]["percentage"], 1.0)
        self.assertEqual(coverage_stats["genes"]["covered"], 2)
        self.assertEqual(coverage_stats["genes"]["total"], 2)
        self.assertEqual(coverage_stats["genes"]["percentage"], 1.0)

    def test_calculate_biclique_statistics(self):
        biclique_stats = calculate_biclique_statistics(self.bicliques, self.graph)
        self.assertEqual(
            biclique_stats["size_distribution"][(3, 3)], 2
        )  # Two bicliques of size 3,3
        self.assertEqual(
            biclique_stats["coverage"]["dmrs"]["covered"], 6
        )  # All 6 DMRs are covered
        self.assertEqual(
            biclique_stats["coverage"]["genes"]["covered"], 5
        )  # All 5 genes are covered
        self.assertEqual(
            biclique_stats["node_participation"]["dmrs"][1], 3
        )  # 3 DMRs appear in 1 biclique
        self.assertEqual(
            biclique_stats["node_participation"]["genes"][1], 3
        )  # 3 genes appear in 1 biclique
        self.assertEqual(
            biclique_stats["node_participation"]["genes"][2], 3
        )  # 1 gene appears in 2 bicliques
        self.assertEqual(biclique_stats["edge_coverage"]["single"], 24)
        self.assertEqual(biclique_stats["edge_coverage"]["multiple"], 3)
        self.assertEqual(biclique_stats["edge_coverage"]["uncovered"], 0)

        # Verify biclique types are present
        self.assertIn("biclique_types", biclique_stats)
        self.assertIsInstance(biclique_stats["biclique_types"], dict)

    def test_calculate_size_distribution(self):
        size_dist = calculate_size_distribution(self.bicliques)
        self.assertEqual(size_dist[(3, 3)], 2)  # Two bicliques with 2 DMRs and 1 gene

    def test_calculate_node_participation(self):
        node_participation = calculate_node_participation(self.bicliques)
        self.assertEqual(
            node_participation["dmrs"][2], 6
        )  # 3 DMRs appear in 2 bicliques
        self.assertEqual(
            node_participation["genes"][8], 2
        )  # 2 genes appear in 2 bicliques

    def test_calculate_edge_coverage(self):
        edge_coverage = calculate_edge_coverage(self.bicliques, self.graph)
        self.assertEqual(edge_coverage["single"], 3)  # 3 edges covered once
        self.assertEqual(
            edge_coverage["multiple"], 0
        )  # No edges covered multiple times
        self.assertEqual(edge_coverage["uncovered"], 1)  # 1 edge not covered
        self.assertEqual(edge_coverage["total"], 4)  # Total of 4 edges in graph

    def test_invalid_graph_structures(self):
        """Test that invalid graph structures raise appropriate exceptions"""
        # Test empty graph
        empty_graph = nx.Graph()
        with self.assertRaises(InvalidGraphError):
            calculate_coverage_statistics([], empty_graph)

        # Test graph with isolated node
        isolated_graph = nx.Graph()
        isolated_graph.add_node(0)
        with self.assertRaises(InvalidGraphError):
            calculate_coverage_statistics([], isolated_graph)

        # Test graph with only DMRs
        dmr_graph = nx.Graph()
        dmr_graph.add_edge(0, 1)
        with self.assertRaises(InvalidGraphError):
            calculate_coverage_statistics([], dmr_graph)

        # Test graph with only genes
        gene_graph = nx.Graph()
        gene_graph.add_edge(3, 4)
        with self.assertRaises(InvalidGraphError):
            calculate_coverage_statistics([], gene_graph)

    def test_calculate_node_participation(self):
        """Test calculation of node participation in bicliques"""
        node_participation = calculate_node_participation(self.bicliques)

        # In our setup:
        # - Each DMR appears in exactly one biclique
        # - Node 8 appears in both bicliques, other genes in one each
        self.assertEqual(
            node_participation["dmrs"][1], 6
        )  # All 6 DMRs appear in 1 biclique
        self.assertEqual(
            node_participation["genes"][1], 4
        )  # 4 genes appear in 1 biclique
        self.assertEqual(
            node_participation["genes"][2], 1
        )  # 1 gene (node 8) appears in 2 bicliques


if __name__ == "__main__":
    unittest.main()


class TestStatisticsEdgeCases(unittest.TestCase):
    def setUp(self):
        """Set up test graph with simple structure"""
        self.graph = nx.Graph()

        # Add nodes
        for n in [0, 1, 2]:
            self.graph.add_node(n, bipartite=0)  # DMRs
        for n in [3, 4, 5]:
            self.graph.add_node(n, bipartite=1)  # Genes

        # Add edges
        self.graph.add_edges_from([(0, 3), (1, 4), (2, 5)])

        # Simple bicliques
        self.bicliques = [({0}, {3}), ({1}, {4}), ({2}, {5})]

    def test_calculate_coverage_statistics(self):
        coverage_stats = calculate_coverage_statistics(self.bicliques, self.graph)
        self.assertEqual(coverage_stats["dmrs"]["covered"], 3)
        self.assertEqual(coverage_stats["genes"]["covered"], 3)
        self.assertEqual(coverage_stats["dmrs"]["percentage"], 1.0)
        self.assertEqual(coverage_stats["genes"]["percentage"], 1.0)

    def test_calculate_edge_coverage(self):
        edge_coverage = calculate_edge_coverage(self.bicliques, self.graph)
        self.assertEqual(edge_coverage["single"], 3)
        self.assertEqual(edge_coverage["multiple"], 0)
        self.assertEqual(edge_coverage["uncovered"], 0)
