import unittest
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
        self.assertEqual(positions, {1: (0, 0.3333333333333333), 2: (1, 0.3333333333333333), 3: (0, 0.6666666666666666), 4: (1, 0.6666666666666666)})

    def test_overlapping_nodes(self):
        bicliques = [({1, 3}, {2, 4})]
        node_biclique_map = {1: [0], 2: [0], 3: [0], 4: [0]}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        self.assertEqual(positions, {1: (0, 0.25), 2: (1, 0.25), 3: (0, 0.75), 4: (1, 0.75)})

    def test_gene_split_bicliques(self):
        # Two bicliques: K_{2,2} and K_{2,3} with a shared gene (gene-split)
        # First biclique: DMRs {1,2} connected to genes {5,6}
        # Second biclique: DMRs {3,4} connected to genes {6,7,8}
        # Note: gene 6 is the split gene appearing in both bicliques
        bicliques = [
            ({1, 2}, {5, 6}),  # K_{2,2}
            ({3, 4}, {6, 7, 8})  # K_{2,3}
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
        
        # All DMRs should be at x=0, all genes at x=1
        for node, (x, y) in positions.items():
            if node <= 4:  # DMR nodes
                self.assertEqual(x, 0)
            else:  # Gene nodes
                self.assertEqual(x, 1)
        
        # Split gene (node 6) should be positioned between its bicliques
        split_gene_y = positions[6][1]
        first_biclique_genes_y = positions[5][1]
        second_biclique_genes_y = positions[7][1]
        
        # Split gene should be between its bicliques
        self.assertTrue(
            min(first_biclique_genes_y, second_biclique_genes_y) <= split_gene_y <= max(first_biclique_genes_y, second_biclique_genes_y),
            "Split gene should be positioned between its bicliques"
        )
        
        # Test relative positioning of bicliques
        # K_{2,2} should be above K_{2,3}
        k22_dmrs_y = [positions[1][1], positions[2][1]]
        k23_dmrs_y = [positions[3][1], positions[4][1]]
        
        self.assertTrue(
            min(k22_dmrs_y) > max(k23_dmrs_y),
            "K_{2,2} should be positioned above K_{2,3}"
        )

    def test_empty_bicliques(self):
        bicliques = []
        node_biclique_map = {}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        self.assertEqual(positions, {})

if __name__ == "__main__":
    unittest.main()
