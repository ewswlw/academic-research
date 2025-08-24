"""
Run Defense First Strategy Fixes Test
Executes comprehensive validation of all critical fixes
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Run the fixes test suite"""
    
    print("=" * 80)
    print("DEFENSE FIRST STRATEGY - CRITICAL FIXES VALIDATION")
    print("=" * 80)
    print("Testing all critical fixes:")
    print("1. SPY Benchmark Calculation Fix")
    print("2. Crisis Period Analysis Fix")
    print("3. Data Normalization Improvement")
    print("4. Performance Calculation Validation")
    print("5. Data Period Extension Validation")
    print("6. VectorBT Integration Attempt")
    print("=" * 80)
    
    try:
        # Import and run the test
        from test_defense_first_fixes import TestDefenseFirstFixes
        
        # Create test suite
        import unittest
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDefenseFirstFixes)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print("\n" + "=" * 80)
        print("FIXES VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
        
        if result.failures:
            print(f"\nFailures:")
            for test, traceback in result.failures:
                print(f"  ✗ {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print(f"\nErrors:")
            for test, traceback in result.errors:
                print(f"  ✗ {test}: {traceback.split('Exception:')[-1].strip()}")
        
        if result.wasSuccessful():
            print(f"\n✓ All fixes validation tests passed!")
        else:
            print(f"\n⚠️  Some fixes validation tests failed - review above")
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Error importing test module: {e}")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
