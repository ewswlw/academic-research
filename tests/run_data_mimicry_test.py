#!/usr/bin/env python3
"""
Run Defense First Data Mimicry Test
Tests exactly what data we can replicate from the academic study
"""

from test_defense_first_data_mimicry import run_comprehensive_mimicry_test

if __name__ == "__main__":
    print("Starting Defense First Data Mimicry Test...")
    print("This will test exactly what data we can replicate from the academic study")
    print("Testing both ETFs and proxy alternatives for maximum coverage")
    print()
    
    # Run the comprehensive test
    test_results = run_comprehensive_mimicry_test()
    
    print("\n" + "="*80)
    print("DATA MIMICRY TEST COMPLETED")
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
    
    print("\nCheck the output above for detailed data availability analysis.")
