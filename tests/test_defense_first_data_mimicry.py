"""
Test Defense First Data Mimicry Capabilities
Verifies exactly what data we can replicate from the academic study
Tests both ETFs and proxy alternatives for maximum coverage
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

class TestDefenseFirstDataMimicry(unittest.TestCase):
    """Test suite for Defense First strategy data mimicry using xbbg"""
    
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
        
        # Required assets from study
        cls.required_assets = {
            'defensive': {
                'TLT US Equity': 'Long-term Treasuries',
                'GLD US Equity': 'Gold', 
                'DBC US Equity': 'Commodities',
                'UUP US Equity': 'US Dollar Index'
            },
            'equity_fallback': 'SPY US Equity',
            'cash_proxy': 'BIL US Equity'
        }
        
        # Potential proxy alternatives for pre-ETF periods
        cls.proxy_alternatives = {
            'TLT_proxy': 'USGG10YR Index',  # 10Y Treasury yield
            'GLD_proxy': 'GC1 Comdty',      # Gold futures
            'DBC_proxy': 'CRY Index',       # CRB commodity index
            'UUP_proxy': 'DXY Curncy',      # Dollar index
            'SPY_proxy': 'SPX Index',       # S&P 500 index
            'BIL_proxy': 'USGG3M Index'     # 3-month Treasury
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
    
    def test_1_etf_data_availability_periods(self):
        """Test 1: Verify exact ETF data availability periods"""
        if not self.xbbg_available:
            self.skipTest("xbbg not available")
        
        print("\n=== Test 1: ETF Data Availability Periods ===")
        
        etf_coverage = {}
        
        for asset_name, asset_desc in self.required_assets['defensive'].items():
            print(f"\nTesting {asset_name} ({asset_desc}):")
            
            # Test progressively earlier start dates
            test_periods = [
                ('2007-01-01', '2023-12-31'),  # Post-2007 (all ETFs exist)
                ('2000-01-01', '2023-12-31'),  # Post-2000
                ('1990-01-01', '2023-12-31'),  # Post-1990
                ('1986-01-01', '2023-12-31'),  # Study start
            ]
            
            asset_coverage = {}
            for start_date, end_date in test_periods:
                try:
                    # Try total return index first
                    data = blp.bdh(asset_name, 'TOT_RETURN_INDEX_GROSS_DVDS', start_date, end_date)
                    if data is not None and not data.empty:
                        asset_coverage[start_date] = {
                            'status': 'Available (TRI)',
                            'data_points': len(data),
                            'coverage_years': (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365.25,
                            'field': 'TOT_RETURN_INDEX_GROSS_DVDS'
                        }
                        print(f"  ✓ {start_date} to {end_date}: TRI - {len(data)} points")
                    else:
                        # Try price data
                        data = blp.bdh(asset_name, 'PX_LAST', start_date, end_date)
                        if data is not None and not data.empty:
                            asset_coverage[start_date] = {
                                'status': 'Available (Price)',
                                'data_points': len(data),
                                'coverage_years': (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365.25,
                                'field': 'PX_LAST'
                            }
                            print(f"  ✓ {start_date} to {end_date}: Price - {len(data)} points")
                        else:
                            asset_coverage[start_date] = {
                                'status': 'Unavailable',
                                'data_points': 0,
                                'coverage_years': 0,
                                'field': None
                            }
                            print(f"  ✗ {start_date} to {end_date}: No data")
                            
                except Exception as e:
                    asset_coverage[start_date] = {
                        'status': f'Error: {str(e)}',
                        'data_points': 0,
                        'coverage_years': 0,
                        'field': None
                    }
                    print(f"  ✗ {start_date} to {end_date}: Error - {e}")
            
            etf_coverage[asset_name] = asset_coverage
        
        # Test equity fallback and cash proxy
        for asset_type, asset_name in [('equity_fallback', self.required_assets['equity_fallback']), 
                                      ('cash_proxy', self.required_assets['cash_proxy'])]:
            print(f"\nTesting {asset_type} ({asset_name}):")
            
            asset_coverage = {}
            for start_date, end_date in test_periods:
                try:
                    data = blp.bdh(asset_name, 'TOT_RETURN_INDEX_GROSS_DVDS', start_date, end_date)
                    if data is not None and not data.empty:
                        asset_coverage[start_date] = {
                            'status': 'Available (TRI)',
                            'data_points': len(data),
                            'coverage_years': (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365.25,
                            'field': 'TOT_RETURN_INDEX_GROSS_DVDS'
                        }
                        print(f"  ✓ {start_date} to {end_date}: TRI - {len(data)} points")
                    else:
                        data = blp.bdh(asset_name, 'PX_LAST', start_date, end_date)
                        if data is not None and not data.empty:
                            asset_coverage[start_date] = {
                                'status': 'Available (Price)',
                                'data_points': len(data),
                                'coverage_years': (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365.25,
                                'field': 'PX_LAST'
                            }
                            print(f"  ✓ {start_date} to {end_date}: Price - {len(data)} points")
                        else:
                            asset_coverage[start_date] = {
                                'status': 'Unavailable',
                                'data_points': 0,
                                'coverage_years': 0,
                                'field': None
                            }
                            print(f"  ✗ {start_date} to {end_date}: No data")
                except Exception as e:
                    asset_coverage[start_date] = {
                        'status': f'Error: {str(e)}',
                        'data_points': 0,
                        'coverage_years': 0,
                        'field': None
                    }
                    print(f"  ✗ {start_date} to {end_date}: Error - {e}")
            
            etf_coverage[asset_name] = asset_coverage
        
        return etf_coverage
    
    def test_2_proxy_alternatives_availability(self):
        """Test 2: Verify proxy alternatives for pre-ETF periods"""
        if not self.xbbg_available:
            self.skipTest("xbbg not available")
        
        print("\n=== Test 2: Proxy Alternatives Availability ===")
        
        proxy_coverage = {}
        
        for proxy_name, proxy_desc in self.proxy_alternatives.items():
            print(f"\nTesting {proxy_name} ({proxy_desc}):")
            
            # Test proxy availability for study period
            test_periods = [
                ('1986-01-01', '2023-12-31'),  # Full study period
                ('1990-01-01', '2023-12-31'),  # Post-1990
                ('2000-01-01', '2023-12-31'),  # Post-2000
            ]
            
            proxy_data = {}
            for start_date, end_date in test_periods:
                try:
                    # Try different field types for proxies
                    fields_to_try = ['PX_LAST', 'TOT_RETURN_INDEX_GROSS_DVDS', 'PX_SETTLE']
                    
                    for field in fields_to_try:
                        try:
                            data = blp.bdh(proxy_name, field, start_date, end_date)
                            if data is not None and not data.empty:
                                proxy_data[start_date] = {
                                    'status': 'Available',
                                    'data_points': len(data),
                                    'coverage_years': (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365.25,
                                    'field': field
                                }
                                print(f"  ✓ {start_date} to {end_date}: {field} - {len(data)} points")
                                break
                        except:
                            continue
                    else:
                        proxy_data[start_date] = {
                            'status': 'Unavailable',
                            'data_points': 0,
                            'coverage_years': 0,
                            'field': None
                        }
                        print(f"  ✗ {start_date} to {end_date}: No data")
                        
                except Exception as e:
                    proxy_data[start_date] = {
                        'status': f'Error: {str(e)}',
                        'data_points': 0,
                        'coverage_years': 0,
                        'field': None
                    }
                    print(f"  ✗ {start_date} to {end_date}: Error - {e}")
            
            proxy_coverage[proxy_name] = proxy_data
        
        return proxy_coverage
    
    def test_3_hybrid_data_construction_capability(self):
        """Test 3: Test ability to construct hybrid datasets combining ETFs and proxies"""
        if not self.xbbg_available:
            self.skipTest("xbbg not available")
        
        print("\n=== Test 3: Hybrid Data Construction Capability ===")
        
        # Test constructing complete datasets by combining proxies and ETFs
        hybrid_coverage = {}
        
        for asset_name, asset_desc in self.required_assets['defensive'].items():
            print(f"\nTesting hybrid construction for {asset_name} ({asset_desc}):")
            
            # Find corresponding proxy
            proxy_name = None
            for proxy, desc in self.proxy_alternatives.items():
                if asset_name.split()[0] in proxy:  # Simple matching
                    proxy_name = proxy
                    break
            
            if proxy_name:
                print(f"  Using proxy: {proxy_name}")
                
                # Test proxy coverage for early period
                try:
                    proxy_data = blp.bdh(proxy_name, 'PX_LAST', '1986-01-01', '2007-01-01')
                    proxy_available = proxy_data is not None and not proxy_data.empty
                    print(f"  Proxy 1986-2007: {'✓ Available' if proxy_available else '✗ Unavailable'}")
                except:
                    proxy_available = False
                    print(f"  Proxy 1986-2007: ✗ Error")
                
                # Test ETF coverage for later period
                try:
                    etf_data = blp.bdh(asset_name, 'TOT_RETURN_INDEX_GROSS_DVDS', '2007-01-01', '2023-12-31')
                    etf_available = etf_data is not None and not etf_data.empty
                    print(f"  ETF 2007-2023: {'✓ Available' if etf_available else '✗ Unavailable'}")
                except:
                    etf_available = False
                    print(f"  ETF 2007-2023: ✗ Error")
                
                # Overall hybrid availability
                if proxy_available and etf_available:
                    hybrid_coverage[asset_name] = {
                        'status': 'Full Coverage Available',
                        'proxy_period': '1986-2007',
                        'etf_period': '2007-2023',
                        'total_coverage': '39 years (100%)'
                    }
                    print(f"  ✓ Full coverage: 1986-2023 (39 years)")
                elif etf_available:
                    hybrid_coverage[asset_name] = {
                        'status': 'Partial Coverage (ETF Only)',
                        'proxy_period': 'None',
                        'etf_period': '2007-2023',
                        'total_coverage': '16 years (41%)'
                    }
                    print(f"  ⚠️  Partial coverage: 2007-2023 (16 years)")
                else:
                    hybrid_coverage[asset_name] = {
                        'status': 'No Coverage',
                        'proxy_period': 'None',
                        'etf_period': 'None',
                        'total_coverage': '0 years (0%)'
                    }
                    print(f"  ✗ No coverage available")
            else:
                print(f"  No proxy found for {asset_name}")
                hybrid_coverage[asset_name] = {
                    'status': 'No Proxy Available',
                    'proxy_period': 'None',
                    'etf_period': 'Unknown',
                    'total_coverage': 'Unknown'
                }
        
        return hybrid_coverage
    
    def test_4_data_quality_comparison(self):
        """Test 4: Compare data quality between ETFs and proxies"""
        if not self.xbbg_available:
            self.skipTest("xbbg not available")
        
        print("\n=== Test 4: Data Quality Comparison ===")
        
        quality_comparison = {}
        
        # Test period for quality comparison
        test_period = ('2007-01-01', '2023-12-31')  # Period where both ETFs and proxies exist
        
        for asset_name, asset_desc in self.required_assets['defensive'].items():
            print(f"\nQuality comparison for {asset_name} ({asset_desc}):")
            
            # Find corresponding proxy
            proxy_name = None
            for proxy, desc in self.proxy_alternatives.items():
                if asset_name.split()[0] in proxy:
                    proxy_name = proxy
                    break
            
            if proxy_name:
                try:
                    # Get ETF data
                    etf_data = blp.bdh(asset_name, 'TOT_RETURN_INDEX_GROSS_DVDS', test_period[0], test_period[1])
                    
                    # Get proxy data
                    proxy_data = blp.bdh(proxy_name, 'PX_LAST', test_period[0], test_period[1])
                    
                    if etf_data is not None and not etf_data.empty and proxy_data is not None and not proxy_data.empty:
                        # Compare data quality
                        etf_points = len(etf_data)
                        proxy_points = len(proxy_data)
                        
                        # Check for missing values
                        etf_missing = etf_data.isnull().sum().sum()
                        proxy_missing = proxy_data.isnull().sum().sum()
                        
                        # Check data consistency
                        etf_consistency = (etf_points - etf_missing) / etf_points * 100
                        proxy_consistency = (proxy_points - proxy_missing) / proxy_points * 100
                        
                        quality_comparison[asset_name] = {
                            'etf_data_points': etf_points,
                            'proxy_data_points': proxy_points,
                            'etf_missing': etf_missing,
                            'proxy_missing': proxy_missing,
                            'etf_consistency': etf_consistency,
                            'proxy_consistency': proxy_consistency,
                            'recommendation': 'ETF' if etf_consistency > proxy_consistency else 'Proxy'
                        }
                        
                        print(f"  ETF: {etf_points} points, {etf_missing} missing ({etf_consistency:.1f}% consistent)")
                        print(f"  Proxy: {proxy_points} points, {proxy_missing} missing ({proxy_consistency:.1f}% consistent)")
                        print(f"  Recommendation: {quality_comparison[asset_name]['recommendation']}")
                        
                    else:
                        print(f"  ✗ Insufficient data for comparison")
                        quality_comparison[asset_name] = {'status': 'Insufficient Data'}
                        
                except Exception as e:
                    print(f"  ✗ Quality comparison error: {e}")
                    quality_comparison[asset_name] = {'status': f'Error: {e}'}
            else:
                print(f"  No proxy available for comparison")
                quality_comparison[asset_name] = {'status': 'No Proxy Available'}
        
        return quality_comparison
    
    def test_5_study_period_replication_assessment(self):
        """Test 5: Final assessment of study period replication capability"""
        if not self.xbbg_available:
            self.skipTest("xbbg not available")
        
        print("\n=== Test 5: Study Period Replication Assessment ===")
        
        # Run all previous tests to get comprehensive assessment
        print("Running comprehensive data mimicry assessment...")
        
        results = {
            'etf_coverage': self.test_1_etf_data_availability_periods(),
            'proxy_coverage': self.test_2_proxy_alternatives_availability(),
            'hybrid_capability': self.test_3_hybrid_data_construction_capability(),
            'data_quality': self.test_4_data_quality_comparison()
        }
        
        # Calculate overall replication capability
        print(f"\n=== OVERALL STUDY PERIOD REPLICATION ASSESSMENT ===")
        
        # Analyze coverage for each asset
        total_required_years = 39  # 1986-2025
        replication_summary = {}
        
        for asset_name in self.required_assets['defensive'].keys():
            print(f"\n{asset_name}:")
            
            # Check ETF coverage
            etf_status = results['etf_coverage'].get(asset_name, {})
            etf_coverage = 0
            if etf_status:
                for period, data in etf_status.items():
                    if data['coverage_years'] > etf_coverage:
                        etf_coverage = data['coverage_years']
            
            # Check hybrid capability
            hybrid_status = results['hybrid_capability'].get(asset_name, {})
            hybrid_coverage = 0
            if hybrid_status.get('status') == 'Full Coverage Available':
                hybrid_coverage = 39  # Full study period
            
            # Best available coverage
            best_coverage = max(etf_coverage, hybrid_coverage)
            coverage_percentage = (best_coverage / total_required_years) * 100
            
            replication_summary[asset_name] = {
                'etf_coverage_years': etf_coverage,
                'hybrid_coverage_years': hybrid_coverage,
                'best_coverage_years': best_coverage,
                'coverage_percentage': coverage_percentage,
                'can_replicate_study': coverage_percentage >= 80
            }
            
            status = "✓" if coverage_percentage >= 80 else "✗"
            print(f"  {status} Coverage: {coverage_percentage:.1f}% ({best_coverage:.1f} years)")
            
            if hybrid_coverage > etf_coverage:
                print(f"  → Hybrid approach provides full coverage")
            elif etf_coverage > 0:
                print(f"  → ETF-only approach: {etf_coverage:.1f} years")
            else:
                print(f"  → No coverage available")
        
        # Overall assessment
        total_coverage = sum(item['best_coverage_years'] for item in replication_summary.values())
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
        
        return {
            'overall_coverage_percentage': overall_coverage_percentage,
            'total_coverage_years': total_coverage,
            'max_possible_coverage': max_possible_coverage,
            'replication_level': replication_level,
            'detailed_results': results,
            'replication_summary': replication_summary
        }

def run_comprehensive_mimicry_test():
    """Run comprehensive data mimicry test"""
    print("=" * 80)
    print("DEFENSE FIRST STRATEGY - COMPREHENSIVE DATA MIMICRY TEST")
    print("=" * 80)
    print("Testing exactly what data we can replicate from the academic study")
    print("=" * 80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()
    
    # Add all tests
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestDefenseFirstDataMimicry))
    
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
    test_results = run_comprehensive_mimicry_test()
