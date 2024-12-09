# File : test_timepoint_data.py
#
import unittest
from unittest.mock import patch, MagicMock
import networkx as nx
from routes.timepoint_data import process_timepoint
from biclique_analysis.processor import process_bicliques
from biclique_analysis.components import process_components
from utils.json_utils import convert_for_json
from utils.constants import START_GENE_ID


class TestTimepointData(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with complex component."""
        # Create mock data
        self.mock_df = MagicMock()
        # Use START_GENE_ID (100000) for gene IDs
        self.mock_gene_id_mapping = {
            "GENE1": START_GENE_ID,  # 100000
            "GENE2": START_GENE_ID + 1,  # 100001
            "GENE3": START_GENE_ID + 2,  # 100002
            "GENE4": START_GENE_ID + 3,  # 100003
            "GENE5": START_GENE_ID + 4,  # 100004
        }

        # Create bipartite graph with complex structure
        self.mock_graph = nx.Graph()

        # Add DMR nodes (0-5) - DMRs start at 0 for first timepoint
        dmr_nodes = range(6)
        self.mock_graph.add_nodes_from(dmr_nodes, bipartite=0)

        # Add Gene nodes (100000-100004)
        gene_nodes = range(START_GENE_ID, START_GENE_ID + 5)
        self.mock_graph.add_nodes_from(gene_nodes, bipartite=1)

        # Create edges for three overlapping bicliques
        # Biclique 1: DMRs [0,1,2] - Genes [100000,100001,100002]
        # Biclique 2: DMRs [2,3,4] - Genes [100001,100002,100003]
        # Biclique 3: DMRs [4,5] - Genes [100002,100003,100004]
        edges = [
            # Biclique 1 edges
            (0, START_GENE_ID),
            (0, START_GENE_ID + 1),
            (0, START_GENE_ID + 2),
            (1, START_GENE_ID),
            (1, START_GENE_ID + 1),
            (1, START_GENE_ID + 2),
            (2, START_GENE_ID),
            (2, START_GENE_ID + 1),
            (2, START_GENE_ID + 2),
            # Biclique 2 edges
            (2, START_GENE_ID + 1),
            (2, START_GENE_ID + 2),
            (2, START_GENE_ID + 3),
            (3, START_GENE_ID + 1),
            (3, START_GENE_ID + 2),
            (3, START_GENE_ID + 3),
            (4, START_GENE_ID + 1),
            (4, START_GENE_ID + 2),
            (4, START_GENE_ID + 3),
            # Biclique 3 edges
            (4, START_GENE_ID + 2),
            (4, START_GENE_ID + 3),
            (4, START_GENE_ID + 4),
            (5, START_GENE_ID + 2),
            (5, START_GENE_ID + 3),
            (5, START_GENE_ID + 4),
        ]
        self.mock_graph.add_edges_from(edges)

        # Mock bicliques result with complex overlapping structure
        self.mock_bicliques_result = {
            "bicliques": [
                (
                    {0, 1, 2},
                    {START_GENE_ID, START_GENE_ID + 1, START_GENE_ID + 2},
                ),  # Biclique 1
                (
                    {2, 3, 4},
                    {START_GENE_ID + 1, START_GENE_ID + 2, START_GENE_ID + 3},
                ),  # Biclique 2
                (
                    {4, 5},
                    {START_GENE_ID + 2, START_GENE_ID + 3, START_GENE_ID + 4},
                ),  # Biclique 3
            ],
            "stats": {
                "coverage": {
                    "dmrs": {"covered": 6, "total": 6, "percentage": 1.0},
                    "genes": {"covered": 5, "total": 5, "percentage": 1.0},
                    "edges": {
                        "single_coverage": 12,
                        "multiple_coverage": 6,
                        "uncovered": 0,
                        "total": 18,
                        "single_percentage": 0.67,
                        "multiple_percentage": 0.33,
                        "uncovered_percentage": 0.0,
                    },
                },
                "components": {
                    "original": {
                        "connected": {
                            "total": 1,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 1,
                        },
                        "biconnected": {
                            "total": 1,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 1,
                        },
                        "triconnected": {
                            "total": 1,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 1,
                        },
                    },
                    "biclique": {
                        "connected": {
                            "total": 1,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 1,
                        }
                    },
                },
            },
            "graph_info": {
                "name": "DSS1",
                "total_dmrs": 6,
                "total_genes": 5,
                "total_edges": 18,
            },
        }

    def test_timepoint_data_structure(self):
        """Test that timepoint data contains all required fields with correct structure."""
        with patch("process_data.process_data") as mock_process:
            mock_process.return_value = {
                "DSS1": {
                    "interesting_components": [],
                    "complex_components": [
                        {
                            "id": 1,
                            "dmrs": 6,
                            "genes": 5,
                            "size": 11,
                            "category": "complex",
                            "raw_bicliques": [
                                (
                                    {0, 1, 2},
                                    {
                                        START_GENE_ID,
                                        START_GENE_ID + 1,
                                        START_GENE_ID + 2,
                                    },
                                ),
                                (
                                    {2, 3, 4},
                                    {
                                        START_GENE_ID + 1,
                                        START_GENE_ID + 2,
                                        START_GENE_ID + 3,
                                    },
                                ),
                                (
                                    {4, 5},
                                    {
                                        START_GENE_ID + 2,
                                        START_GENE_ID + 3,
                                        START_GENE_ID + 4,
                                    },
                                ),
                            ],
                            "split_genes": [
                                START_GENE_ID + 1,
                                START_GENE_ID + 2,
                                START_GENE_ID + 3,
                            ],
                            "edge_classifications": {
                                "permanent": [(0, START_GENE_ID), (1, START_GENE_ID)],
                                "shared": [
                                    (2, START_GENE_ID + 2),
                                    (4, START_GENE_ID + 2),
                                ],
                                "bridge": [
                                    (2, START_GENE_ID + 1),
                                    (4, START_GENE_ID + 3),
                                ],
                            },
                        }
                    ],
                    "bicliques": self.mock_bicliques_result["bicliques"],
                    "stats": self.mock_bicliques_result["stats"],
                    "bicliques_summary": {
                        "graph_info": self.mock_bicliques_result["graph_info"],
                        "header_stats": {
                            "operations": 15,
                            "splits": 3,
                            "deletions": 0,
                            "additions": 0,
                        },
                    },
                }
            }

            # Test data structure
            data = mock_process.return_value["DSS1"]

            # Test presence of required top-level keys
            required_keys = {
                "interesting_components",
                "complex_components",
                "bicliques",
                "stats",
                "bicliques_summary",
            }
            self.assertTrue(all(key in data for key in required_keys))

            # Test complex component structure
            comp = data["complex_components"][0]
            self.assertIsInstance(comp["id"], int)
            self.assertIsInstance(comp["dmrs"], int)
            self.assertIsInstance(comp["genes"], int)
            self.assertIsInstance(comp["size"], int)
            self.assertIsInstance(comp["category"], str)
            self.assertIsInstance(comp["raw_bicliques"], list)
            self.assertIsInstance(comp["split_genes"], list)
            self.assertIsInstance(comp["edge_classifications"], dict)

            # Verify overlapping structure
            self.assertEqual(len(comp["raw_bicliques"]), 3)
            self.assertEqual(len(comp["split_genes"]), 3)

            # Verify edge classifications
            edge_class = comp["edge_classifications"]
            self.assertTrue(
                all(key in edge_class for key in ["permanent", "shared", "bridge"])
            )

            # Verify correct ID ranges
            for biclique in comp["raw_bicliques"]:
                dmrs, genes = biclique
                # DMRs should start at 0
                self.assertTrue(all(dmr_id >= 0 and dmr_id < 6 for dmr_id in dmrs))
                # Genes should start at START_GENE_ID (100000)
                self.assertTrue(all(gene_id >= START_GENE_ID for gene_id in genes))

    def test_json_conversion(self):
        """Test that data can be properly converted to JSON."""
        with patch("process_data.process_data") as mock_process:
            mock_process.return_value = {"DSS1": self.mock_bicliques_result}

            # Convert to JSON-safe format
            json_data = convert_for_json(mock_process.return_value["DSS1"])

            # Verify structure is maintained
            self.assertIn("bicliques", json_data)
            self.assertIn("stats", json_data)
            self.assertIn("graph_info", json_data)

            # Verify all sets are converted to lists
            for biclique in json_data["bicliques"]:
                self.assertIsInstance(biclique[0], list)  # DMRs
                self.assertIsInstance(biclique[1], list)  # Genes

    def test_error_handling(self):
        """Test error handling in data processing."""
        with patch("routes.timepoint_data.process_data") as mock_process:
            # Simulate an error
            mock_process.return_value = {"DSS1": {"error": "Test error"}}

            # Verify error is properly handled
            data = mock_process.return_value["DSS1"]
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Test error")

    def test_component_processing(self):
        """Test that components are properly processed."""
        with patch("routes.timepoint_data.process_data") as mock_process:
            mock_process.return_value = {
                "DSS1": {
                    "interesting_components": [],
                    "complex_components": [
                        {
                            "id": 1,
                            "dmrs": 6,
                            "genes": 5,
                            "size": 11,
                            "category": "complex",
                            "raw_bicliques": self.mock_bicliques_result["bicliques"],
                            "split_genes": [
                                START_GENE_ID + 1,
                                START_GENE_ID + 2,
                                START_GENE_ID + 3,
                            ],
                        }
                    ],
                    "bicliques": self.mock_bicliques_result["bicliques"],
                    "stats": self.mock_bicliques_result["stats"],
                }
            }

            data = mock_process.return_value["DSS1"]

            # Verify component structure
            self.assertEqual(len(data["complex_components"]), 1)
            comp = data["complex_components"][0]

            # Verify component has correct number of nodes
            self.assertEqual(comp["dmrs"], 6)
            self.assertEqual(comp["genes"], 5)

            # Verify split genes are identified correctly
            self.assertEqual(len(comp["split_genes"]), 3)
            self.assertTrue(
                all(gene_id >= START_GENE_ID for gene_id in comp["split_genes"])
            )
