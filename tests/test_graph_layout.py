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

    def test_empty_bicliques(self):
        bicliques = []
        node_biclique_map = {}
        positions = calculate_node_positions(bicliques, node_biclique_map)
        self.assertEqual(positions, {})

if __name__ == "__main__":
    unittest.main()
