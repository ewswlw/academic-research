"""
Investigate ETF Data Sources
Determines what Bloomberg is actually providing for pre-ETF periods
"""

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

def investigate_etf_data_sources():
    """Investigate what data sources Bloomberg uses for pre-ETF periods"""
    
    if not XBBG_AVAILABLE:
        print("xbbg not available")
        return
    
    print("=" * 80)
    print("INVESTIGATING ETF DATA SOURCES")
    print("=" * 80)
    print("Determining what Bloomberg actually provides for pre-ETF periods")
    print("=" * 80)
    
    # ETFs to investigate with their actual inception dates
    etfs_to_investigate = {
        'TLT US Equity': {
            'inception': '2002-07-22',
            'description': 'iShares 20+ Year Treasury Bond ETF',
            'underlying': 'USGG10YR Index (10Y Treasury)'
        },
        'GLD US Equity': {
            'inception': '2004-11-18', 
            'description': 'SPDR Gold Shares ETF',
            'underlying': 'GC1 Comdty (Gold Futures)'
        },
        'DBC US Equity': {
            'inception': '2006-02-03',
            'description': 'Invesco DB Commodity Index ETF',
            'underlying': 'CRY Index (Commodity Index)'
        },
        'UUP US Equity': {
            'inception': '2007-01-05',
            'description': 'Invesco DB US Dollar Index Bullish Fund',
            'underlying': 'DXY Curncy (Dollar Index)'
        },
        'SPY US Equity': {
            'inception': '1993-01-29',
            'description': 'SPDR S&P 500 ETF Trust',
            'underlying': 'SPX Index (S&P 500)'
        },
        'BIL US Equity': {
            'inception': '2007-05-25',
            'description': 'SPDR Bloomberg 1-3 Month T-Bill ETF',
            'underlying': 'USGG3M Index (3M Treasury)'
        }
    }
    
    print("\nETF Inception Dates vs Bloomberg Data Availability:")
    print("-" * 80)
    
    for etf_name, etf_info in etfs_to_investigate.items():
        print(f"\n{etf_name}:")
        print(f"  Inception Date: {etf_info['inception']}")
        print(f"  Description: {etf_info['description']}")
        print(f"  Underlying Index: {etf_info['underlying']}")
        
        # Test data availability before ETF inception
        pre_inception_start = '1986-01-01'
        pre_inception_end = etf_info['inception']
        
        print(f"  Testing pre-inception period: {pre_inception_start} to {pre_inception_end}")
        
        try:
            # Test total return index
            tri_data = blp.bdh(etf_name, 'TOT_RETURN_INDEX_GROSS_DVDS', pre_inception_start, pre_inception_end)
            if tri_data is not None and not tri_data.empty:
                print(f"    ✓ TRI Available: {len(tri_data)} data points")
                print(f"      First date: {tri_data.index[0]}")
                print(f"      Last date: {tri_data.index[-1]}")
                
                # Check if data is backfilled (all same value or pattern)
                unique_values = tri_data.iloc[:, 0].nunique()
                if unique_values == 1:
                    print(f"      ⚠️  WARNING: All values identical - likely backfilled")
                elif unique_values < 10:
                    print(f"      ⚠️  WARNING: Only {unique_values} unique values - suspicious")
                else:
                    print(f"      ✓ Data appears genuine with {unique_values} unique values")
                
                # Check for data source field
                try:
                    source_data = blp.bdh(etf_name, 'DATA_SOURCE', pre_inception_start, pre_inception_end)
                    if source_data is not None and not source_data.empty:
                        print(f"      Data Source: {source_data.iloc[0, 0] if len(source_data) > 0 else 'Unknown'}")
                    else:
                        print(f"      Data Source: Not available")
                except:
                    print(f"      Data Source: Field not available")
                    
            else:
                print(f"    ✗ TRI Not available")
                
        except Exception as e:
            print(f"    ✗ TRI Error: {e}")
        
        # Test price data
        try:
            price_data = blp.bdh(etf_name, 'PX_LAST', pre_inception_start, pre_inception_end)
            if price_data is not None and not price_data.empty:
                print(f"    ✓ Price Available: {len(price_data)} data points")
                print(f"      First date: {price_data.index[0]}")
                print(f"      Last date: {price_data.index[-1]}")
                
                # Check if data is backfilled
                unique_values = price_data.iloc[:, 0].nunique()
                if unique_values == 1:
                    print(f"      ⚠️  WARNING: All values identical - likely backfilled")
                elif unique_values < 10:
                    print(f"      ⚠️  WARNING: Only {unique_values} unique values - suspicious")
                else:
                    print(f"      ✓ Data appears genuine with {unique_values} unique values")
                    
            else:
                print(f"    ✗ Price Not available")
                
        except Exception as e:
            print(f"    ✗ Price Error: {e}")
        
        # Test underlying index availability
        underlying_index = etf_info['underlying'].split()[0]  # Extract first part
        print(f"  Testing underlying index: {underlying_index}")
        
        try:
            underlying_data = blp.bdh(underlying_index, 'PX_LAST', pre_inception_start, pre_inception_end)
            if underlying_data is not None and not underlying_data.empty:
                print(f"    ✓ Underlying Available: {len(underlying_data)} data points")
                print(f"      First date: {underlying_data.index[0]}")
                print(f"      Last date: {underlying_data.index[-1]}")
                
                # Compare with ETF data
                if 'tri_data' in locals() and tri_data is not None and not tri_data.empty:
                    if len(underlying_data) == len(tri_data):
                        print(f"      ✓ Same number of data points as ETF")
                    else:
                        print(f"      ⚠️  Different data points: ETF={len(tri_data)}, Underlying={len(underlying_data)}")
                        
            else:
                print(f"    ✗ Underlying Not available")
                
        except Exception as e:
            print(f"    ✗ Underlying Error: {e}")
        
        print("-" * 80)
    
    # Test specific fields that might indicate data source
    print("\n" + "=" * 80)
    print("TESTING DATA SOURCE INDICATORS")
    print("=" * 80)
    
    test_etf = 'TLT US Equity'
    test_period = ('1986-01-01', '1990-01-01')
    
    print(f"Testing data source indicators for {test_etf} in {test_period[0]} to {test_period[1]}")
    
    # Fields that might indicate data source
    source_fields = [
        'DATA_SOURCE',
        'DATA_SRC',
        'SOURCE',
        'ORIG_SOURCE',
        'BACKFILL_SOURCE',
        'INDEX_SOURCE',
        'UNDERLYING_SOURCE'
    ]
    
    for field in source_fields:
        try:
            data = blp.bdh(test_etf, field, test_period[0], test_period[1])
            if data is not None and not data.empty:
                print(f"✓ {field}: {data.iloc[0, 0] if len(data) > 0 else 'Available'}")
            else:
                print(f"✗ {field}: Not available")
        except:
            print(f"✗ {field}: Field not available")
    
    # Test if we can get the actual underlying index data
    print(f"\nTesting actual underlying index data availability:")
    
    underlying_indices = [
        'USGG10YR Index',  # TLT underlying
        'GC1 Comdty',      # GLD underlying  
        'CRY Index',       # DBC underlying
        'DXY Curncy',      # UUP underlying
        'SPX Index',       # SPY underlying
        'USGG3M Index'     # BIL underlying
    ]
    
    for index in underlying_indices:
        try:
            data = blp.bdh(index, 'PX_LAST', test_period[0], test_period[1])
            if data is not None and not data.empty:
                print(f"✓ {index}: {len(data)} data points")
            else:
                print(f"✗ {index}: No data")
        except Exception as e:
            print(f"✗ {index}: Error - {e}")

