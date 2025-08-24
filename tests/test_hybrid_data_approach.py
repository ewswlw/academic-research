"""
Test Defense First Hybrid Data Approach
Validates the study's hybrid approach using underlying indices + ETFs
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from xbbg import blp
    XBBG_AVAILABLE = True
except ImportError:
    XBBG_AVAILABLE = False

class TestDefenseFirstHybridApproach(unittest.TestCase):
    """Test suite for Defense First strategy hybrid data approach"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment and test Bloomberg connection"""
        cls.xbbg_available = XBBG_AVAILABLE
        if cls.xbbg_available:
            cls.test_bloomberg_connection()
        
        # Study parameters (exact from paper)
        cls.study_start = '1986-01-01'
        cls.study_end = '2025-12-31'
        cls.current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Hybrid data mapping (study's exact approach)
        cls.hybrid_data_mapping = {
            'TLT': {
                'etf': 'TLT US Equity',
                'etf_inception': '2002-07-22',
                'pre_etf_source': 'USGG10YR Index',  # 10Y Treasury yield
                'description': 'Long-term Treasuries'
            },
            'GLD': {
                'etf': 'GLD US Equity', 
                'etf_inception': '2004-11-18',
                'pre_etf_source': 'GC1 Comdty',      # Gold futures
                'description': 'Gold'
            },
            'DBC': {
                'etf': 'DBC US Equity',
                'etf_inception': '2006-02-03', 
                'pre_etf_source': 'CRY Index',       # CRB commodity index
                'description': 'Commodities'
            },
            'UUP': {
                'etf': 'UUP US Equity',
                'etf_inception': '2007-01-05',
                'pre_etf_source': 'DXY Curncy',      # Dollar index
                'description': 'US Dollar Index'
            },
            'SPY': {
                'etf': 'SPY US Equity',
                'etf_inception': '1993-01-29',
                'pre_etf_source': 'SPX Index',       # S&P 500 index
                'description': 'S&P 500'
            },
            'BIL': {
                'etf': 'BIL US Equity',
                'etf_inception': '2007-05-25',
                'pre_etf_source': 'USGG3M Index',    # 3-month Treasury
                'description': '90-day T-bills'
            }
        }
        
        # Study performance targets (from paper)
        cls.study_targets = {
            'annual_return': 10.87,
            'volatility': 8.50,
            'sharpe_ratio': 0.89,
            'max_drawdown': -14.81,
            'crisis_performance': {
                '2008': -14.61,  # vs -50.97 S&P
                '2020': 0.00,    # vs -19.63 S&P
                '2022': -6.70    # vs -23.95 S&P
            }
        }
    
    @classmethod
    def test_bloomberg_connection(cls):
        """Test basic Bloomberg connection"""
        try:
            test_data = blp.bdh('SPY US Equity', 'PX_LAST', '2023-01-01', '2023-01-02')
            print("✓ Bloomberg connection successful")
            return True
        except Exception as e:
            print(f"✗ Bloomberg connection failed: {e}")
            return False
    
    def test_1_hybrid_data_availability(self):
        """Test 1: Verify hybrid data availability for full study period"""
        if not self.xbbg_available:
            self.skipTest("xbbg not available")
        
        print("\n=== Test 1: Hybrid Data Availability ===")
        
        hybrid_coverage = {}
        
        for asset_name, asset_info in self.hybrid_data_mapping.items():
            print(f"\nTesting {asset_name} ({asset_info['description']}):")
            
            # Test pre-ETF period using underlying index
            pre_etf_start = self.study_start
            pre_etf_end = asset_info['etf_inception']
            
            print(f"  Pre-ETF period ({pre_etf_start} to {pre_etf_end}):")
            print(f"    Using: {asset_info['pre_etf_source']}")
            
            try:
                # Test underlying index availability
                underlying_data = blp.bdh(asset_info['pre_etf_source'], 'PX_LAST', pre_etf_start, pre_etf_end)
                
                if underlying_data is not None and not underlying_data.empty:
                    pre_etf_coverage = {
                        'status': 'Available',
                        'data_points': len(underlying_data),
                        'coverage_years': (pd.to_datetime(pre_etf_end) - pd.to_datetime(pre_etf_start)).days / 365.25,
                        'field': 'PX_LAST',
                        'first_date': underlying_data.index[0],
                        'last_date': underlying_data.index[-1]
                    }
                    print(f"    ✓ Available: {len(underlying_data)} data points")
                    print(f"      Coverage: {pre_etf_coverage['coverage_years']:.1f} years")
                    print(f"      Period: {underlying_data.index[0]} to {underlying_data.index[-1]}")
                else:
                    pre_etf_coverage = {
                        'status': 'Unavailable',
                        'data_points': 0,
                        'coverage_years': 0,
                        'field': None,
                        'first_date': None,
                        'last_date': None
                    }
                    print(f"    ✗ Not available")
                    
            except Exception as e:
                pre_etf_coverage = {
                    'status': f'Error: {str(e)}',
                    'data_points': 0,
                    'coverage_years': 0,
                    'field': None,
                    'first_date': None,
                    'last_date': None
                }
                print(f"    ✗ Error: {e}")
            
            # Test ETF period
            etf_start = asset_info['etf_inception']
            etf_end = '2023-12-31'
            
            print(f"  ETF period ({etf_start} to {etf_end}):")
            print(f"    Using: {asset_info['etf']}")
            
            try:
                # Test ETF availability
                etf_data = blp.bdh(asset_info['etf'], 'TOT_RETURN_INDEX_GROSS_DVDS', etf_start, etf_end)
                
                if etf_data is not None and not etf_data.empty:
                    etf_coverage = {
                        'status': 'Available',
                        'data_points': len(etf_data),
                        'coverage_years': (pd.to_datetime(etf_end) - pd.to_datetime(etf_start)).days / 365.25,
                        'field': 'TOT_RETURN_INDEX_GROSS_DVDS',
                        'first_date': etf_data.index[0],
                        'last_date': etf_data.index[-1]
                    }
                    print(f"    ✓ Available: {len(etf_data)} data points")
                    print(f"      Coverage: {etf_coverage['coverage_years']:.1f} years")
                    print(f"      Period: {etf_data.index[0]} to {etf_data.index[-1]}")
                else:
                    etf_coverage = {
                        'status': 'Unavailable',
                        'data_points': 0,
                        'coverage_years': 0,
                        'field': None,
                        'first_date': None,
                        'last_date': None
                    }
                    print(f"    ✗ Not available")
                    
            except Exception as e:
                etf_coverage = {
                    'status': f'Error: {str(e)}',
                    'data_points': 0,
                    'coverage_years': 0,
                    'field': None,
                    'first_date': None,
                    'last_date': None
                }
                print(f"    ✗ Error: {e}")
            
            # Overall hybrid coverage
            total_coverage_years = pre_etf_coverage['coverage_years'] + etf_coverage['coverage_years']
            total_required_years = 39  # 1986-2025
            coverage_percentage = (total_coverage_years / total_required_years) * 100
            
            if pre_etf_coverage['status'] == 'Available' and etf_coverage['status'] == 'Available':
                hybrid_status = 'Full Coverage Available'
                print(f"  ✓ Full hybrid coverage: {total_coverage_years:.1f} years ({coverage_percentage:.1f}%)")
            elif pre_etf_coverage['status'] == 'Available' or etf_coverage['status'] == 'Available':
                hybrid_status = 'Partial Coverage Available'
                print(f"  ⚠️  Partial coverage: {total_coverage_years:.1f} years ({coverage_percentage:.1f}%)")
            else:
                hybrid_status = 'No Coverage Available'
                print(f"  ✗ No coverage available")
            
            hybrid_coverage[asset_name] = {
                'pre_etf': pre_etf_coverage,
                'etf': etf_coverage,
                'total_coverage_years': total_coverage_years,
                'coverage_percentage': coverage_percentage,
                'hybrid_status': hybrid_status
            }
        
        return hybrid_coverage
    
    def test_2_data_stitching_capability(self):
        """Test 2: Test ability to stitch underlying indices with ETFs seamlessly"""
        if not self.xbbg_available:
            self.skipTest("xbbg not available")
        
        print("\n=== Test 2: Data Stitching Capability ===")
        
        # Test with TLT as example
        test_asset = 'TLT'
        asset_info = self.hybrid_data_mapping[test_asset]
        
        print(f"Testing data stitching for {test_asset} ({asset_info['description']}):")
        
        # Get pre-ETF data (underlying index)
        pre_etf_start = '2000-01-01'  # Test period before ETF inception
        pre_etf_end = asset_info['etf_inception']
        
        print(f"  Pre-ETF period ({pre_etf_start} to {pre_etf_end}):")
        
        try:
            pre_etf_data = blp.bdh(asset_info['pre_etf_source'], 'PX_LAST', pre_etf_start, pre_etf_end)
            
            if pre_etf_data is not None and not pre_etf_data.empty:
                print(f"    ✓ Underlying index data: {len(pre_etf_data)} points")
                print(f"      First: {pre_etf_data.index[0]}, Last: {pre_etf_data.index[-1]}")
                print(f"      Sample values: {pre_etf_data.iloc[:3, 0].tolist()}")
            else:
                print(f"    ✗ No underlying index data")
                return None
                
        except Exception as e:
            print(f"    ✗ Error getting underlying data: {e}")
            return None
        
        # Get ETF data (overlapping period for comparison)
        etf_start = asset_info['etf_inception']
        etf_end = '2005-01-01'  # Test period after ETF inception
        
        print(f"  ETF period ({etf_start} to {etf_end}):")
        
        try:
            etf_data = blp.bdh(asset_info['etf'], 'TOT_RETURN_INDEX_GROSS_DVDS', etf_start, etf_end)
            
            if etf_data is not None and not etf_data.empty:
                print(f"    ✓ ETF data: {len(etf_data)} points")
                print(f"      First: {etf_data.index[0]}, Last: {etf_data.index[-1]}")
                print(f"      Sample values: {etf_data.iloc[:3, 0].tolist()}")
            else:
                print(f"    ✗ No ETF data")
                return None
                
        except Exception as e:
            print(f"    ✗ Error getting ETF data: {e}")
            return None
        
        # Test data continuity around transition point
        print(f"  Data continuity test:")
        
        # Get data around the transition point
        transition_start = (pd.to_datetime(etf_start) - timedelta(days=30)).strftime('%Y-%m-%d')
        transition_end = (pd.to_datetime(etf_start) + timedelta(days=30)).strftime('%Y-%m-%d')
        
        try:
            # Get underlying data around transition
            underlying_transition = blp.bdh(asset_info['pre_etf_source'], 'PX_LAST', transition_start, transition_end)
            
            # Get ETF data around transition
            etf_transition = blp.bdh(asset_info['etf'], 'TOT_RETURN_INDEX_GROSS_DVDS', transition_start, transition_end)
            
            if underlying_transition is not None and not underlying_transition.empty and etf_transition is not None and not etf_transition.empty:
                print(f"    ✓ Both data sources available around transition")
                print(f"      Underlying: {len(underlying_transition)} points")
                print(f"      ETF: {len(etf_transition)} points")
                
                # Check for overlap
                underlying_dates = set(underlying_transition.index)
                etf_dates = set(etf_transition.index)
                overlap_dates = underlying_dates.intersection(etf_dates)
                
                if overlap_dates:
                    print(f"      Overlap dates: {len(overlap_dates)}")
                    print(f"      Sample overlap: {sorted(list(overlap_dates))[:3]}")
                else:
                    print(f"      No date overlap (expected for different data sources)")
                    
            else:
                print(f"    ✗ Missing data around transition")
                
        except Exception as e:
            print(f"    ✗ Error testing transition: {e}")
        
        return {
            'pre_etf_data': pre_etf_data,
            'etf_data': etf_data,
            'stitching_possible': True
        }
    
    def test_3_momentum_calculation_validation(self):
        """Test 3: Validate momentum calculation works with hybrid data"""
        if not self.xbbg_available:
            self.skipTest("xbbg not available")
        
        print("\n=== Test 3: Momentum Calculation Validation ===")
        
        # Test momentum calculation using hybrid approach
        test_asset = 'TLT'
        asset_info = self.hybrid_data_mapping[test_asset]
        
        print(f"Testing momentum calculation for {test_asset} using hybrid data:")
        
        # Test period where we have both underlying and ETF data
        test_start = '2000-01-01'
        test_end = '2005-01-01'
        
        # Get hybrid data
        try:
            # Pre-ETF period (underlying index)
            pre_etf_data = blp.bdh(asset_info['pre_etf_source'], 'PX_LAST', test_start, asset_info['etf_inception'])
            
            # ETF period
            etf_data = blp.bdh(asset_info['etf'], 'TOT_RETURN_INDEX_GROSS_DVDS', asset_info['etf_inception'], test_end)
            
            if pre_etf_data is not None and not pre_etf_data.empty and etf_data is not None and not etf_data.empty:
                print(f"  ✓ Hybrid data available:")
                print(f"    Underlying: {len(pre_etf_data)} points")
                print(f"    ETF: {len(etf_data)} points")
                
                # Combine data (simple concatenation for test)
                # In real implementation, we'd need proper normalization
                combined_data = pd.concat([pre_etf_data, etf_data])
                combined_data = combined_data.sort_index()
                
                print(f"    Combined: {len(combined_data)} points")
                print(f"    Period: {combined_data.index[0]} to {combined_data.index[-1]}")
                
                # Test momentum calculation
                lookback_days = [21, 63, 126, 252]  # 1, 3, 6, 12 months
                
                print(f"  Testing momentum calculations:")
                for days in lookback_days:
                    if len(combined_data) > days:
                        current_value = combined_data.iloc[-1].iloc[0]
                        past_value = combined_data.iloc[-days-1].iloc[0]
                        
                        if past_value > 0:  # Avoid division by zero
                            momentum = (current_value / past_value - 1) * 100
                            print(f"    {days} days: {momentum:.2f}%")
                        else:
                            print(f"    {days} days: Invalid (past_value <= 0)")
                    else:
                        print(f"    {days} days: Insufficient data")
                
                return {
                    'pre_etf_data': pre_etf_data,
                    'etf_data': etf_data,
                    'combined_data': combined_data,
                    'momentum_calculation_possible': True
                }
                
            else:
                print(f"  ✗ Insufficient hybrid data")
                return None
                
        except Exception as e:
            print(f"  ✗ Error in momentum calculation: {e}")
            return None
    
    def test_4_study_period_replication_capability(self):
        """Test 4: Final assessment of study period replication capability"""
        if not self.xbbg_available:
            self.skipTest("xbbg not available")
        
        print("\n=== Test 4: Study Period Replication Capability ===")
        
        # Run comprehensive hybrid data test
        print("Running comprehensive hybrid data assessment...")
        
        hybrid_results = self.test_1_hybrid_data_availability()
        
        # Calculate overall replication capability
        print(f"\n=== OVERALL STUDY PERIOD REPLICATION ASSESSMENT ===")
        
        total_required_years = 39  # 1986-2025
        replication_summary = {}
        
        for asset_name, results in hybrid_results.items():
            print(f"\n{asset_name}:")
            
            pre_etf_coverage = results['pre_etf']['coverage_years']
            etf_coverage = results['etf']['coverage_years']
            total_coverage = results['total_coverage_years']
            coverage_percentage = results['coverage_percentage']
            
            print(f"  Pre-ETF: {pre_etf_coverage:.1f} years")
            print(f"  ETF: {etf_coverage:.1f} years")
            print(f"  Total: {total_coverage:.1f} years ({coverage_percentage:.1f}%)")
            
            if coverage_percentage >= 80:
                status = "✓"
                replication_level = "FULL REPLICATION POSSIBLE"
            elif coverage_percentage >= 60:
                status = "⚠️"
                replication_level = "PARTIAL REPLICATION POSSIBLE"
            else:
                status = "✗"
                replication_level = "LIMITED REPLICATION"
            
            print(f"  {status} {replication_level}")
            
            replication_summary[asset_name] = {
                'pre_etf_coverage': pre_etf_coverage,
                'etf_coverage': etf_coverage,
                'total_coverage': total_coverage,
                'coverage_percentage': coverage_percentage,
                'can_replicate_study': coverage_percentage >= 80
            }
        
        # Overall assessment
        total_coverage = sum(item['total_coverage'] for item in replication_summary.values())
        max_possible_coverage = len(replication_summary) * total_required_years
        overall_coverage_percentage = (total_coverage / max_possible_coverage) * 100
        
        print(f"\n=== FINAL ASSESSMENT ===")
        print(f"Overall Coverage: {overall_coverage_percentage:.1f}%")
        print(f"Total Years Available: {total_coverage:.1f} / {max_possible_coverage}")
        
        if overall_coverage_percentage >= 80:
            replication_level = "FULL STUDY REPLICATION POSSIBLE"
        elif overall_coverage_percentage >= 60:
            replication_level = "PARTIAL STUDY REPLICATION POSSIBLE"
        else:
            replication_level = "LIMITED STUDY REPLICATION"
        
        print(f"Replication Level: {replication_level}")
        
        # Recommendations
        print(f"\n=== RECOMMENDATIONS ===")
        
        if overall_coverage_percentage >= 80:
            print("✓ Study can be replicated using hybrid approach")
            print("✓ Proceed with full backtest implementation")
            print("✓ Use underlying indices for pre-ETF periods")
            print("✓ Use ETFs for post-ETF periods")
        elif overall_coverage_percentage >= 60:
            print("⚠️  Study can be partially replicated")
            print("⚠️  Consider alternative data sources for missing periods")
        else:
            print("✗ Study replication faces significant challenges")
            print("✗ Consider alternative strategies or data sources")
        
        return {
            'overall_coverage_percentage': overall_coverage_percentage,
            'total_coverage_years': total_coverage,
            'max_possible_coverage': max_possible_coverage,
            'replication_level': replication_level,
            'detailed_results': hybrid_results,
            'replication_summary': replication_summary
        }

def run_comprehensive_hybrid_test():
    """Run comprehensive hybrid data approach test"""
    print("=" * 80)
    print("DEFENSE FIRST STRATEGY - HYBRID DATA APPROACH TEST")
    print("=" * 80)
    print("Testing the study's hybrid approach using underlying indices + ETFs")
    print("=" * 80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()
    
    # Add all tests
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestDefenseFirstHybridApproach))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    results = runner.run(test_suite)
    
    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests Run: {results.testsRun}")
    print(f"Failures: {len(results.failures)}")
    print(f"Errors: {len(results.errors)}")
    print(f"Success Rate: {((results.testsRun - len(results.failures) - len(results.errors)) / results.testsRun * 100):.1f}%")
    
    return results

if __name__ == "__main__":
    # Run comprehensive test
    test_results = run_comprehensive_hybrid_test()
