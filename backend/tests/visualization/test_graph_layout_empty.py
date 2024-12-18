import unittest
from backend.app.visualization.graph_layout_logical import (
    calculate_node_positions,
    collect_node_information,
    position_remaining_nodes,
)
from backend.app.utils.node_info import NodeInfo


class TestEmptyBicliquesLayout(unittest.TestCase):
    def setUp(self):
        # Setup some test data
        self.empty_bicliques = []
        from backend.app.utils.constants import START_GENE_ID
        self.node_biclique_map = {
            0: [],  # DMR node
            1: [],  # DMR node
            START_GENE_ID: [],     # Gene node
            START_GENE_ID + 1: [], # Gene node
        }

    def test_empty_bicliques(self):
        """Test that empty bicliques are handled correctly"""
        positions = calculate_node_positions(
            self.empty_bicliques, self.node_biclique_map
        )

        # Check that all nodes got positions
        self.assertEqual(len(positions), len(self.node_biclique_map))

        # Check that DMRs are on left (x=0) and genes on right (x=1)
        for node_id, (x, y) in positions.items():
            if node_id < 3:  # DMR nodes
                self.assertEqual(x, 0, f"DMR node {node_id} should be at x=0")
            else:  # Gene nodes
                self.assertEqual(x, 1, f"Gene node {node_id} should be at x=1")

        # Check that y positions are spaced properly
        y_positions = [y for _, y in positions.values()]
        y_positions.sort()
        for i in range(1, len(y_positions)):
            self.assertGreater(
                y_positions[i],
                y_positions[i - 1],
                "Y positions should be strictly increasing",
            )

    def test_node_info_empty_bicliques(self):
        """Test that NodeInfo is created correctly with empty bicliques"""
        node_info = collect_node_information(
            self.empty_bicliques, self.node_biclique_map
        )

        self.assertIsInstance(node_info, NodeInfo)
        self.assertEqual(len(node_info.all_nodes), len(self.node_biclique_map))
        self.assertEqual(len(node_info.dmr_nodes), 2)  # Nodes 0 and 1
        self.assertEqual(len(node_info.regular_genes), 2)  # Nodes 3 and 4
        self.assertEqual(len(node_info.split_genes), 0)  # No split genes in empty case

    def test_position_remaining_nodes(self):
        """Test that position_remaining_nodes handles all nodes correctly"""
        node_info = collect_node_information(
            self.empty_bicliques, self.node_biclique_map
        )
        positions = {}
        current_y = 0
        spacing = 0.2

        positions = position_remaining_nodes(positions, node_info, current_y, spacing)

        # Check that all nodes got positions
        self.assertEqual(len(positions), len(self.node_biclique_map))

        # Verify x positions
        for node_id, (x, _) in positions.items():
            if node_id < 3:
                self.assertEqual(x, 0, f"DMR node {node_id} should be at x=0")
            else:
                self.assertEqual(x, 1, f"Gene node {node_id} should be at x=1")

    def test_empty_bicliques_with_split_genes(self):
        """Test handling of split genes in empty bicliques case"""
        # Modify node_biclique_map to include a split gene
        self.node_biclique_map[5] = []  # Add a split gene
        node_info = collect_node_information(
            self.empty_bicliques, self.node_biclique_map
        )

        positions = calculate_node_positions(
            self.empty_bicliques, self.node_biclique_map
        )

        # Check that all nodes got positions
        self.assertEqual(len(positions), len(self.node_biclique_map))

        # Check specific positions for split genes
        for node_id, (x, _) in positions.items():
            if node_id < 3:  # DMR nodes
                self.assertEqual(x, 0)
            elif node_id == 5:  # Split gene
                self.assertEqual(x, 1.1)
            else:  # Regular genes
                self.assertEqual(x, 1)


if __name__ == "__main__":
    unittest.main()
