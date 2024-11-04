import unittest
import pandas as pd
import networkx as nx
from processDMR import create_bipartite_graph, process_enhancer_info, nx

class TestGraphStatistics(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame setup for testing
        data = {
            "DMR_No.": [1, 2, 3],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": ["GeneD;GeneE", "GeneF", None]
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
        self.bipartite_graph = create_bipartite_graph(df)

    def test_min_degree(self):
        degrees = dict(self.bipartite_graph.degree())
        min_degree = min(degrees.values())
        self.assertEqual(min_degree, 1, "Minimum degree should be 1.")

    def test_max_degree(self):
        degrees = dict(self.bipartite_graph.degree())
        max_degree = max(degrees.values())
        self.assertEqual(max_degree, 2, "Maximum degree should be 2.")

    def test_connected_components(self):
        num_connected_components = nx.number_connected_components(self.bipartite_graph)
        self.assertEqual(num_connected_components, 1, "There should be 1 connected component.")

    def test_min_degree(self):
        degrees = dict(self.bipartite_graph.degree())
        min_degree = min(degrees.values())
        self.assertEqual(min_degree, 1, "Minimum degree should be 1.")

    def test_max_degree(self):
        degrees = dict(self.bipartite_graph.degree())
        max_degree = max(degrees.values())
        self.assertEqual(max_degree, 2, "Maximum degree should be 2.")

    def test_connected_components(self):
        num_connected_components = nx.number_connected_components(self.bipartite_graph)
        self.assertEqual(num_connected_components, 1, "There should be 1 connected component.")

if __name__ == '__main__':
    unittest.main()
