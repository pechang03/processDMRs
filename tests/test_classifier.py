import unittest
from biclique_analysis.classifier import (
    classify_biclique, 
    classify_biclique_types,
    BicliqueSizeCategory
)

class TestClassifier(unittest.TestCase):
    def test_classify_biclique(self):
        # Test empty biclique
        self.assertEqual(classify_biclique(set(), set()), BicliqueSizeCategory.EMPTY)
        
        # Test simple biclique
        self.assertEqual(classify_biclique({1}, {2}), BicliqueSizeCategory.SIMPLE)
        
        # Test small bicliques are now considered simple
        self.assertEqual(classify_biclique({1, 2}, {3}), BicliqueSizeCategory.SIMPLE)
        self.assertEqual(classify_biclique({1}, {2, 3}), BicliqueSizeCategory.SIMPLE)
        
        # Test interesting biclique
        self.assertEqual(
            classify_biclique({1, 2, 3}, {4, 5, 6}), 
            BicliqueSizeCategory.INTERESTING
        )
        
    def test_classify_biclique_types(self):
        bicliques = [
            ({1}, {2}),  # simple
            ({1, 2}, {3}),  # simple 
            ({1}, {2, 3}),  # simple
            ({1, 2, 3}, {4, 5, 6}),  # interesting
        ]
        
        counts = classify_biclique_types(bicliques)
        expected = {
            "empty": 0,
            "simple": 3,
            "interesting": 1,
            "complex": 0
        }
        self.assertEqual(counts, expected)

if __name__ == '__main__':
    unittest.main()
