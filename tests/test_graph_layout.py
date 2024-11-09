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
        self.assertEqual(positions, {1: (0, 0.5), 2: (1, 0.5)})

    def test_multiple_bicliques(self):
        bicliques = [({1}, {2}), ({3}, {4})]
        node_biclique_map = {1: [0], 2: [0], 3: [1], 4: [1]}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        self.assertEqual(
            positions,
            {
                1: (0, 0.3333333333333333),
                2: (1, 0.3333333333333333),
                3: (0, 0.6666666666666666),
                4: (1, 0.6666666666666666),
            },
        )

    def test_overlapping_nodes(self):
        bicliques = [({1, 3}, {2, 4})]
        node_biclique_map = {1: [0], 2: [0], 3: [0], 4: [0]}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        self.assertEqual(
            positions, {1: (0, 0.25), 2: (1, 0.25), 3: (0, 0.75), 4: (1, 0.75)}
        )

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
        
        # Test basic position requirements
        self.assertEqual(len(positions), 8)  # Total 8 nodes
        
        # Check x positions
        for node in [1, 2, 3, 4]:  # DMR nodes
            self.assertEqual(positions[node][0], 0)
        
        for node in [5, 6, 7, 8]:  # Gene nodes
            self.assertEqual(positions[node][0], 1)
        
        # Verify y-coordinate relationships
        # Split gene (node 6) should be positioned between its connected bicliques
        split_gene_y = positions[6][1]
        first_biclique_y = [positions[5][1]]  # y-coords of other genes in first biclique
        second_biclique_y = [positions[7][1], positions[8][1]]  # y-coords of other genes in second biclique
        
        # Split gene should be positioned between its connected bicliques
        self.assertTrue(
            min(first_biclique_y) <= split_gene_y <= max(second_biclique_y) or
            min(second_biclique_y) <= split_gene_y <= max(first_biclique_y),
            "Split gene should be positioned between its connected bicliques"
        )

    def test_empty_bicliques(self):
        bicliques = []
        node_biclique_map = {}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        self.assertEqual(positions, {})


if __name__ == "__main__":
    unittest.main()
