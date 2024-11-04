import unittest
import pandas as pd
import networkx as nx
from processDMR import create_bipartite_graph, process_enhancer_info, greedy_rb_domination

class TestBipartiteGraph(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame setup for testing the bipartite graph creation
        data = {
            "DMR_No.": [1, 2, 3],  # Original DMR_No.
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
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [".", ".", ".", ".", ".", "."],
            "Confidence_Scores": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]  # Add this line
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
            "DMR_No.": [0, 1],  # Use numeric values for DMR_No.
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
        self.assertIn(2, graph.nodes(), "2 should be a node in the graph.")
        self.assertIn(0, graph.nodes(), "0 should be a node in the graph.")
        self.assertIn(1, graph.nodes(), "1 should be a node in the graph.")
        self.assertIn("GeneD", graph.nodes(), "GeneD should be a node in the graph.")
        self.assertIn("GeneE", graph.nodes(), "GeneE should be a node in the graph.")

    def test_dominating_set(self):
        # Sample data to simulate the DSS1 dataset
        df_dss1 = pd.DataFrame({
            "DMR_No.": [1, 2, 3],  # Ensure these are the correct starting values
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "Area_Stat": [10.5, 20.3, 15.2],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": ["GeneD;GeneE", "GeneF", None]
        })
        df_dss1["Processed_Enhancer_Info"] = df_dss1["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
        bipartite_graph_dss1 = create_bipartite_graph(df_dss1)

        # Test for DSS1 using Area_Stat
        area_col_dss1 = "Area_Stat"
        dominating_set_dss1 = greedy_rb_domination(bipartite_graph_dss1, df_dss1, area_col=area_col_dss1)
        expected_dominating_set_dss1 = {0, 1, 2}  # Adjust to match the correct node IDs

        # Ensure node 0 is covered by the dominating set
        self.assertIn(0, dominating_set_dss1, "Node 0 should be in the dominating set for DSS1.")

        # Test for HOME1 using Confidence_Scores
        area_col_home1 = "Confidence_Scores"
        dominating_set_home1 = greedy_rb_domination(self.bipartite_graph, self.df_home1, area_col=area_col_home1)
        for node in self.bipartite_graph.nodes():
            neighbors = set(self.bipartite_graph.neighbors(node))
            self.assertTrue(any(neighbor in dominating_set_home1 for neighbor in neighbors) or node in dominating_set_home1,
                            f"Node {node} is not adjacent to any node in the dominating set for HOME1.")

        # Ensure node 0 is covered by the dominating set for HOME1
        self.assertIn(0, dominating_set_home1, "Node 0 should be in the dominating set for HOME1.")

        # Test using only the degree of the vertex
        dominating_set_degree = greedy_rb_domination(self.bipartite_graph, self.df_home1, area_col=area_col_home1)
        for node, data in self.bipartite_graph.nodes(data=True):
            if data['bipartite'] == 1:  # Only check gene nodes
                neighbors = set(self.bipartite_graph.neighbors(node))
                self.assertTrue(any(neighbor in dominating_set_degree for neighbor in neighbors),
                                f"Gene node {node} is not adjacent to any node in the dominating set using degree only.")

        # Ensure node 0 is covered by the dominating set using degree only
    def test_complete_bipartite_graphs(self):
        # Create a DataFrame for K_{2,3}
        data_k23 = {
            "DMR_No.": [1, 1, 1, 2, 2, 2],  # Each DMR connected to all three genes
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC", "GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None, None, None, None, None, None]
        }
        df_k23 = pd.DataFrame(data_k23)
        df_k23["Processed_Enhancer_Info"] = df_k23["Gene_Symbol_Nearby"].apply(lambda x: list(set(x.split(";"))) if x else [])

        # Test K_{3,7}
        genes_k37 = [f"Gene{i}" for i in range(7)]  # Create 7 unique gene names
        data_k37 = {
            "DMR_No.": [1, 2, 3] * 7,  # Each DMR connected to all seven genes
            "Gene_Symbol_Nearby": genes_k37 * 3,  # Each gene connected to all three DMRs
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None] * 21
        }
        df_k37 = pd.DataFrame(data_k37)
        df_k37["Processed_Enhancer_Info"] = df_k37["Gene_Symbol_Nearby"].apply(lambda x: list(set(x.split(";"))) if x else [])

        # Create a bipartite graph for K_{3,7}
        graph_k37 = create_bipartite_graph(df_k37)

        # Test K_{3,7} structure
        self.assertEqual(len(graph_k37.nodes()), 10, "K_{3,7} should have 10 nodes (3 DMRs + 7 genes).")
        self.assertEqual(len(graph_k37.edges()), 21, "K_{3,7} should have 21 edges (3 * 7 connections).")

        # Verify all connections in K_{3,7}
        for dmr in range(3):  # DMR nodes are 0, 1, 2
            for gene in genes_k37:
                self.assertTrue(graph_k37.has_edge(dmr, gene), f"DMR {dmr} should be connected to {gene}.")

        # Create a bipartite graph for K_{2,3}
        data_k23 = {
            "DMR_No.": [1, 1, 1, 2, 2, 2],  # Each DMR connected to all three genes
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC", "GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None, None, None, None, None, None]
        }
        df_k23 = pd.DataFrame(data_k23)
        df_k23["Processed_Enhancer_Info"] = df_k23["Gene_Symbol_Nearby"].apply(lambda x: list(set(x.split(";"))) if x else [])
        graph_k23 = create_bipartite_graph(df_k23)

        # Test dominating sets for both graphs
        dom_set_k23 = greedy_rb_domination(graph_k23, df_k23)
        dom_set_k37 = greedy_rb_domination(graph_k37, df_k37)

        # Verify that dominating set size is at most the number of connected components
        components = nx.number_connected_components(graph_k23)
        self.assertLessEqual(len(dom_set_k23), components, 
            "Dominating set size should not exceed number of connected components")

        components = nx.number_connected_components(graph_k37)
        self.assertLessEqual(len(dom_set_k37), components,
            "Dominating set size should not exceed number of connected components")

if __name__ == '__main__':
    unittest.main()
