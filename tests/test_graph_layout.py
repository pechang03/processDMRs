import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from visualization.graph_layout_logical import calculate_node_positions


class TestCalculateNodePositions(unittest.TestCase):
    def test_single_biclique(self):
        """Test single biclique with equal DMRs and genes"""
        bicliques = [({1}, {2})]
        node_biclique_map = {1: [0], 2: [0]}
        positions = calculate_node_positions(bicliques, node_biclique_map)

        # Check x positions
        self.assertEqual(positions[1][0], 0)  # DMR at x=0
        self.assertEqual(positions[2][0], 1)  # Regular gene at x=1

        # Check y positions - should be same since equal numbers
        self.assertAlmostEqual(positions[1][1], positions[2][1])

    def test_multiple_bicliques_equal_nodes(self):
        """Test multiple bicliques with equal DMRs and genes in each"""
        bicliques = [({1, 2}, {3, 4}), ({5, 6}, {7, 8})]
        node_biclique_map = {
            1: [0],
            2: [0],
            3: [0],
            4: [0],
            5: [1],
            6: [1],
            7: [1],
            8: [1],
        }
        positions = calculate_node_positions(bicliques, node_biclique_map)

        # Check x positions
        for dmr in [1, 2, 5, 6]:
            self.assertEqual(positions[dmr][0], 0)  # DMRs at x=0
        for gene in [3, 4, 7, 8]:
            self.assertEqual(positions[gene][0], 1)  # Genes at x=1

        # Check y positions - pairs should match within each biclique
        # First biclique
        dmr_positions_1 = sorted([positions[1][1], positions[2][1]])
        gene_positions_1 = sorted([positions[3][1], positions[4][1]])
    
        # Second biclique
        dmr_positions_2 = sorted([positions[5][1], positions[6][1]])
        gene_positions_2 = sorted([positions[7][1], positions[8][1]])

        # Verify spacing within bicliques
        spacing_1 = dmr_positions_1[1] - dmr_positions_1[0]
        spacing_2 = dmr_positions_2[1] - dmr_positions_2[0]
    
        # Check that spacings are positive
        self.assertGreater(spacing_1, 0)
        self.assertGreater(spacing_2, 0)

        # Verify biclique separation
        biclique_spacing = dmr_positions_2[0] - dmr_positions_1[1]
        self.assertGreater(biclique_spacing, 0)

    def test_unequal_nodes(self):
        """Test biclique with unequal numbers of DMRs and genes"""
        bicliques = [({1, 2, 3}, {4, 5})]
        node_biclique_map = {1: [0], 2: [0], 3: [0], 4: [0], 5: [0]}
        positions = calculate_node_positions(bicliques, node_biclique_map)

        # Check x positions
        for dmr in [1, 2, 3]:
            self.assertEqual(positions[dmr][0], 0)  # DMRs at x=0
        for gene in [4, 5]:
            self.assertEqual(positions[gene][0], 1)  # Genes at x=1

        # Get sorted positions for each side
        dmr_positions = sorted([positions[dmr][1] for dmr in [1, 2, 3]])
        gene_positions = sorted([positions[gene][1] for gene in [4, 5]])

        # Verify spacing is positive and consistent within each side
        dmr_spacing = dmr_positions[1] - dmr_positions[0]
        gene_spacing = gene_positions[1] - gene_positions[0]
    
        self.assertGreater(dmr_spacing, 0)
        self.assertGreater(gene_spacing, 0)
    
        # Verify the third DMR spacing
        self.assertAlmostEqual(dmr_positions[2] - dmr_positions[1], dmr_spacing)

    def test_overlapping_bicliques(self):
        """Test overlapping bicliques with shared nodes"""
        bicliques = [({1, 2}, {3, 4}), ({2, 5}, {4, 6})]
        node_biclique_map = {1: [0], 2: [0, 1], 3: [0], 4: [0, 1], 5: [1], 6: [1]}
        positions = calculate_node_positions(bicliques, node_biclique_map)

        # Check x positions
        for dmr in [1, 2, 5]:
            self.assertEqual(positions[dmr][0], 0)
        for gene in [3, 6]:
            self.assertEqual(positions[gene][0], 1)
        # Split genes at x=1.1
        self.assertEqual(
            positions[4][0], 1.1
        )  # Node 4 appears in both biclique_spacing

        # Check y positions are monotonically increasing
        y_positions = sorted([pos[1] for pos in positions.values()])
        
        # Verify all spacings are positive
        for i in range(1, len(y_positions)):
            self.assertGreater(y_positions[i] - y_positions[i-1], 0)


if __name__ == "__main__":
    unittest.main()
