import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import networkx as nx
from processDMR import create_bipartite_graph
from biclique_analysis.processor import process_enhancer_info
from biclique_analysis.statistics import validate_graph
# from rb_domination import greedy_rb_domination


class TestGraphStatistics(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame setup for testing
        data = {
            "DMR_No.": [1, 2, 3],
            "Gene_Symbol_Nearby": ["genea", "geneb", "genec"],  # Make lowercase
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [
                "genea;geneb;genec",  # Each DMR connects to all genes
                "genea;geneb;genec",
                "genea;geneb;genec"
            ],
            "Gene_Description": ["Desc1", "Desc2", "Desc3"],
        }
        self.df = pd.DataFrame(data)
        self.df["Processed_Enhancer_Info"] = self.df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        # Create gene_id_mapping starting at START_GENE_ID (10000)
        all_genes = set()
        all_genes.update(self.df["Gene_Symbol_Nearby"].str.strip().str.lower())
        for genes in self.df["Processed_Enhancer_Info"]:
            if genes:
                all_genes.update(g.strip().lower() for g in genes)

        from utils.constants import START_GENE_ID
        self.gene_id_mapping = {
            gene: START_GENE_ID + idx for idx, gene in enumerate(sorted(all_genes))
        }

        # Create the bipartite graph
        self.bipartite_graph = create_bipartite_graph(self.df, self.gene_id_mapping)

        # Print debug info
        print("\nDebug information:")
        print(f"Number of nodes: {len(self.bipartite_graph.nodes())}")
        print(f"Number of edges: {len(self.bipartite_graph.edges())}")
        print(f"Gene mapping: {self.gene_id_mapping}")
        print(f"Edges: {list(self.bipartite_graph.edges())}")
        print(f"First gene ID: {min(self.gene_id_mapping.values())}")

    def test_min_degree(self):
        """Test minimum degree in the graph"""
        degrees = dict(self.bipartite_graph.degree())
        min_degree = min(degrees.values())
        self.assertEqual(min_degree, 3, "Minimum degree should be 3 in K_{3,3} bicliques.")

    def test_max_degree(self):
        degrees = dict(self.bipartite_graph.degree())
        max_degree = max(degrees.values())
        self.assertEqual(max_degree, 2, "Maximum degree should be 2.")

    def test_connected_components(self):
        """Test connected components in graph"""
        # Create a single connected component
        from utils.constants import START_GENE_ID
        data = {
            "DMR_No.": [1, 2, 3],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [
                "GeneD;GeneE",
                "GeneE;GeneF",
                "GeneF;GeneD"
            ]
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
    
        mapping = {
            name: START_GENE_ID + i 
            for i, name in enumerate(['GeneA', 'GeneB', 'GeneC', 'GeneD', 'GeneE', 'GeneF'])
        }
    
        graph = create_bipartite_graph(df, mapping)
        num_components = nx.number_connected_components(graph)
        self.assertEqual(num_components, 1, "There should be 1 connected component.")

    def test_graph_structure(self):
        """Test the basic structure of the graph"""
        # Test number of nodes
        expected_nodes = 9  # 3 DMRs + 6 genes (A,B,C,D,E,F)
        self.assertEqual(len(self.bipartite_graph.nodes()), expected_nodes)

        # Test number of edges
        expected_edges = 6  # Each DMR connects to its nearby gene and enhancer genes
        self.assertEqual(len(self.bipartite_graph.edges()), expected_edges)

    def test_graph_validation(self):
        """Test graph validation function"""
        try:
            dmr_nodes, gene_nodes = validate_graph(self.bipartite_graph)
            self.assertTrue(len(dmr_nodes) > 0, "Should have DMR nodes")
            self.assertTrue(len(gene_nodes) > 0, "Should have gene nodes")
        except Exception as e:
            self.fail(f"Graph validation failed: {str(e)}")


from visualization.core import create_biclique_visualization
