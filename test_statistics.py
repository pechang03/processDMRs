# test_statistics.py
import unittest
import networkx as nx
from statistics import calculate_edge_coverage, calculate_coverage_statistics, calculate_biclique_statistics
from processDMR import create_bipartite_graph
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

    def test_graph_structure(self):
        """Test the basic structure of the graph"""
        # Test number of nodes
        expected_nodes = 11  # 6 DMRs + 5 genes
        self.assertEqual(len(self.graph.nodes()), expected_nodes)

        # Test number of edges
        expected_edges = 9  # K_{3,3} should have 9 edges
        self.assertEqual(len(self.graph.edges()), expected_edges)

    def test_max_degree(self):
        """Test maximum degree in the graph"""
        degrees = dict(self.graph.degree())
        max_degree = max(degrees.values())
        self.assertEqual(max_degree, 3, "Maximum degree should be 3.")

    def test_min_degree(self):
        """Test minimum degree in the graph"""
        degrees = dict(self.graph.degree())
        min_degree = min(degrees.values())
        self.assertEqual(min_degree, 3, "Minimum degree should be 3 in K_{3,3} bicliques.")

    def test_complete_bipartite_graphs_timepoints(self):
        """Test creation of complete bipartite graphs for different timepoints"""
        # Create a small test graph for each timepoint
        data = {
            "DMR_No.": [1, 2],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [
                "GeneA;GeneB",
                "GeneA;GeneB"
            ]
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(
            process_enhancer_info
        )

        from utils.constants import START_GENE_ID
        mapping = {
            "GeneA": START_GENE_ID,
            "GeneB": START_GENE_ID + 1
        }
        
        # Test different timepoints
        timepoints = ["P21-P28", "P21-P40", "P21-P60"]
        graphs = {}
        
        for timepoint in timepoints:
            graphs[timepoint] = create_bipartite_graph(df, mapping, timepoint)
            
            # Basic validation for each graph
            graph = graphs[timepoint]
            self.assertTrue(nx.is_bipartite(graph))
            self.assertEqual(len(graph.edges()), 4)  # K_{2,2} should have 4 edges
            
            # Verify DMR IDs are in correct range for timepoint
            dmr_nodes = {n for n, d in graph.nodes(data=True) if d["bipartite"] == 0}
            for dmr in dmr_nodes:
                self.assertEqual(graph.nodes[dmr]["timepoint"], timepoint)
                
                # Verify DMR ID is in correct range
                if timepoint == "P21-P28":
                    self.assertGreaterEqual(dmr, 1000000)
                    self.assertLess(dmr, 2000000)
                elif timepoint == "P21-P40":
                    self.assertGreaterEqual(dmr, 2000000)
                    self.assertLess(dmr, 3000000)
                elif timepoint == "P21-P60":
                    self.assertGreaterEqual(dmr, 3000000)
                    self.assertLess(dmr, 4000000)

    def test_calculate_biclique_statistics(self):
        """Test calculation of biclique statistics"""
        stats = calculate_biclique_statistics(self.graph, self.bicliques)
        self.assertEqual(stats['bicliques'], len(self.bicliques))
        self.assertEqual(stats['edges_covered'], 9)  # Adjusted expected value

    def test_calculate_coverage_statistics(self):
        """Test calculation of coverage statistics"""
        coverage_stats = calculate_coverage_statistics(self.graph, self.bicliques)
        self.assertEqual(coverage_stats["dmrs"]["covered"], 6)  # Adjusted expected value

if __name__ == "__main__":
    unittest.main()
