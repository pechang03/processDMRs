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
        self.graph = nx.Graph()
        # DMR nodes should be 0,1,2 (3 DMRs)
        # Gene nodes should be 3,4 (2 genes)
        self.graph.add_edges_from([
            (0, 3), (1, 3), (2, 3),  # First gene connected to all DMRs
            (0, 4), (1, 4), (2, 4)   # Second gene connected to all DMRs
        ])
        
        # Add bipartite attributes
        for n in [0, 1, 2]:
            self.graph.nodes[n]['bipartite'] = 0  # DMRs
        for n in [3, 4]:
            self.graph.nodes[n]['bipartite'] = 1  # Genes
        
        # Bicliques should use the same node numbering convention
        self.bicliques = [
            ({0, 1}, {3}),    # First biclique: DMRs 0,1 with gene 3
            ({2}, {3, 4}),    # Second biclique: DMR 2 with genes 3,4
            ({0, 1, 2}, {4})  # Third biclique: All DMRs with gene 4
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

    def test_calculate_size_distribution(self):
        size_dist = calculate_size_distribution(self.bicliques)
        self.assertEqual(size_dist[(2, 1)], 1)
        self.assertEqual(size_dist[(1, 2)], 1)
        self.assertEqual(size_dist[(3, 1)], 1)

    def test_calculate_node_participation(self):
        node_participation = calculate_node_participation(self.bicliques)
        # DMRs: node 2 appears in 2 bicliques, nodes 0,1 appear in 2 bicliques
        self.assertEqual(node_participation["dmrs"][2], 3)  # 3 DMRs appear in 2 bicliques
        # Genes: node 3 appears in 2 bicliques, node 4 appears in 2 bicliques
        self.assertEqual(node_participation["genes"][2], 2)  # 2 genes appear in 2 bicliques

    def test_calculate_edge_coverage(self):
        edge_coverage = calculate_edge_coverage(self.bicliques, self.graph)
        self.assertEqual(edge_coverage["single"], 3)      # 3 edges covered once
        self.assertEqual(edge_coverage["multiple"], 0)    # No edges covered multiple times
        self.assertEqual(edge_coverage["uncovered"], 3)   # 3 edges not covered
        self.assertEqual(edge_coverage["total"], 6)       # Total of 6 edges in graph

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
