import unittest
from test_gene_processing import TestGeneProcessing
# Import other test classes as needed

def create_test_suite():
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGeneProcessing))
    # Add other test cases as needed
    
    return suite

if __name__ == '__main__':
    suite = create_test_suite()
    runner = unittest.TextTestRunner()
    runner.run(suite)
import unittest
from test_gene_processing import TestGeneProcessing
from test_classifier import TestClassifier
from test_statistics import TestStatistics
from tests.test_graph_layout_empty import TestEmptyBicliquesLayout

def create_test_suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGeneProcessing))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestClassifier))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStatistics))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEmptyBicliquesLayout))
    return suite

if __name__ == '__main__':
    suite = create_test_suite()
    runner = unittest.TextTestRunner()
    runner.run(suite)
