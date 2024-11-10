import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from graph_layout import calculate_node_positions

class TestCalculateNodePositions(unittest.TestCase):
    def test_single_biclique(self):
        bicliques = [({1}, {2})]
        node_biclique_map = {1: [0], 2: [0]}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        
        # Check x positions
        self.assertEqual(positions[1][0], 0)  # DMR at x=0
        self.assertEqual(positions[2][0], 1)  # Regular gene at x=1
        
        # Check y positions
        self.assertAlmostEqual(positions[1][1], 0.5)  # DMR y position
        self.assertAlmostEqual(positions[2][1], 0.5)  # Gene y position

    def test_multiple_bicliques(self):
        bicliques = [({1}, {2}), ({3}, {4})]
        node_biclique_map = {1: [0], 2: [0], 3: [1], 4: [1]}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        
        # Check x positions
        self.assertEqual(positions[1][0], 0)  # DMR at x=0
        self.assertEqual(positions[3][0], 0)  # DMR at x=0
        self.assertEqual(positions[2][0], 1)  # Regular gene at x=1
        self.assertEqual(positions[4][0], 1)  # Regular gene at x=1
        
        # Check y positions are evenly spaced
        dmr_y_positions = sorted([positions[1][1], positions[3][1]])
        gene_y_positions = sorted([positions[2][1], positions[4][1]])
        
        # Verify spacing is consistent
        spacing = 1.0 / 5  # 4 nodes + 1 for spacing
        self.assertAlmostEqual(dmr_y_positions[1] - dmr_y_positions[0], spacing, places=3)
        self.assertAlmostEqual(gene_y_positions[1] - gene_y_positions[0], spacing, places=3)

    def test_overlapping_nodes(self):
        bicliques = [({1, 3}, {2, 4})]
        node_biclique_map = {1: [0], 2: [0], 3: [0], 4: [0]}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        
        # Check x positions
        self.assertEqual(positions[1][0], 0)  # DMR at x=0
        self.assertEqual(positions[3][0], 0)  # DMR at x=0
        self.assertEqual(positions[2][0], 1)  # Regular gene at x=1
        self.assertEqual(positions[4][0], 1)  # Regular gene at x=1
        
        # Check y positions are evenly spaced
        y_positions = sorted([pos[1] for pos in positions.values()])
        spacing = y_positions[1] - y_positions[0]
        
        for i in range(1, len(y_positions)):
            self.assertAlmostEqual(y_positions[i] - y_positions[i-1], spacing, places=3)

    def test_gene_split_bicliques(self):
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
        for node in [1, 2, 3, 4]:  # DMR nodes
            self.assertEqual(positions[node][0], 0)
        
        for node in [5, 7, 8]:  # Regular gene nodes
            self.assertEqual(positions[node][0], 1)
        
        # Split gene should be at x=1.1
        self.assertEqual(positions[6][0], 1.1)
        
        # Verify y positions are evenly spaced
        y_positions = sorted([pos[1] for pos in positions.values()])
        spacing = y_positions[1] - y_positions[0]
        
        for i in range(1, len(y_positions)):
            self.assertAlmostEqual(y_positions[i] - y_positions[i-1], spacing, places=3)

    def test_empty_bicliques(self):
        bicliques = []
        node_biclique_map = {}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        self.assertEqual(positions, {})

if __name__ == "__main__":
    unittest.main()
