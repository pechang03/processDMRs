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

if __name__ == '__main__':
    unittest.main()
