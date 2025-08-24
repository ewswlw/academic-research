#!/usr/bin/env python3
"""
Run Defense First Hybrid Approach Test
Tests the study's hybrid approach using underlying indices + ETFs
"""

from test_hybrid_data_approach import run_comprehensive_hybrid_test

if __name__ == "__main__":
    print("Starting Defense First Hybrid Approach Test...")
    print("This will test the study's hybrid approach using underlying indices + ETFs")
    print("Validating we can replicate the full 39-year backtest period")
    print()
    
    # Run the comprehensive test
    test_results = run_comprehensive_hybrid_test()
    
    print("\n" + "="*80)
    print("HYBRID APPROACH TEST COMPLETED")
    print("="*80)
    print(f"Tests Run: {test_results.testsRun}")
    print(f"Failures: {len(test_results.failures)}")
    print(f"Errors: {len(test_results.errors)}")
    
    if test_results.failures:
        print("\nFAILURES:")
        for test, traceback in test_results.failures:
            print(f"- {test}: {traceback}")
    
    if test_results.errors:
        print("\nERRORS:")
        for test, traceback in test_results.errors:
            print(f"- {test}: {traceback}")
    
    print("\nCheck the output above for hybrid data approach analysis.")
    print("This will determine if we can replicate the study's 39-year backtest.")
