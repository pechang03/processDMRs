import unittest
import random
import pandas as pd
import networkx as nx
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now import the modules
from processDMR import create_bipartite_graph, process_enhancer_info
from rb_domination import greedy_rb_domination
from visualization.core import create_biclique_visualization
from utils.constants import START_GENE_ID


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
        self.gene_id_mapping = {
            gene: idx + len(df) for idx, gene in enumerate(sorted(all_genes))
        }

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
        """Test graph with DMRs that have no associated genes"""
        data = {
            "DMR_No.": [1, 2],
            "Gene_Symbol_Nearby": ["GeneA", "GeneB"],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [None, None],
        }
        test_df = pd.DataFrame(data)
        test_df["Processed_Enhancer_Info"] = test_df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        mapping = {
            "GeneA": START_GENE_ID,
            "GeneB": START_GENE_ID + 1,
        }  # Use START_GENE_ID
        graph = create_bipartite_graph(test_df, mapping)

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
                "Gene_Symbol_Nearby": [
                    f"Gene{j % num_genes}" for j in range(num_dmrs)
                ],  # Ensure each DMR has a corresponding gene
                "ENCODE_Enhancer_Interaction(BingRen_Lab)": [
                    ";".join([f"Gene{k}" for k in range(num_genes)])
                    for _ in range(num_dmrs)
                ],  # Connect each DMR to all genes
            }
            df = pd.DataFrame(data)
            df["Processed_Enhancer_Info"] = df[
                "ENCODE_Enhancer_Interaction(BingRen_Lab)"
            ].apply(process_enhancer_info)

            mapping = {f"Gene{j}": j + num_dmrs for j in range(num_genes)}
            graph = create_bipartite_graph(df, mapping)

            # Add debugging output
            if (
                len(graph.nodes()) != num_dmrs + num_genes
                or len(graph.edges()) != num_dmrs * num_genes
            ):
                print(
                    f"Debug: num_dmrs={num_dmrs}, num_genes={num_genes}, graph_nodes={len(graph.nodes())}, graph_edges={len(graph.edges())}"
                )
                print(f"Graph nodes: {graph.nodes()}")
                print(f"Gene ID Mapping: {mapping}")
                print(f"Associated Genes: {[f'Gene{j}' for j in range(num_genes)]}")

            self.assertEqual(len(graph.nodes()), num_dmrs + num_genes)
            self.assertEqual(len(graph.edges()), num_dmrs * num_genes)

    def test_sparse_and_dense_graphs(self):
        """Test handling of sparse and dense graphs"""
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

        sparse_mapping = {
            "GeneA": START_GENE_ID,
            "GeneB": START_GENE_ID + 1,
            "GeneC": START_GENE_ID + 2,
        }
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
        # Test K_{3,3}
        df_k23 = pd.DataFrame(
            {
                "DMR_No.": [1, 2, 3],
                "Gene_Symbol_Nearby": ["GeneA", "GeneB", "GeneC"],
                "ENCODE_Enhancer_Interaction(BingRen_Lab)": [
                    "GeneA;GeneB;GeneC",
                    "GeneA;GeneB;GeneC",
                    "GeneA;GeneB;GeneC",
                ],
            }
        )
        df_k23["Processed_Enhancer_Info"] = df_k23[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        mapping_k23 = {
            "GeneA": START_GENE_ID,
            "GeneB": START_GENE_ID + 1,
            "GeneC": START_GENE_ID + 2,
        }
        graph_k23 = create_bipartite_graph(df_k23, mapping_k23)

        self.assertEqual(
            len(graph_k23.edges()), 9
        )  # Update expected edges to 9 for K_{3,3}


if __name__ == "__main__":
    unittest.main()