def test_data_consistency():
    """Test if pre-ETF data is consistent with post-ETF data"""
    
    if not XBBG_AVAILABLE:
        print("xbbg not available")
        return
    
    print("\n" + "=" * 80)
    print("TESTING DATA CONSISTENCY")
    print("=" * 80)
    
    test_etf = 'TLT US Equity'
    
    # Test periods
    periods = {
        'pre_etf': ('1986-01-01', '2002-01-01'),      # Before TLT inception
        'etf_early': ('2002-07-22', '2005-01-01'),    # Early ETF period
        'etf_recent': ('2020-01-01', '2023-12-31')    # Recent ETF period
    }
    
    print(f"Testing data consistency for {test_etf}:")
    
    for period_name, (start, end) in periods.items():
        print(f"\n{period_name.upper()} ({start} to {end}):")
        
        try:
            # Get data
            data = blp.bdh(test_etf, 'TOT_RETURN_INDEX_GROSS_DVDS', start, end)
            
            if data is not None and not data.empty:
                print(f"  ✓ Data available: {len(data)} points")
                print(f"    First date: {data.index[0]}")
                print(f"    Last date: {data.index[-1]}")
                
                # Calculate basic statistics
                values = data.iloc[:, 0]
                print(f"    Min: {values.min():.2f}")
                print(f"    Max: {values.max():.2f}")
                print(f"    Mean: {values.mean():.2f}")
                print(f"    Std: {values.std():.2f}")
                
                # Check for missing values
                missing = values.isnull().sum()
                print(f"    Missing values: {missing}")
                
                # Check for zero/negative values
                zero_neg = (values <= 0).sum()
                print(f"    Zero/negative values: {zero_neg}")
                
            else:
                print(f"  ✗ No data available")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")

if __name__ == "__main__":
    print("Starting ETF Data Source Investigation...")
    print("This will determine what Bloomberg actually provides for pre-ETF periods")
    print()
    
    # Run investigation
    investigate_etf_data_sources()
    
    # Test data consistency
    test_data_consistency()
    
    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)
    print("Check the output above for data source analysis.")
