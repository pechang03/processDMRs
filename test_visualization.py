# test_visualization.py
import unittest
import networkx as nx
from visualization import create_node_traces
from utils.constants import START_GENE_ID

class TestVisualization(unittest.TestCase):
    def setUp(self):
        # Setup some test data
        self.graph = nx.Graph()
        self.graph.add_nodes_from([0, 1, START_GENE_ID, START_GENE_ID + 1])
        self.graph.add_edges_from([(0, START_GENE_ID), (1, START_GENE_ID + 1)])
        self.bicliques = [
            ({0}, {START_GENE_ID}),
            ({1}, {START_GENE_ID + 1})
        ]

    def test_invalid_biclique_number(self):
        """Test handling of invalid biclique numbers"""
        dmr_trace = create_node_traces(self.graph, self.bicliques, -1)
        self.assertEqual(dmr_trace.marker.color[0], "gray")

if __name__ == "__main__":
    unittest.main()
