import os
import sys
from pathlib import Path

def run_tests():
    """Run all tests."""
    print("Running all tests...")
    
    # Add parent directory to path
    parent_dir = str(Path(__file__).parent.parent)
    sys.path.append(parent_dir)
    
    # Import test modules
    try:
        from tests.test_volve_dataset import main as test_volve
        from tests.test_unisim_dataset import main as test_unisim
        from tests.test_spe10_dataset import main as test_spe10
        from tests.test_integration import TestSystemIntegration
    except ImportError as e:
        print(f"Error importing test modules: {e}")
        return
    
    # Run tests
    try:
        print("\n=== Testing with Volve Dataset ===")
        test_volve()
    except Exception as e:
        print(f"Error running Volve tests: {e}")
    
    try:
        print("\n=== Testing with UNISIM-I Dataset ===")
        test_unisim()
    except Exception as e:
        print(f"Error running UNISIM tests: {e}")
      try:
        print("\n=== Testing with SPE10 Dataset ===")
        test_spe10()
    except Exception as e:
        print(f"Error running SPE10 tests: {e}")
        
    try:
        print("\n=== Running Integration Tests ===")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestSystemIntegration)
        unittest.TextTestRunner(verbosity=2).run(suite)
    except Exception as e:
        print(f"Error running integration tests: {e}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    run_tests() 