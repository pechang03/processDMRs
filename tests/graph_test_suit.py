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
