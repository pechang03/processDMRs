import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from visualization.graph_layout_logical import calculate_node_positions

class TestGeneSplitBicliques(unittest.TestCase):
    def test_split_gene_positions(self):
        """Test positioning of split genes (genes appearing in multiple bicliques)"""
        bicliques = [
            ({1, 2}, {5, 6}),  # First biclique
            ({3, 4}, {6, 7, 8})  # Second biclique, gene 6 appears in both
        ]
        node_biclique_map = {
            1: [0], 2: [0],  # DMRs in first biclique
            3: [1], 4: [1],  # DMRs in second biclique
            5: [0],          # Gene only in first biclique
            6: [0, 1],       # Split gene (in both bicliques)
            7: [1], 8: [1]   # Genes only in second biclique
        }

        positions = calculate_node_positions(bicliques, node_biclique_map)

        # Test x positions
        self.assertEqual(positions[1][0], 0)  # DMR at x=0
        self.assertEqual(positions[3][0], 0)  # DMR at x=0
        self.assertEqual(positions[2][0], 0)  # DMR at x=0
        self.assertEqual(positions[4][0], 0)  # DMR at x=0

        # Regular genes at x=1
        self.assertEqual(positions[5][0], 1)  # Regular gene at x=1
        self.assertEqual(positions[7][0], 1)  # Regular gene at x=1
        self.assertEqual(positions[8][0], 1)  # Regular gene at x=1

        # Split gene should be at x=1.1
        self.assertEqual(positions[6][0], 1.1)

        # Check y positions are monotonically increasing within each biclique
        y_positions = sorted([pos[1] for pos in positions.values()])
        
        # Verify all spacings are positive
        for i in range(1, len(y_positions)):
            self.assertGreater(y_positions[i] - y_positions[i-1], 0)

        # Verify bicliques are separated
        first_biclique_nodes = {1, 2, 5, 6}
        second_biclique_nodes = {3, 4, 6, 7, 8}
        
        max_y_first = max(positions[n][1] for n in first_biclique_nodes)
        min_y_second = min(positions[n][1] for n in second_biclique_nodes)
        
        self.assertGreater(min_y_second, max_y_first)

if __name__ == "__main__":
    unittest.main()
