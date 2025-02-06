import unittest
import sys
import os
from backend.app.visualization.graph_layout_logical import calculate_node_positions

class TestGeneSplitBicliques(unittest.TestCase):
    def test_split_gene_positions(self):
        """Test positioning of split genes (genes appearing in multiple bicliques)"""
        from backend.app.utils.constants import START_GENE_ID
        bicliques = [
            ({1, 2}, {START_GENE_ID, START_GENE_ID + 1}),  # First biclique
            ({3, 4}, {START_GENE_ID + 1, START_GENE_ID + 2, START_GENE_ID + 3})  # Second biclique
        ]
        node_biclique_map = {
            1: [0], 2: [0],  # DMRs in first biclique
            3: [1], 4: [1],  # DMRs in second biclique
            START_GENE_ID: [0],          # Gene only in first biclique
            START_GENE_ID + 1: [0, 1],   # Split gene (in both bicliques)
            START_GENE_ID + 2: [1], 
            START_GENE_ID + 3: [1]       # Genes only in second biclique
        }

        positions = calculate_node_positions(bicliques, node_biclique_map)

        # Test x positions
        for dmr in [1, 2, 3, 4]:
            self.assertEqual(positions[dmr][0], 0)  # DMRs at x=0

        # Regular genes at x=1
        self.assertEqual(positions[START_GENE_ID][0], 1)
        self.assertEqual(positions[START_GENE_ID + 2][0], 1)
        self.assertEqual(positions[START_GENE_ID + 3][0], 1)

        # Split gene at x=1.1
        self.assertEqual(positions[START_GENE_ID + 1][0], 1.1)

if __name__ == "__main__":
    unittest.main()
