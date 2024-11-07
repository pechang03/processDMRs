import unittest
from graph_layout import calculate_node_positions
import sys

sys.path.append("..")


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
        bicliques = [
            ({1, 2}, {5, 6}),  # First biclique
            ({3, 4}, {6, 7, 8})  # Second biclique
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
        
        # Check x positions and collect y positions by biclique
        first_biclique_dmr_y = []
        second_biclique_dmr_y = []
        first_biclique_gene_y = []
        second_biclique_gene_y = []
        
        for node, (x, y) in positions.items():
            if node <= 4:  # DMR nodes
                self.assertEqual(x, 0)
                if node in {1, 2}:
                    first_biclique_dmr_y.append(y)
                else:
                    second_biclique_dmr_y.append(y)
            else:  # Gene nodes
                self.assertEqual(x, 1)
                if node in {5, 6}:
                    first_biclique_gene_y.append(y)
                if node in {6, 7, 8}:
                    second_biclique_gene_y.append(y)
        
        # Split gene (node 6) should be positioned between its bicliques
        split_gene_y = positions[6][1]
        
        # Verify y-coordinate relationships
        self.assertTrue(
            min(first_biclique_gene_y) <= split_gene_y <= max(second_biclique_gene_y) or
            min(second_biclique_gene_y) <= split_gene_y <= max(first_biclique_gene_y),
            "Split gene should be positioned between its connected bicliques"
        )

    def test_empty_bicliques(self):
        bicliques = []
        node_biclique_map = {}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        self.assertEqual(positions, {})


if __name__ == "__main__":
    unittest.main()
