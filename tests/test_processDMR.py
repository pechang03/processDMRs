import unittest
import random
import pandas as pd
import networkx as nx
from processDMR import create_bipartite_graph, process_enhancer_info
from rb_domination import greedy_rb_domination

class TestBipartiteGraph(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame setup for testing
        data = {
            "DMR_No.": [1, 2, 3],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": ["GeneD;GeneE", "GeneF", None],
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)
        
        # Create gene_id_mapping
        all_genes = set()
        all_genes.update(df["Gene_Symbol_Nearby"].dropna())
        all_genes.update([g for genes in df["Processed_Enhancer_Info"] for g in genes])
        self.gene_id_mapping = {gene: idx + len(df) for idx, gene in enumerate(sorted(all_genes))}
        
        self.df = df  # Store df for use in tests
        self.bipartite_graph = create_bipartite_graph(df, self.gene_id_mapping)

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(
            columns=[
                "DMR_No.",
                "Gene_Symbol_Nearby",
                "ENCODE_Enhancer_Interaction(BingRen_Lab)",
            ]
        )
        empty_graph = create_bipartite_graph(empty_df, {})
        self.assertEqual(len(empty_graph.nodes()), 0)

    def test_single_node_graph(self):
        single_node_df = pd.DataFrame(
            {
                "DMR_No.": [1],
                "Gene_Symbol_Nearby": ["GeneA"],
                "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None],
            }
        )
        single_node_df["Processed_Enhancer_Info"] = single_node_df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)
        
        single_mapping = {"GeneA": 1}
        single_node_graph = create_bipartite_graph(single_node_df, single_mapping)
        self.assertEqual(len(single_node_graph.nodes()), 2)

    def test_dmr_without_genes(self):
        data = {
            "DMR_No.": [1, 2],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None, None],
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)
        
        mapping = {"GeneA": 2, "GeneB": 3}
        graph = create_bipartite_graph(df, mapping)
        self.assertEqual(len(graph.nodes()), 4)
        self.assertEqual(len(graph.edges()), 2)

    def test_multiple_dmrs(self):
        data = {
            "DMR_No.": [1, 2, 3],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [
                "GeneD;GeneE",
                "GeneF;GeneG",
                "GeneH",
            ],
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)
        
        all_genes = set()
        all_genes.update(df["Gene_Symbol_Nearby"].dropna())
        all_genes.update([g for genes in df["Processed_Enhancer_Info"] for g in genes])
        mapping = {gene: idx + len(df) for idx, gene in enumerate(sorted(all_genes))}
        
        graph = create_bipartite_graph(df, mapping)
        self.assertEqual(len(graph.nodes()), 11)

    def test_random_bipartite_graphs(self):
        for _ in range(10):
            num_dmrs = random.randint(1, 10)
            num_genes = random.randint(1, 10)
            data = {
                "DMR_No.": list(range(1, num_dmrs + 1)),
                "Gene_Symbol_Nearby": [f"Gene{j}" for j in range(num_genes)],
                "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None] * num_dmrs,
            }
            df = pd.DataFrame(data)
            df["Processed_Enhancer_Info"] = df[
                "ENCODE_Enhancer_Interaction(BingRen_Lab)"
            ].apply(process_enhancer_info)
            
            mapping = {f"Gene{j}": j + num_dmrs for j in range(num_genes)}
            graph = create_bipartite_graph(df, mapping)
            
            self.assertEqual(len(graph.nodes()), num_dmrs + num_genes)

    def test_sparse_and_dense_graphs(self):
        # Test sparse graph
        sparse_data = {
            "DMR_No.": [1, 2, 3],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None, None, None],
        }
        sparse_df = pd.DataFrame(sparse_data)
        sparse_df["Processed_Enhancer_Info"] = sparse_df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)
        
        sparse_mapping = {"GeneA": 3, "GeneB": 4, "GeneC": 5}
        sparse_graph = create_bipartite_graph(sparse_df, sparse_mapping)
        self.assertEqual(len(sparse_graph.nodes()), 6)
        self.assertEqual(len(sparse_graph.edges()), 3)

        # Test dense graph
        dense_data = {
            "DMR_No.": [1, 2, 3],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [
                "GeneA;GeneB;GeneC",
                "GeneA;GeneB;GeneC",
                "GeneA;GeneB;GeneC",
            ],
        }
        dense_df = pd.DataFrame(dense_data)
        dense_df["Processed_Enhancer_Info"] = dense_df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)
        
        dense_mapping = {"GeneA": 3, "GeneB": 4, "GeneC": 5}
        dense_graph = create_bipartite_graph(dense_df, dense_mapping)
        self.assertEqual(len(dense_graph.nodes()), 6)
        self.assertEqual(len(dense_graph.edges()), 9)

    def test_degree_one_genes(self):
        data = {
            "DMR_No.": [1, 2],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None, None],
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)
        
        mapping = {"GeneA": 2, "GeneB": 3}
        graph = create_bipartite_graph(df, mapping)
        
        # Add Area_Stat column for rb_domination
        df["Area_Stat"] = [1.0, 1.0]
        
        dominating_set = greedy_rb_domination(graph, df)
        
        for node in graph.nodes():
            if graph.nodes[node]["bipartite"] == 1 and graph.degree(node) == 1:
                neighbor = list(graph.neighbors(node))[0]
                self.assertIn(neighbor, dominating_set)

    def test_complete_bipartite_graphs(self):
        # Test K_{2,3}
        data_k23 = {
            "DMR_No.": [1, 2],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None, None],
        }
        df_k23 = pd.DataFrame(data_k23)
        df_k23["Processed_Enhancer_Info"] = df_k23[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)
        
        mapping_k23 = {"GeneA": 2, "GeneB": 3, "GeneC": 4}
        graph_k23 = create_bipartite_graph(df_k23, mapping_k23)
        
        self.assertEqual(len(graph_k23.nodes()), 5)
        self.assertEqual(len(graph_k23.edges()), 6)

if __name__ == "__main__":
    unittest.main()
