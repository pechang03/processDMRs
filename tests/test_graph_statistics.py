import unittest
import pandas as pd
import networkx as nx
from processDMR import create_bipartite_graph, process_enhancer_info

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
import networkx as nx
import pandas as pd

import networkx as nx

import networkx as nx
import pandas as pd

def validate_bipartite_graph(B):
    """Validate the bipartite graph properties"""
    # Check for isolated nodes
    isolated = list(nx.isolates(B))
    if isolated:
        print(f"Warning: Found {len(isolated)} isolated nodes: {isolated[:5]}")
        
    # Check node degrees
    degrees = dict(B.degree())
    if min(degrees.values()) == 0:
        zero_degree_nodes = [n for n, d in degrees.items() if d == 0]
        print(f"Warning: Graph contains {len(zero_degree_nodes)} nodes with degree 0")
        print(f"First 5 zero-degree nodes: {zero_degree_nodes[:5]}")

    # Verify bipartite property
    if not nx.is_bipartite(B):
        print("Warning: Graph is not bipartite")
