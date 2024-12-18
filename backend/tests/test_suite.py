import unittest
from backend.tests.core.test_gene_processing import TestGeneProcessing
from backend.tests.biclique_analysis.test_classifier import TestClassifier
from backend.tests.core.test_statistics import TestStatistics
from backend.tests.visualization.test_graph_layout_empty import TestEmptyBicliquesLayout
# Import other test classes as needed


def create_test_suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGeneProcessing))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestClassifier))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStatistics))
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestEmptyBicliquesLayout)
    )
    return suite


if __name__ == "__main__":
    suite = create_test_suite()
    runner = unittest.TextTestRunner()
    runner.run(suite)
