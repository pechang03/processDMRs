import unittest
import networkx as nx

# from biclique_analysis.classifier import BicliqueSizeCategory
from utils.constants import START_GENE_ID
from biclique_analysis.statistics import (
    calculate_coverage_statistics,
    calculate_biclique_statistics,
    calculate_size_distribution,
    calculate_node_participation,
    calculate_edge_coverage,
    InvalidGraphError,
    # validate_graph,
)


class TestStatistics(unittest.TestCase):
    def setUp(self):
        """Set up test graph with two overlapping K_{3,3} bicliques"""
        self.graph = nx.Graph()

        # First add all nodes to the graph with correct bipartite attributes
        # DMR nodes (0-5)
        for n in range(6):  # 6 DMR nodes total
            self.graph.add_node(n, bipartite=0)

        # Gene nodes (START_GENE_ID to START_GENE_ID+4)
        for n in range(5):  # 5 gene nodes total
            self.graph.add_node(START_GENE_ID + n, bipartite=1)

        # Add edges for first K_{3,3} biclique
        for n in [0, 1, 2]:
            for m in [START_GENE_ID, START_GENE_ID + 1, START_GENE_ID + 2]:
                self.graph.add_edge(n, m)

        # Add edges for second K_{3,3} biclique (overlapping with first)
        for n in [3, 4, 5]:
            for m in [START_GENE_ID + 2, START_GENE_ID + 3, START_GENE_ID + 4]:
                self.graph.add_edge(n, m)

        # Define two overlapping bicliques
        self.bicliques = [
            (
                {0, 1, 2},  # First biclique DMRs
                {
                    START_GENE_ID,
                    START_GENE_ID + 1,
                    START_GENE_ID + 2,
                },  # First biclique genes
            ),
            (
                {3, 4, 5},  # Second biclique DMRs
                {
                    START_GENE_ID + 2,
                    START_GENE_ID + 3,
                    START_GENE_ID + 4,
                },  # Second biclique genes (note overlap at START_GENE_ID + 2)
            ),
        ]

    def test_calculate_coverage_statistics(self):
        coverage_stats = calculate_coverage_statistics(self.bicliques, self.graph)
        self.assertEqual(coverage_stats["dmrs"]["covered"], 6)  # All 6 DMRs covered
        self.assertEqual(coverage_stats["dmrs"]["total"], 6)
        self.assertEqual(coverage_stats["dmrs"]["percentage"], 1.0)
        self.assertEqual(coverage_stats["genes"]["covered"], 5)  # All 5 genes covered
        self.assertEqual(coverage_stats["genes"]["total"], 5)
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
            biclique_stats["node_participation"]["dmrs"][1], 6
        )  # 3 DMRs appear in 1 biclique
        self.assertEqual(
            biclique_stats["node_participation"]["genes"][1], 4
        )  # 4 genes appear in 1 biclique
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
        self.assertEqual(size_dist[(3, 3)], 2)  # Two bicliques of size (3,3)

    def test_calculate_edge_coverage(self):
        edge_coverage = calculate_edge_coverage(self.bicliques, self.graph)
        self.assertEqual(
            edge_coverage["single_coverage"], 18
        )  # Each biclique has 9 edges
        self.assertEqual(
            edge_coverage["multiple_coverage"], 0
        )  # No edges are covered multiple times
        self.assertEqual(edge_coverage["uncovered"], 0)
        self.assertEqual(edge_coverage["total"], 18)

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

        # Each DMR appears in exactly one biclique
        self.assertEqual(node_participation["dmrs"][1], 6)  # All 6 DMRs appear once

        # Most genes appear in one biclique, but one gene appears in both
        self.assertEqual(node_participation["genes"][1], 4)  # 4 genes appear once
        self.assertEqual(
            node_participation["genes"][2], 1
        )  # 1 gene appears twice (the overlap)


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
        self.assertEqual(edge_coverage["single_coverage"], 3)
        self.assertEqual(edge_coverage["multiple_coverage"], 0)
        self.assertEqual(edge_coverage["uncovered"], 0)


if __name__ == "__main__":
    unittest.main()
