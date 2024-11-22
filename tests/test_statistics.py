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


class TestStatistics(unittest.TestCase):
    def setUp(self):
        """Set up test graph with two overlapping K_{3,3} bicliques"""
        self.graph = nx.Graph()
        
        # First add all nodes to the graph
        self.graph.add_nodes_from(range(11))  # Add nodes 0-10
        
        # Then set bipartite attributes
        for n in [0, 1, 2, 3, 4, 5]:
            self.graph.nodes[n]["bipartite"] = 0  # DMRs
        for n in [6, 7, 8, 9, 10]:
            self.graph.nodes[n]["bipartite"] = 1  # Genes

        # Add edges for first K_{3,3}
        for n in [0, 1, 2]:
            for m in [6, 7, 8]:
                self.graph.add_edge(n, m)

        # Add edges for second K_{3,3}
        for n in [3, 4, 5]:
            for m in [8, 9, 10]:
                self.graph.add_edge(n, m)

        # Update bicliques to match the graph structure
        self.bicliques = [
            ({0, 1, 2}, {6, 7, 8}),  # First K_{3,3}
            ({3, 4, 5}, {8, 9, 10})  # Second K_{3,3}
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
        self.assertEqual(biclique_stats["size_distribution"][(2, 1)], 1)
        self.assertEqual(biclique_stats["size_distribution"][(1, 2)], 1)
        self.assertEqual(biclique_stats["size_distribution"][(3, 1)], 1)
        self.assertEqual(biclique_stats["coverage"]["dmrs"]["covered"], 3)
        self.assertEqual(biclique_stats["coverage"]["genes"]["covered"], 2)
        self.assertEqual(biclique_stats["node_participation"]["dmrs"][2], 1)
        self.assertEqual(biclique_stats["node_participation"]["genes"][2], 1)
        self.assertEqual(biclique_stats["edge_coverage"]["single"], 3)
        self.assertEqual(biclique_stats["edge_coverage"]["multiple"], 0)
        self.assertEqual(biclique_stats["edge_coverage"]["uncovered"], 3)

        # Verify biclique types are present
        self.assertIn("biclique_types", biclique_stats)
        self.assertIsInstance(biclique_stats["biclique_types"], dict)

    def test_calculate_size_distribution(self):
        size_dist = calculate_size_distribution(self.bicliques)
        self.assertEqual(size_dist[(2, 1)], 2)  # Two bicliques with 2 DMRs and 1 gene

    def test_calculate_node_participation(self):
        node_participation = calculate_node_participation(self.bicliques)
        # DMRs: node 2 appears in 2 bicliques, nodes 0,1 appear in 2 bicliques
        self.assertEqual(
            node_participation["dmrs"][2], 3
        )  # 3 DMRs appear in 2 bicliques
        # Genes: node 3 appears in 2 bicliques, node 4 appears in 2 bicliques
        self.assertEqual(
            node_participation["genes"][2], 2
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


if __name__ == "__main__":
    unittest.main()
