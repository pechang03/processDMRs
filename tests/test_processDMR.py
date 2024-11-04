import unittest
import pandas as pd
import networkx as nx
from processDMR import create_bipartite_graph, process_enhancer_info

class TestBipartiteGraph(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame setup for testing the bipartite graph creation
        data = {
            "DMR_No.": [1, 2, 3],  # Use numeric values for DMR_No.
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": ["GeneD;GeneE", "GeneF", None]
        }
        df = pd.DataFrame(data)

        # Process the enhancer information to create the 'Processed_Enhancer_Info' column
        df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)

        self.bipartite_graph = create_bipartite_graph(df)

        # Sample data to simulate the HOME1 dataset
        self.df_home1 = pd.DataFrame({
            "DMR_No.": [1, 2, 3, 4, 5, 6],
            "Gene_Symbol": ["Sulf1", "Rgs20", "Pabpc1l2a", "Vmn2r121", "Mid1", "Amer1"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [".", ".", ".", ".", ".", "."]
        })

        # Process the enhancer information for HOME1
        self.df_home1["Processed_Enhancer_Info"] = self.df_home1["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
        # Check if the node is a DMR and assert it has adjacent edges
        for dmr in self.bipartite_graph.nodes():
            if self.bipartite_graph.nodes[dmr].get('bipartite') == 0:  # Check if it's a DMR
                self.assertGreater(len(list(self.bipartite_graph.adj[dmr])), 0, f"{dmr} has no adjacent edges.")

    def test_empty_dataframe(self):
        # Assert that the graph has no nodes when provided with an empty DataFrame
        empty_df = pd.DataFrame(columns=["DMR_No.", "Gene_Symbol_Nearby", "ENCODE_Enhancer_Interaction(BingRen_Lab)"])
        empty_graph = create_bipartite_graph(empty_df)
        self.assertEqual(len(empty_graph.nodes()), 0, "Graph should have no nodes for an empty DataFrame.")

    def test_dmr_without_genes(self):
        # Assert that the graph has 2 DMR nodes without any associated genes or edges
        data = {
            "DMR_No.": [1, 2],  # Use numeric values for DMR_No.
            "Gene_Symbol_Nearby": [None, None],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None, None]
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
        graph = create_bipartite_graph(df)
        self.assertEqual(len(graph.nodes()), 2, "Graph should have 2 DMR nodes without any edges.")

    def test_multiple_dmrs(self):
        # Assert that the graph has the correct number of nodes based on DMRs and unique genes
        data = {
            "DMR_No.": [1, 2, 3],  # Use numeric values for DMR_No.
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": ["GeneD;GeneE", "GeneF;GeneG", "GeneH"]
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
        graph = create_bipartite_graph(df)
        self.assertEqual(len(graph.nodes()), 11, "Graph should have 11 nodes (3 DMRs + 8 unique genes).")
        self.assertIn(1, graph.nodes(), "1 should be a node in the graph.")
        self.assertIn("GeneD", graph.nodes(), "GeneD should be a node in the graph.")
        self.assertIn("GeneE", graph.nodes(), "GeneE should be a node in the graph.")

    def test_dominating_set(self):
        # Calculate the dominating set for the test bipartite graph
        dominating_set = nx.algorithms.dominating.min_weighted_dominating_set(self.bipartite_graph)

        # Check that every node is adjacent to at least one node in the dominating set
        for node in self.bipartite_graph.nodes():
            # Get neighbors of the node
            neighbors = set(self.bipartite_graph.neighbors(node))
            # Check if any neighbor is in the dominating set
            self.assertTrue(any(neighbor in dominating_set for neighbor in neighbors),
                            f"Node {node} is not adjacent to any node in the dominating set.")
if __name__ == '__main__':
    unittest.main()
