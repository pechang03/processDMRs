import unittest
from visualization.traces import create_node_traces
from visualization.core import create_biclique_visualization
from utils.node_info import NodeInfo


class TestVisualization(unittest.TestCase):
    def setUp(self):
        # Create a basic NodeInfo object for testing
        from utils.constants import START_GENE_ID
        self.node_info = NodeInfo(
            all_nodes={1, 2, START_GENE_ID, START_GENE_ID + 1},  # Nodes 1,2 are DMRs, others are genes
            dmr_nodes={1, 2},
            regular_genes={START_GENE_ID},
            split_genes={START_GENE_ID + 1},
            node_degrees={1: 1, 2: 0, START_GENE_ID: 1, START_GENE_ID + 1: 2},
            min_gene_id=START_GENE_ID,
        )

        # Basic node positions
        self.node_positions = {
            1: (0, 0.2), 
            2: (0, 0.4), 
            START_GENE_ID: (1, 0.2), 
            START_GENE_ID + 1: (1, 0.4)
        }

        # Basic node labels
        self.node_labels = {
            1: "DMR_1", 
            2: "DMR_2", 
            START_GENE_ID: "Gene_1", 
            START_GENE_ID + 1: "Gene_2"
        }

    def test_create_node_traces_empty_bicliques(self):
        """Test node coloring when no bicliques are present"""
        node_biclique_map = {}  # Empty biclique map
        biclique_colors = ["red", "blue", "green"]

        traces = create_node_traces(
            self.node_info,
            self.node_positions,
            self.node_labels,
            node_biclique_map,
            biclique_colors,
        )

        # Should get two traces (one for DMRs, one for genes)
        self.assertEqual(len(traces), 2)

        # All nodes should be gray since there are no bicliques
        dmr_trace = traces[0]
        gene_trace = traces[1]

        self.assertTrue(all(color == "gray" for color in dmr_trace.marker.color))
        self.assertTrue(all(color == "gray" for color in gene_trace.marker.color))

    def test_create_node_traces_with_bicliques(self):
        """Test node coloring with valid biclique assignments"""
        from utils.constants import START_GENE_ID
        node_biclique_map = {
            1: [0],  # DMR in first biclique
            2: [0],  # DMR also in first biclique
            START_GENE_ID: [0],     # Gene in first biclique
            START_GENE_ID + 1: [0]  # Gene in first biclique
        }
        biclique_colors = ["red", "blue", "green"]

        traces = create_node_traces(
            self.node_info,
            self.node_positions,
            self.node_labels,
            node_biclique_map,
            biclique_colors,
        )

        dmr_trace = traces[0]
        gene_trace = traces[1]

        # Check colors
        self.assertEqual(list(dmr_trace.marker.color), ["red", "red"])  # Both DMRs in first biclique
        self.assertEqual(list(gene_trace.marker.color), ["red", "red"])  # Both genes in first biclique

    def test_create_node_traces_invalid_biclique_number(self):
        """Test handling of invalid biclique numbers"""
        node_biclique_map = {
            1: [3]  # Biclique index 3, but only 3 colors in list (indices 0-2)
        }
        biclique_colors = ["red", "blue", "green"]  # Only 3 colors

        traces = create_node_traces(
            self.node_info,
            self.node_positions,
            self.node_labels,
            node_biclique_map,
            biclique_colors,
        )

        dmr_trace = traces[0]
        # First DMR should be gray due to invalid biclique number
        self.assertEqual(dmr_trace.marker.color[0], "gray")

    def test_create_node_traces_empty_color_list(self):
        """Test handling of empty color list"""
        node_biclique_map = {
            1: [0]  # Biclique index 0
        }
        biclique_colors = []  # Empty color list

        traces = create_node_traces(
            self.node_info,
            self.node_positions,
            self.node_labels,
            node_biclique_map,
            biclique_colors,
        )

        dmr_trace = traces[0]
        # Should default to gray when no colors are available
        self.assertEqual(dmr_trace.marker.color[0], "gray")


if __name__ == "__main__":
    unittest.main()
