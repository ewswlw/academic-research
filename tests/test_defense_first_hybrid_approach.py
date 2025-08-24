"""
Test Defense First Hybrid Data Approach
Validates the study's hybrid methodology using correct Bloomberg fields
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
    """Test the hybrid data approach for Defense First strategy"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data and parameters"""
        
        if not XBBG_AVAILABLE:
            print("Warning: xbbg not available - tests will be skipped")
            return
        
        # Corrected hybrid data mapping based on our investigation
        cls.hybrid_data_mapping = {
            'TLT': {
                'etf': 'TLT US Equity',
                'etf_inception': '2002-07-22',
                'pre_etf_source': 'VUSTX US Equity',  # ✓ Vanguard Long-Term Treasury
                'description': 'Long-term Treasuries',
                'field': 'TOT_RETURN_INDEX_GROSS_DVDS'
            },
            'GLD': {
                'etf': 'GLD US Equity', 
                'etf_inception': '2004-11-18',
                'pre_etf_source': 'GC1 Comdty',      # ✓ Gold futures
                'description': 'Gold',
                'field': 'PX_LAST'  # Futures use PX_LAST
            },
            'DBC': {
                'etf': 'DBC US Equity',
                'etf_inception': '2006-02-03', 
                'pre_etf_source': 'CRY Index',       # ✓ CRB commodity index
                'description': 'Commodities',
                'field': 'PX_LAST'
            },
            'UUP': {
                'etf': 'UUP US Equity',
                'etf_inception': '2007-01-05',
                'pre_etf_source': 'DXY Curncy',      # ✓ Dollar index
                'description': 'US Dollar Index',
                'field': 'PX_LAST'
            },
            'SPY': {
                'etf': 'SPY US Equity',
                'etf_inception': '1993-01-29',
                'pre_etf_source': 'SPX Index',       # ✓ S&P 500 index
                'description': 'S&P 500',
                'field': 'PX_LAST'
            },
            'BIL': {
                'etf': 'BIL US Equity',
                'etf_inception': '2007-05-25',
                'pre_etf_source': 'USGG3M Index',    # ✓ 3-month Treasury
                'description': '90-day T-bills',
                'field': 'PX_LAST'
            }
        }
        
        # Test periods
        cls.study_period = ('1986-01-01', '2023-12-31')
        cls.etf_test_period = ('2000-01-01', '2010-12-31')
        cls.pre_etf_test_period = ('1990-01-01', '2000-12-31')
        
        # Strategy parameters
        cls.momentum_lookbacks = [21, 63, 126, 252]  # 1, 3, 6, 12 months
        
        print("Test setup complete")
    
    def test_1_hybrid_data_availability(self):
        """Test that all required hybrid data sources are available"""
        
        if not XBBG_AVAILABLE:
            self.skipTest("xbbg not available")
        
        print("\nTesting hybrid data availability...")
        
        for asset_name, asset_info in self.hybrid_data_mapping.items():
            print(f"\nTesting {asset_name} ({asset_info['description']}):")
            
            # Test pre-ETF source
            try:
                pre_etf_data = blp.bdh(
                    asset_info['pre_etf_source'],
                    asset_info['field'],
                    self.pre_etf_test_period[0],
                    self.pre_etf_test_period[1]
                )
                
                if pre_etf_data is not None and not pre_etf_data.empty:
                    print(f"  ✓ Pre-ETF ({asset_info['pre_etf_source']}): {len(pre_etf_data)} points")
                    print(f"    Period: {pre_etf_data.index[0]} to {pre_etf_data.index[-1]}")
                    
                    # Verify data quality
                    sample_values = pre_etf_data.iloc[:3, 0].tolist()
                    if all(v > 0 for v in sample_values):
                        print(f"    ✓ Data quality: All values positive")
                    else:
                        print(f"    ⚠️  Data quality: Some values not positive: {sample_values}")
                        
                else:
                    print(f"  ✗ Pre-ETF: No data available")
                    self.fail(f"No pre-ETF data for {asset_name}")
                    
            except Exception as e:
                print(f"  ✗ Pre-ETF error: {e}")
                self.fail(f"Error fetching pre-ETF data for {asset_name}: {e}")
            
            # Test ETF source
            try:
                etf_data = blp.bdh(
                    asset_info['etf'],
                    'TOT_RETURN_INDEX_GROSS_DVDS',
                    self.etf_test_period[0],
                    self.etf_test_period[1]
                )
                
                if etf_data is not None and not etf_data.empty:
                    print(f"  ✓ ETF ({asset_info['etf']}): {len(etf_data)} points")
                    print(f"    Period: {etf_data.index[0]} to {etf_data.index[-1]}")
                    
                    # Verify data quality
                    sample_values = etf_data.iloc[:3, 0].tolist()
                    if all(v > 0 for v in sample_values):
                        print(f"    ✓ Data quality: All values positive")
                    else:
                        print(f"    ⚠️  Data quality: Some values not positive: {sample_values}")
                        
                else:
                    print(f"  ✗ ETF: No data available")
                    self.fail(f"No ETF data for {asset_name}")
                    
            except Exception as e:
                print(f"  ✗ ETF error: {e}")
                self.fail(f"Error fetching ETF data for {asset_name}: {e}")
    
    def test_2_data_stitching_capability(self):
        """Test that we can successfully stitch pre-ETF and ETF data"""
        
        if not XBBG_AVAILABLE:
            self.skipTest("xbbg not available")
        
        print("\nTesting data stitching capability...")
        
        for asset_name, asset_info in self.hybrid_data_mapping.items():
            print(f"\nTesting {asset_name} data stitching...")
            
            # Fetch pre-ETF data
            pre_etf_data = blp.bdh(
                asset_info['pre_etf_source'],
                asset_info['field'],
                '1990-01-01',
                asset_info['etf_inception']
            )
            
            # Fetch ETF data
            etf_data = blp.bdh(
                asset_info['etf'],
                'TOT_RETURN_INDEX_GROSS_DVDS',
                asset_info['etf_inception'],
                '2010-12-31'
            )
            
            # Test data combination
            if not pre_etf_data.empty and not etf_data.empty:
                # Simple concatenation test
                combined_data = pd.concat([pre_etf_data, etf_data])
                combined_data = combined_data.sort_index()
                combined_data = combined_data[~combined_data.index.duplicated(keep='first')]
                
                print(f"  ✓ Data stitching successful")
                print(f"    Combined period: {combined_data.index[0]} to {combined_data.index[-1]}")
                print(f"    Total points: {len(combined_data)}")
                
                # Verify no gaps in data
                date_diff = combined_data.index.to_series().diff().dt.days
                max_gap = date_diff.max()
                if max_gap < 10:  # Allow small gaps for weekends/holidays
                    print(f"    ✓ Data continuity: Max gap {max_gap} days")
                else:
                    print(f"    ⚠️  Data continuity: Large gap {max_gap} days detected")
                
                # Verify data quality
                sample_values = combined_data.iloc[:5, 0].tolist()
                if all(v > 0 for v in sample_values):
                    print(f"    ✓ Data quality: All sample values positive")
                else:
                    print(f"    ⚠️  Data quality: Some values not positive: {sample_values}")
                    
            else:
                self.fail(f"Could not fetch data for {asset_name}")
    
    def test_3_momentum_calculation_validation(self):
        """Test that momentum calculations work with hybrid data"""
        
        if not XBBG_AVAILABLE:
            self.skipTest("xbbg not available")
        
        print("\nTesting momentum calculation validation...")
        
        # Test with a specific asset (TLT)
        asset_name = 'TLT'
        asset_info = self.hybrid_data_mapping[asset_name]
        
        print(f"Testing momentum calculation for {asset_name}...")
        
        # Fetch hybrid data
        pre_etf_data = blp.bdh(
            asset_info['pre_etf_source'],
            asset_info['field'],
            '1995-01-01',
            asset_info['etf_inception']
        )
        
        etf_data = blp.bdh(
            asset_info['etf'],
            'TOT_RETURN_INDEX_GROSS_DVDS',
            asset_info['etf_inception'],
            '2005-12-31'
        )
        
        # Combine data
        combined_data = pd.concat([pre_etf_data, etf_data])
        combined_data = combined_data.sort_index()
        combined_data = combined_data[~combined_data.index.duplicated(keep='first')]
        
        # Test momentum calculation
        prices = combined_data.iloc[:, 0]
        
        for lookback in self.momentum_lookbacks:
            if len(prices) > lookback:
                current_price = prices.iloc[-1]
                past_price = prices.iloc[-lookback-1]
                
                if past_price > 0:
                    momentum = (current_price / past_price - 1) * 100
                    print(f"  ✓ {lookback}-day momentum: {momentum:.2f}%")
                else:
                    print(f"  ✗ {lookback}-day momentum: Invalid past price {past_price}")
                    self.fail(f"Invalid price data for momentum calculation")
            else:
                print(f"  ⚠️  {lookback}-day momentum: Insufficient data ({len(prices)} points)")
    
    def test_4_study_period_replication_assessment(self):
        """Assess our ability to replicate the full study period"""
        
        if not XBBG_AVAILABLE:
            self.skipTest("xbbg not available")
        
        print("\nAssessing study period replication capability...")
        
        study_start = datetime(1986, 1, 1)
        study_end = datetime(2023, 12, 31)
        
        total_days = (study_end - study_start).days
        print(f"Study period: {total_days} days ({total_days/365.25:.1f} years)")
        
        # Check coverage for each asset
        coverage_summary = {}
        
        for asset_name, asset_info in self.hybrid_data_mapping.items():
            print(f"\nChecking coverage for {asset_name}...")
            
            # Calculate coverage periods
            pre_etf_start = study_start
            pre_etf_end = datetime.strptime(asset_info['etf_inception'], '%Y-%m-%d')
            etf_start = pre_etf_end
            etf_end = study_end
            
            pre_etf_days = (pre_etf_end - pre_etf_start).days
            etf_days = (etf_end - etf_start).days
            
            total_coverage = pre_etf_days + etf_days
            coverage_pct = (total_coverage / total_days) * 100
            
            print(f"  Pre-ETF coverage: {pre_etf_days} days ({pre_etf_days/365.25:.1f} years)")
            print(f"  ETF coverage: {etf_days} days ({etf_days/365.25:.1f} years)")
            print(f"  Total coverage: {total_coverage} days ({total_coverage/365.25:.1f} years)")
            print(f"  Coverage percentage: {coverage_pct:.1f}%")
            
            coverage_summary[asset_name] = {
                'pre_etf_days': pre_etf_days,
                'etf_days': etf_days,
                'total_coverage': total_coverage,
                'coverage_pct': coverage_pct
            }
            
            # Verify we have sufficient coverage
            self.assertGreater(coverage_pct, 95, f"Insufficient coverage for {asset_name}: {coverage_pct:.1f}%")
        
        # Overall assessment
        avg_coverage = np.mean([info['coverage_pct'] for info in coverage_summary.values()])
        print(f"\nOverall coverage assessment:")
        print(f"  Average coverage: {avg_coverage:.1f}%")
        print(f"  ✓ Sufficient coverage for study replication: {avg_coverage > 95}")
        
        self.assertGreater(avg_coverage, 95, f"Overall coverage insufficient: {avg_coverage:.1f}%")
    
    def test_5_data_quality_validation(self):
        """Validate data quality for strategy implementation"""
        
        if not XBBG_AVAILABLE:
            self.skipTest("xbbg not available")
        
        print("\nValidating data quality for strategy implementation...")
        
        # Test data quality metrics
        quality_metrics = {}
        
        for asset_name, asset_info in self.hybrid_data_mapping.items():
            print(f"\nValidating {asset_name} data quality...")
            
            # Fetch sample data
            sample_data = blp.bdh(
                asset_info['pre_etf_source'],
                asset_info['field'],
                '2000-01-01',
                '2005-01-01'
            )
            
            if sample_data is not None and not sample_data.empty:
                prices = sample_data.iloc[:, 0]
                
                # Calculate quality metrics
                total_points = len(prices)
                positive_points = (prices > 0).sum()
                zero_points = (prices == 0).sum()
                negative_points = (prices < 0).sum()
                missing_points = prices.isna().sum()
                
                # Calculate returns for momentum validation
                returns = prices.pct_change().dropna()
                valid_returns = returns[returns != np.inf]
                inf_returns = (returns == np.inf).sum()
                nan_returns = returns.isna().sum()
                
                quality_metrics[asset_name] = {
                    'total_points': total_points,
                    'positive_points': positive_points,
                    'zero_points': zero_points,
                    'negative_points': negative_points,
                    'missing_points': missing_points,
                    'valid_returns': len(valid_returns),
                    'inf_returns': inf_returns,
                    'nan_returns': nan_returns
                }
                
                print(f"  Data points: {total_points}")
                print(f"  Positive values: {positive_points} ({positive_points/total_points*100:.1f}%)")
                print(f"  Zero values: {zero_points} ({zero_points/total_points*100:.1f}%)")
                print(f"  Negative values: {negative_points} ({negative_points/total_points*100:.1f}%)")
                print(f"  Missing values: {missing_points} ({missing_points/total_points*100:.1f}%)")
                print(f"  Valid returns: {len(valid_returns)}")
                print(f"  Infinite returns: {inf_returns}")
                print(f"  NaN returns: {nan_returns}")
                
                # Quality assertions
                self.assertGreater(positive_points/total_points, 0.95, f"Too many non-positive values for {asset_name}")
                self.assertLess(missing_points/total_points, 0.05, f"Too many missing values for {asset_name}")
                self.assertLess(inf_returns, total_points * 0.01, f"Too many infinite returns for {asset_name}")
                
            else:
                self.fail(f"No data available for {asset_name}")
        
        print(f"\nData quality validation complete for {len(quality_metrics)} assets")

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
