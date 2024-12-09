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
        """Set up test graph with proper K_{2,2} structure and correct ID ranges"""
        from utils.constants import START_GENE_ID

        # Sample DataFrame setup for testing - creating two overlapping K_{3,3} bicliques
        data = {
            "DMR_No.": [1, 2, 3, 4, 5, 6],  # DMR IDs will be 0-5
            "Gene_Symbol_Nearby": [
                "genea",  # First biclique genes
                "genea",
                "genea",
                "gened",  # Second biclique genes
                "gened",
                "gened",
            ],
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": [
                "geneb;genec",  # Complete first K_{3,3}
                "geneb;genec",
                "geneb;genec",
                "genee;genef",  # Complete second K_{3,3}
                "genee;genef",
                "genee;genef",
            ],
            "Gene_Description": ["Desc1", "Desc2", "Desc3", "Desc4", "Desc5", "Desc6"],
        }
        self.df = pd.DataFrame(data)
        self.df["Processed_Enhancer_Info"] = self.df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        # Create gene_id_mapping with explicit IDs starting at START_GENE_ID (100000)
        self.gene_id_mapping = {
            "genea": START_GENE_ID,  # 100000
            "geneb": START_GENE_ID + 1,  # 100001
            "genec": START_GENE_ID + 2,  # 100002 - shared between bicliques
            "gened": START_GENE_ID + 3,  # 100003
            "genee": START_GENE_ID + 4,  # 100004
            "genef": START_GENE_ID + 5,  # 100005
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
        self.assertEqual(
            min_degree, 3, "Minimum degree should be 3 in K_{3,3} bicliques."
        )

    def test_max_degree(self):
        degrees = dict(self.bipartite_graph.degree())
        max_degree = max(degrees.values())
        self.assertEqual(max_degree, 3, "Maximum degree should be 3.")

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
                "GeneF;GeneD",
            ],
        }
        df = pd.DataFrame(data)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        mapping = {
            name: START_GENE_ID + i
            for i, name in enumerate(
                ["GeneA", "GeneB", "GeneC", "GeneD", "GeneE", "GeneF"]
            )
        }

        graph = create_bipartite_graph(df, mapping)
        num_components = nx.number_connected_components(graph)
        self.assertEqual(num_components, 1, "There should be 1 connected component.")

    def test_graph_structure(self):
        """Test the basic structure of the graph"""
        # Test number of nodes
        expected_nodes = 12  # 6 DMRs + 6 genes (genea through genef)
        self.assertEqual(len(self.bipartite_graph.nodes()), expected_nodes)

        # Test number of edges
        expected_edges = 18  # Each DMR connects to 3 genes
        self.assertEqual(len(self.bipartite_graph.edges()), expected_edges)

    def test_graph_validation(self):
        """Test graph validation function"""
        try:
            dmr_nodes, gene_nodes = validate_graph(self.bipartite_graph)
            self.assertTrue(len(dmr_nodes) > 0, "Should have DMR nodes")
            self.assertTrue(len(gene_nodes) > 0, "Should have gene nodes")
        except Exception as e:
            self.fail(f"Graph validation failed: {str(e)}")

    def test_biclique_classification(self):
        """Test biclique classification functions"""
        from biclique_analysis.classifier import (
            BicliqueSizeCategory,
            classify_biclique,
            classify_component,
            is_complex,
            get_size_thresholds,
        )

        # Test BicliqueSizeCategory methods
        self.assertEqual(BicliqueSizeCategory.EMPTY.get_complexity_score(), 0)
        self.assertEqual(
            BicliqueSizeCategory.from_string("COMPLEX"), BicliqueSizeCategory.COMPLEX
        )

        # Test size thresholds
        thresholds = get_size_thresholds()
        self.assertEqual(thresholds.to_tuple(), (3, 1, 1))

        # Get DMR and gene nodes from first biclique
        dmr_nodes = {0, 1, 2}  # First three DMRs
        gene_nodes = {
            self.gene_id_mapping[gene] for gene in ["genea", "geneb", "genec"]
        }

        # Test classify_biclique
        category = classify_biclique(dmr_nodes, gene_nodes)
        self.assertEqual(category, BicliqueSizeCategory.INTERESTING)

        # Test classify_component with single biclique
        bicliques = [(dmr_nodes, gene_nodes)]
        component_category = classify_component(dmr_nodes, gene_nodes, bicliques)
        self.assertEqual(component_category, BicliqueSizeCategory.INTERESTING)

        # Test is_complex with multiple bicliques
        second_dmr_nodes = {3, 4, 5}  # Second three DMRs
        second_gene_nodes = {
            self.gene_id_mapping[gene] for gene in ["gened", "genee", "genef"]
        }
        bicliques = [(dmr_nodes, gene_nodes), (second_dmr_nodes, second_gene_nodes)]
        self.assertTrue(is_complex(bicliques))

    def test_component_analyzer(self):
        """Test ComponentAnalyzer functionality"""
        from biclique_analysis.component_analyzer import ComponentAnalyzer

        # Create analyzer instance
        analyzer = ComponentAnalyzer(
            self.bipartite_graph,
            {
                "bicliques": [
                    (
                        set(range(3)),
                        {self.gene_id_mapping[g] for g in ["genea", "geneb", "genec"]},
                    )
                ]
            },
            self.bipartite_graph.copy(),
        )

        # Test graph creation
        created_graph = analyzer._create_biclique_graph()
        self.assertIsInstance(created_graph, nx.Graph)

        # Test component analysis
        component_stats = analyzer.analyze_components()
        self.assertIn("components", component_stats)

        # Test graph component analysis
        graph_stats = analyzer._analyze_graph_components(self.bipartite_graph)
        self.assertIn("connected", graph_stats)

        # Test dominating set analysis
        dominating_set = {0, 1}  # Example dominating set
        dom_stats = analyzer._analyze_dominating_set(dominating_set)
        self.assertIn("size", dom_stats)

        # Test component counting
        count = analyzer._count_components_with_dominating_nodes(dominating_set)
        self.assertIsInstance(count, int)

        # Test average size calculation
        avg_size = analyzer._calculate_avg_size_per_component(dominating_set)
        self.assertIsInstance(avg_size, float)

        # Test edge classification retrieval
        edge_classes = analyzer.get_edge_classifications()
        self.assertIsInstance(edge_classes, dict)

        # Test redundant node finding
        redundant = analyzer.find_redundant_dominating_nodes(dominating_set)
        self.assertIsInstance(redundant, list)

        # Test dominating set validation
        try:
            analyzer.validate_dominating_set(dominating_set)
        except ValueError:
            pass  # Expected for this test case

        # Test dominating set optimization
        optimized = analyzer.optimize_dominating_set(dominating_set)
        self.assertIsInstance(optimized, set)

        # Test dominating set statistics
        stats = analyzer.get_dominating_set_stats(dominating_set)
        self.assertIn("size", stats)
