import unittest
import sys
import os

# Add the parent directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_gene_processing import TestGeneProcessing
from test_classifier import TestClassifier
from test_statistics import TestStatistics
from test_graph_layout_empty import TestEmptyBicliquesLayout
from test_graph_layout import TestCalculateNodePositions
from test_visualization import TestVisualization
from test_gene_split_bicliques import TestGeneSplitBicliques
from test_graph_statistics import TestGraphStatistics

def create_test_suite():
    """Discover and run all tests in the tests directory."""
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGeneProcessing))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestClassifier))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStatistics))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEmptyBicliquesLayout))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCalculateNodePositions))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestVisualization))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGeneSplitBicliques))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGraphStatistics))
    
    return suite

if __name__ == '__main__':
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
import unittest
import sys
import os

# Add the parent directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Discover and run all tests in the tests directory."""
    # Get the directory containing this file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Discover all tests in the tests directory
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests and return the result
    result = runner.run(suite)
    
    # Return 0 for success, 1 for failures
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
