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

def create_test_suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGeneProcessing))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestClassifier))
    return suite

if __name__ == '__main__':
    suite = create_test_suite()
    runner = unittest.TextTestRunner()
    runner.run(suite)
