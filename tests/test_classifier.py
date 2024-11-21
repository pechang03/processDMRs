import unittest
from biclique_analysis.classifier import classify_biclique, classify_biclique_types

class TestClassifier(unittest.TestCase):
    def test_classify_biclique(self):
        # Test trivial biclique
        self.assertEqual(classify_biclique({1}, {2}), "trivial")
        
        # Test small biclique
        self.assertEqual(classify_biclique({1, 2}, {3}), "small")
        self.assertEqual(classify_biclique({1}, {2, 3}), "small")
        
        # Test interesting biclique
        self.assertEqual(classify_biclique({1, 2, 3}, {4, 5, 6}), "interesting")
        
    def test_get_biclique_type_counts(self):
        bicliques = [
            ({1}, {2}),  # trivial
            ({1, 2}, {3}),  # small
            ({1}, {2, 3}),  # small
            ({1, 2, 3}, {4, 5, 6}),  # interesting
        ]
        
        counts = get_biclique_type_counts(bicliques)
        self.assertEqual(counts, {"trivial": 1, "small": 2, "interesting": 1})

if __name__ == '__main__':
    unittest.main()
