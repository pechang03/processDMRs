import unittest
import pandas as pd
import networkx as nx
from processDMR import create_bipartite_graph  # Adjust the import based on your project structure

class TestBipartiteGraph(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame setup for testing
        data = {
            "DMR_No.": ["DMR1", "DMR2", "DMR3"],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": ["GeneD;GeneE", "GeneF", None]
        }
        df = pd.DataFrame(data)
        self.bipartite_graph = create_bipartite_graph(df)

    def test_dmr_has_edges(self):
        for dmr in self.bipartite_graph.nodes():
            if self.bipartite_graph.nodes[dmr].get('bipartite') == 0:  # Check if it's a DMR
                self.assertGreater(len(list(self.bipartite_graph.adjacency()[dmr])), 0, f"{dmr} has no adjacent edges.")

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["DMR_No.", "Gene_Symbol_Nearby", "ENCODE_Enhancer_Interaction(BingRen_Lab)"])
        empty_graph = create_bipartite_graph(empty_df)
        self.assertEqual(len(empty_graph.nodes()), 0, "Graph should have no nodes for an empty DataFrame.")

    def test_dmr_without_genes(self):
        data = {
            "DMR_No.": ["DMR1", "DMR2"],
            "Gene_Symbol_Nearby": [None, None],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None, None]
        }
        df = pd.DataFrame(data)
        graph = create_bipartite_graph(df)
        self.assertEqual(len(graph.nodes()), 2, "Graph should have 2 DMR nodes without any edges.")

    def test_multiple_dmrs(self):
        data = {
            "DMR_No.": ["DMR1", "DMR2", "DMR3"],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": ["GeneD;GeneE", "GeneF;GeneG", "GeneH"]
        }
        df = pd.DataFrame(data)
        graph = create_bipartite_graph(df)
        self.assertEqual(len(graph.nodes()), 8, "Graph should have 8 nodes (3 DMRs + 5 unique genes).")
        self.assertIn("DMR1", graph.nodes(), "DMR1 should be a node in the graph.")
        self.assertIn("GeneD", graph.nodes(), "GeneD should be a node in the graph.")
        self.assertIn("GeneE", graph.nodes(), "GeneE should be a node in the graph.")

if __name__ == '__main__':
    unittest.main()
