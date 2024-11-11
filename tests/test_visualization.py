import unittest
from biclique_visualization import create_node_traces
from node_info import NodeInfo

class TestVisualization(unittest.TestCase):
    def setUp(self):
        # Create a basic NodeInfo object for testing
        self.node_info = NodeInfo(
            all_nodes={1, 2, 3, 4},  # Nodes 1,2 are DMRs, 3,4 are genes
            dmr_nodes={1, 2},
            regular_genes={3},
            split_genes={4},
            node_degrees={1: 1, 2: 0, 3: 1, 4: 2},
            min_gene_id=3
        )
        
        # Basic node positions
        self.node_positions = {
            1: (0, 0.2),
            2: (0, 0.4),
            3: (1, 0.2),
            4: (1, 0.4)
        }
        
        # Basic node labels
        self.node_labels = {
            1: "DMR_1",
            2: "DMR_2",
            3: "Gene_3",
            4: "Gene_4"
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
            biclique_colors
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
        node_biclique_map = {
            1: [1],  # Node 1 in first biclique
            3: [1],  # Node 3 in first biclique
            4: [1, 2]  # Node 4 in first and second bicliques
        }
        biclique_colors = ["red", "blue", "green"]
        
        traces = create_node_traces(
            self.node_info,
            self.node_positions,
            self.node_labels,
            node_biclique_map,
            biclique_colors
        )
        
        dmr_trace = traces[0]
        gene_trace = traces[1]
        
        # Check DMR colors
        self.assertEqual(dmr_trace.marker.color, ["red", "gray"])  # DMR 1 red, DMR 2 gray
        
        # Check gene colors
        self.assertEqual(gene_trace.marker.color, ["red", "red"])  # Both genes red (first biclique)

    def test_create_node_traces_invalid_biclique_number(self):
        """Test handling of invalid biclique numbers"""
        node_biclique_map = {
            1: [4]  # Biclique number larger than available colors
        }
        biclique_colors = ["red", "blue", "green"]  # Only 3 colors
        
        traces = create_node_traces(
            self.node_info,
            self.node_positions,
            self.node_labels,
            node_biclique_map,
            biclique_colors
        )
        
        dmr_trace = traces[0]
        # First DMR should be gray due to invalid biclique number
        self.assertEqual(dmr_trace.marker.color[0], "gray")

    def test_create_node_traces_empty_color_list(self):
        """Test handling of empty color list"""
        node_biclique_map = {
            1: [1]  # Valid biclique number but no colors available
        }
        biclique_colors = []  # Empty color list
        
        traces = create_node_traces(
            self.node_info,
            self.node_positions,
            self.node_labels,
            node_biclique_map,
            biclique_colors
        )
        
        dmr_trace = traces[0]
        # Should default to gray when no colors are available
        self.assertEqual(dmr_trace.marker.color[0], "gray")

if __name__ == '__main__':
    unittest.main()
