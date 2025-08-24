"""
Investigate Correct Bloomberg Fields for Defense First Study
Finds the exact fields needed to replicate the study's methodology
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

def investigate_treasury_bond_fields():
    """Investigate correct Bloomberg fields for Treasury bonds"""
    
    if not XBBG_AVAILABLE:
        print("xbbg not available")
        return
    
    print("=" * 80)
    print("INVESTIGATING TREASURY BOND FIELDS")
    print("=" * 80)
    
    # Test different Bloomberg fields for Treasury bonds
    test_fields = [
        'PX_LAST',                    # Last price
        'TOT_RETURN_INDEX_GROSS_DVDS', # Total return index
        'PX_SETTLE',                  # Settlement price
        'PX_BID',                     # Bid price
        'PX_ASK',                     # Ask price
        'PX_OPEN',                    # Open price
        'PX_HIGH',                    # High price
        'PX_LOW',                     # Low price
        'YLD_YTM_MID',               # Yield to maturity
        'YLD_CUR_MID',               # Current yield
        'DUR_MID',                    # Duration
        'MOD_DUR_MID',               # Modified duration
    ]
    
    # Test different Treasury instruments
    treasury_instruments = [
        'USGG10YR Index',            # 10Y Treasury yield
        'USGG30YR Index',            # 30Y Treasury yield
        'USGG5YR Index',             # 5Y Treasury yield
        'UST Index',                  # Treasury bond index
        'UST10 Index',               # 10Y Treasury index
        'UST30 Index',               # 30Y Treasury index
        'USGG10YR Curncy',           # 10Y Treasury currency
        'USGG10YR Govt',             # 10Y Treasury government
    ]
    
    test_period = ('2000-01-01', '2005-01-01')
    
    print(f"Testing Treasury fields for period: {test_period[0]} to {test_period[1]}")
    print()
    
    for instrument in treasury_instruments:
        print(f"Testing {instrument}:")
        
        available_fields = []
        for field in test_fields:
            try:
                data = blp.bdh(instrument, field, test_period[0], test_period[1])
                if data is not None and not data.empty:
                    available_fields.append(field)
                    print(f"  ✓ {field}: {len(data)} points")
                    
                    # Show sample values for key fields
                    if field in ['PX_LAST', 'TOT_RETURN_INDEX_GROSS_DVDS', 'YLD_YTM_MID']:
                        sample_values = data.iloc[:3, 0].tolist()
                        print(f"    Sample values: {sample_values}")
                        
                else:
                    print(f"  ✗ {field}: No data")
            except Exception as e:
                print(f"  ✗ {field}: Error - {e}")
        
        print(f"  Available fields: {len(available_fields)}/{len(test_fields)}")
        print("-" * 60)

def investigate_alternative_treasury_sources():
    """Investigate alternative Treasury data sources"""
    
    if not XBBG_AVAILABLE:
        print("xbbg not available")
        return
    
    print("\n" + "=" * 80)
    print("INVESTIGATING ALTERNATIVE TREASURY SOURCES")
    print("=" * 80)
    
    # Test Vanguard Treasury mutual funds
    vanguard_funds = [
        'VFITX US Equity',           # Vanguard Intermediate-Term Treasury
        'VUSTX US Equity',           # Vanguard Long-Term Treasury
        'VFISX US Equity',           # Vanguard Short-Term Treasury
        'VUSTX Index',               # Vanguard Long-Term Treasury Index
    ]
    
    # Test Treasury bond ETFs
    treasury_etfs = [
        'IEF US Equity',             # iShares 7-10 Year Treasury
        'TLT US Equity',             # iShares 20+ Year Treasury
        'SHY US Equity',             # iShares 1-3 Year Treasury
        'SHV US Equity',             # iShares Short Treasury
    ]
    
    # Test Treasury bond indices
    treasury_indices = [
        'UST Index',                 # Treasury bond index
        'UST10 Index',               # 10Y Treasury index
        'UST30 Index',               # 30Y Treasury index
        'UST5 Index',                # 5Y Treasury index
        'UST2 Index',                # 2Y Treasury index
    ]
    
    test_period = ('1990-01-01', '2000-01-01')
    
    print(f"Testing alternative sources for period: {test_period[0]} to {test_period[1]}")
    print()
    
    # Test Vanguard funds
    print("Vanguard Treasury Funds:")
    for fund in vanguard_funds:
        try:
            data = blp.bdh(fund, 'TOT_RETURN_INDEX_GROSS_DVDS', test_period[0], test_period[1])
            if data is not None and not data.empty:
                print(f"  ✓ {fund}: {len(data)} points")
                print(f"    Period: {data.index[0]} to {data.index[-1]}")
            else:
                print(f"  ✗ {fund}: No data")
        except Exception as e:
            print(f"  ✗ {fund}: Error - {e}")
    
    print()
    
    # Test Treasury indices
    print("Treasury Bond Indices:")
    for index in treasury_indices:
        try:
            data = blp.bdh(index, 'PX_LAST', test_period[0], test_period[1])
            if data is not None and not data.empty:
                print(f"  ✓ {index}: {len(data)} points")
                print(f"    Period: {data.index[0]} to {data.index[-1]}")
                
                # Check if it's price data (not yield)
                sample_values = data.iloc[:3, 0].tolist()
                if all(v > 0 for v in sample_values):
                    print(f"    ✓ Appears to be price data (values > 0)")
                else:
                    print(f"    ⚠️  Values not all positive: {sample_values}")
                    
            else:
                print(f"  ✗ {index}: No data")
        except Exception as e:
            print(f"  ✗ {index}: Error - {e}")

def test_yield_to_price_conversion():
    """Test if we can convert yields to prices for Treasury bonds"""
    
    if not XBBG_AVAILABLE:
        print("xbbg not available")
        return
    
    print("\n" + "=" * 80)
    print("TESTING YIELD TO PRICE CONVERSION")
    print("=" * 80)
    
    # Test period
    test_period = ('2000-01-01', '2005-01-01')
    
    print(f"Testing yield to price conversion for period: {test_period[0]} to {test_period[1]}")
    print()
    
    # Get yield data
    try:
        yield_data = blp.bdh('USGG10YR Index', 'YLD_YTM_MID', test_period[0], test_period[1])
        
        if yield_data is not None and not yield_data.empty:
            print(f"✓ Yield data available: {len(yield_data)} points")
            print(f"  Sample yields: {yield_data.iloc[:5, 0].tolist()}")
            
            # Test if we can get duration data for conversion
            try:
                duration_data = blp.bdh('USGG10YR Index', 'DUR_MID', test_period[0], test_period[1])
                if duration_data is not None and not duration_data.empty:
                    print(f"✓ Duration data available: {len(duration_data)} points")
                    print(f"  Sample durations: {duration_data.iloc[:5, 0].tolist()}")
                    
                    # Test yield to price conversion
                    print(f"\nTesting yield to price conversion:")
                    
                    # Simple example: if yield changes by 1%, price changes by -duration * 1%
                    sample_yield_change = yield_data.iloc[1, 0] - yield_data.iloc[0, 0]
                    sample_duration = duration_data.iloc[0, 0]
                    
                    if sample_duration > 0:
                        estimated_price_change = -sample_duration * sample_yield_change
                        print(f"  Yield change: {sample_yield_change:.3f}%")
                        print(f"  Duration: {sample_duration:.2f}")
                        print(f"  Estimated price change: {estimated_price_change:.3f}%")
                        print(f"  ✓ Conversion appears possible")
                    else:
                        print(f"  ✗ Duration data invalid")
                        
                else:
                    print(f"✗ Duration data not available")
                    
            except Exception as e:
                print(f"✗ Error getting duration: {e}")
                
        else:
            print(f"✗ Yield data not available")
            
    except Exception as e:
        print(f"✗ Error in yield to price test: {e}")

if __name__ == "__main__":
    print("Starting Bloomberg Field Investigation...")
    print("Finding correct fields to replicate Defense First study exactly")
    print()
    
    # Run investigations
    investigate_treasury_bond_fields()
    investigate_alternative_treasury_sources()
    test_yield_to_price_conversion()
    
    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)
    print("Check output above for correct Bloomberg fields.")
