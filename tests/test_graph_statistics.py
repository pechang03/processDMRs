import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import networkx as nx
from processDMR import create_bipartite_graph
from graph_utils import process_enhancer_info
# from rb_domination import greedy_rb_domination


class TestGraphStatistics(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame setup for testing
        data = {
            "DMR_No.": [1, 2, 3],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": ["GeneD;GeneE", "GeneF", None],
            "Gene_Description": ["Desc1", "Desc2", "Desc3"]
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)
        # Create gene_id_mapping for testing
        all_genes = set()
        all_genes.update(df["Gene_Symbol_Nearby"].dropna())
        all_genes.update([g for genes in df["Processed_Enhancer_Info"] for g in genes if g])
        self.gene_id_mapping = {gene: idx + len(df) for idx, gene in enumerate(sorted(all_genes))}
        
        self.bipartite_graph = create_bipartite_graph(df, self.gene_id_mapping)

    def test_min_degree(self):
        degrees = dict(self.bipartite_graph.degree())
        min_degree = min(degrees.values())
        self.assertEqual(min_degree, 1, "Minimum degree should be 1.")

    def test_max_degree(self):
        degrees = dict(self.bipartite_graph.degree())
        max_degree = max(degrees.values())
        self.assertEqual(max_degree, 3, "Maximum degree should be 3.")

    def test_connected_components(self):
        num_connected_components = nx.number_connected_components(self.bipartite_graph)
        self.assertEqual(
            num_connected_components, 3, "There should be 3 connected components."
        )


    def test_graph_structure(self):
        """Test the basic structure of the graph"""
        # Test number of nodes
        expected_nodes = 9  # 3 DMRs + 6 genes (A,B,C,D,E,F)
        self.assertEqual(len(self.bipartite_graph.nodes()), expected_nodes)
        
        # Test number of edges
        expected_edges = 6  # Each DMR connects to its nearby gene and enhancer genes
        self.assertEqual(len(self.bipartite_graph.edges()), expected_edges)
from visualization.core import create_biclique_visualization
