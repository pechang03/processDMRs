import unittest
import pandas as pd
import networkx as nx
from processDMR import create_bipartite_graph, process_enhancer_info  # Adjust the import based on your project structure

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

if __name__ == '__main__':
    unittest.main()
import unittest
import pandas as pd
import networkx as nx
from processDMR import create_bipartite_graph, process_enhancer_info, gene_id_mapping

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

    def test_no_unknown_gene_ids(self):
        # Create the bipartite graph
        bipartite_graph_home1 = create_bipartite_graph(self.df_home1, closest_gene_col="Gene_Symbol")

        # Check that all gene IDs in the graph are valid numbers
        for edge in bipartite_graph_home1.edges():
            dmr, gene = edge
            self.assertIn(gene, gene_id_mapping, f"Gene {gene} is not in gene_id_mapping")

if __name__ == '__main__':
    unittest.main()
