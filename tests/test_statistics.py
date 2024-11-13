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

class TestStatistics(unittest.TestCase):
    def setUp(self):
        self.graph = nx.Graph()
        self.graph.add_edges_from([(0, 3), (1, 3), (2, 3), (0, 4), (1, 4), (2, 4)])
        self.bicliques = [
            ({0, 1}, {3}),
            ({2}, {3, 4}),
            ({0, 1, 2}, {4}),
        ]

    def test_calculate_coverage_statistics(self):
        coverage_stats = calculate_coverage_statistics(self.bicliques, self.graph)
        self.assertEqual(coverage_stats["dmrs"]["covered"], 3)
        self.assertEqual(coverage_stats["dmrs"]["total"], 5)
        self.assertEqual(coverage_stats["dmrs"]["percentage"], 0.6)
        self.assertEqual(coverage_stats["genes"]["covered"], 2)
        self.assertEqual(coverage_stats["genes"]["total"], 5)
        self.assertEqual(coverage_stats["genes"]["percentage"], 0.4)

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

    def test_calculate_size_distribution(self):
        size_dist = calculate_size_distribution(self.bicliques)
        self.assertEqual(size_dist[(2, 1)], 1)
        self.assertEqual(size_dist[(1, 2)], 1)
        self.assertEqual(size_dist[(3, 1)], 1)

    def test_calculate_node_participation(self):
        node_participation = calculate_node_participation(self.bicliques)
        self.assertEqual(node_participation["dmrs"][2], 1)
        self.assertEqual(node_participation["genes"][2], 1)

    def test_calculate_edge_coverage(self):
        edge_coverage = calculate_edge_coverage(self.bicliques, self.graph)
        self.assertEqual(edge_coverage["single"], 3)
        self.assertEqual(edge_coverage["multiple"], 0)
        self.assertEqual(edge_coverage["uncovered"], 3)

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

if __name__ == '__main__':
    unittest.main()
