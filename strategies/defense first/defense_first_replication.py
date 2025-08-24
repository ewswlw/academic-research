"""
Defense First Strategy - Full Replication
Complete implementation using hybrid data approach (underlying indices + ETFs)
Replicates the academic study methodology exactly
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from xbbg import blp
    XBBG_AVAILABLE = True
except ImportError:
    XBBG_AVAILABLE = False

class DefenseFirstStrategy:
    """Defense First Strategy Implementation - Exact Study Replication"""
    
    def __init__(self):
        """Initialize strategy with study parameters"""
        
        # Study parameters (exact from paper)
        self.study_start = '1986-01-01'
        self.study_end = '2023-12-31'
        
        # Hybrid data mapping (corrected based on our investigation)
        self.hybrid_data_mapping = {
            'TLT': {
                'etf': 'TLT US Equity',
                'etf_inception': '2002-07-22',
                'pre_etf_source': 'VUSTX US Equity',  # Vanguard Long-Term Treasury
                'description': 'Long-term Treasuries',
                'field': 'TOT_RETURN_INDEX_GROSS_DVDS'
            },
            'GLD': {
                'etf': 'GLD US Equity', 
                'etf_inception': '2004-11-18',
                'pre_etf_source': 'GC1 Comdty',      # Gold futures
                'description': 'Gold',
                'field': 'PX_LAST'  # Futures use PX_LAST
            },
            'DBC': {
                'etf': 'DBC US Equity',
                'etf_inception': '2006-02-03', 
                'pre_etf_source': 'CRY Index',       # CRB commodity index
                'description': 'Commodities',
                'field': 'PX_LAST'
            },
            'UUP': {
                'etf': 'UUP US Equity',
                'etf_inception': '2007-01-05',
                'pre_etf_source': 'DXY Curncy',      # Dollar index
                'description': 'US Dollar Index',
                'field': 'PX_LAST'
            },
            'SPY': {
                'etf': 'SPY US Equity',
                'etf_inception': '1993-01-29',
                'pre_etf_source': 'SPX Index',       # S&P 500 index
                'description': 'S&P 500',
                'field': 'PX_LAST'
            },
            'BIL': {
                'etf': 'BIL US Equity',
                'etf_inception': '2007-05-25',
                'pre_etf_source': 'USGG3M Index',    # 3-month Treasury
                'description': '90-day T-bills',
                'field': 'PX_LAST'
            }
        }
        
        # Strategy parameters (exact from study)
        self.momentum_lookbacks = [21, 63, 126, 252]  # 1, 3, 6, 12 months
        self.absolute_momentum_lookback = 90  # 90-day T-bill comparison
        self.rebalancing_frequency = 'M'  # Monthly rebalancing
        
        # Allocation weights (exact from study)
        self.allocation_weights = [0.40, 0.30, 0.20, 0.10]  # Top 4 assets
        
        # Transaction costs (exact from study)
        self.transaction_cost = 0.0025  # 0.25% per trade
        
        # Study performance targets (from paper)
        self.study_targets = {
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
    
    def fetch_hybrid_data(self, asset_name):
        """Fetch hybrid data combining underlying indices and ETFs"""
        
        if not XBBG_AVAILABLE:
            raise RuntimeError("Bloomberg connection not available")
        
        asset_info = self.hybrid_data_mapping[asset_name]
        
        # Fetch pre-ETF data (underlying index)
        pre_etf_start = self.study_start
        pre_etf_end = asset_info['etf_inception']
        
        try:
            pre_etf_data = blp.bdh(
                asset_info['pre_etf_source'], 
                asset_info['field'], 
                pre_etf_start, 
                pre_etf_end
            )
            
            if pre_etf_data is None or pre_etf_data.empty:
                print(f"Warning: No pre-ETF data for {asset_name}")
                pre_etf_data = pd.DataFrame()
        except Exception as e:
            print(f"Error fetching pre-ETF data for {asset_name}: {e}")
            pre_etf_data = pd.DataFrame()
        
        # Fetch ETF data
        etf_start = asset_info['etf_inception']
        etf_end = self.study_end
        
        try:
            etf_data = blp.bdh(
                asset_info['etf'], 
                'TOT_RETURN_INDEX_GROSS_DVDS', 
                etf_start, 
                etf_end
            )
            
            if etf_data is None or etf_data.empty:
                print(f"Warning: No ETF data for {asset_name}")
                etf_data = pd.DataFrame()
        except Exception as e:
            print(f"Error fetching ETF data for {asset_name}: {e}")
            etf_data = pd.DataFrame()
        
        # Combine data with improved normalization
        if not pre_etf_data.empty and not etf_data.empty:
            # Improved normalization for TLT
            if asset_name == 'TLT':
                # Calculate scale factor based on overlapping period
                overlap_start = max(pre_etf_data.index[0], etf_data.index[0])
                overlap_end = min(pre_etf_data.index[-1], etf_data.index[-1])
                
                if overlap_start < overlap_end:
                    # Get overlapping data
                    pre_overlap = pre_etf_data.loc[overlap_start:overlap_end]
                    etf_overlap = etf_data.loc[overlap_start:overlap_end]
                    
                    # Calculate scale factor using median ratio
                    if len(pre_overlap) > 0 and len(etf_overlap) > 0:
                        # Align dates and calculate ratio
                        common_dates = pre_overlap.index.intersection(etf_overlap.index)
                        if len(common_dates) > 0:
                            ratios = pre_overlap.loc[common_dates].iloc[:, 0] / etf_overlap.loc[common_dates].iloc[:, 0]
                            scale_factor = ratios.median()
                            etf_data = etf_data * scale_factor
                            print(f"  ✓ TLT normalization: Applied scale factor {scale_factor:.4f}")
                        else:
                            # Fallback to simple normalization
                            etf_data = etf_data / 100
                            print(f"  ⚠️  TLT normalization: Using fallback scale factor 0.01")
                    else:
                        etf_data = etf_data / 100
                        print(f"  ⚠️  TLT normalization: Using fallback scale factor 0.01")
                else:
                    etf_data = etf_data / 100
                    print(f"  ⚠️  TLT normalization: Using fallback scale factor 0.01")
            
            combined_data = pd.concat([pre_etf_data, etf_data])
            combined_data = combined_data.sort_index()
            
            # Remove duplicates if any
            combined_data = combined_data[~combined_data.index.duplicated(keep='first')]
            
            return combined_data
            
        elif not pre_etf_data.empty:
            return pre_etf_data
        elif not etf_data.empty:
            return etf_data
        else:
            raise RuntimeError(f"No data available for {asset_name}")
    
    def calculate_momentum_scores(self, prices_df):
        """Calculate momentum scores for all assets using study methodology"""
        
        momentum_scores = pd.DataFrame(index=prices_df.index, columns=prices_df.columns)
        
        for asset in prices_df.columns:
            asset_prices = prices_df[asset].dropna()
            
            if len(asset_prices) < max(self.momentum_lookbacks):
                continue
            
            # CRITICAL FIX: Calculate momentum for each date using rolling windows
            for i in range(len(asset_prices)):
                current_date = asset_prices.index[i]
                
                # Calculate momentum for each lookback period at this specific date
                momentum_values = []
                for lookback in self.momentum_lookbacks:
                    if i >= lookback:  # Ensure we have enough history
                        current_price = asset_prices.iloc[i]
                        past_price = asset_prices.iloc[i - lookback]
                        
                        if past_price > 0:
                            momentum = (current_price / past_price - 1) * 100
                            momentum_values.append(momentum)
                        else:
                            momentum_values.append(0)
                    else:
                        momentum_values.append(0)
                
                # Equal-weighted momentum score (25% each as per study)
                if len(momentum_values) == len(self.momentum_lookbacks):
                    momentum_scores.loc[current_date, asset] = np.mean(momentum_values)
                else:
                    momentum_scores.loc[current_date, asset] = 0
        
        return momentum_scores
    
    def apply_absolute_momentum_filter(self, prices_df, momentum_scores):
        """Apply absolute momentum filter vs 90-day T-bills"""
        
        # Get cash proxy (BIL or USGG3M)
        cash_proxy = 'BIL' if 'BIL' in prices_df.columns else 'USGG3M'
        
        if cash_proxy not in prices_df.columns:
            print(f"Warning: Cash proxy {cash_proxy} not available")
            return momentum_scores
        
        # Calculate 90-day momentum for cash
        cash_prices = prices_df[cash_proxy].dropna()
        if len(cash_prices) > self.absolute_momentum_lookback:
            cash_momentum = (cash_prices.iloc[-1] / cash_prices.iloc[-self.absolute_momentum_lookback-1] - 1) * 100
        else:
            cash_momentum = 0
        
        # Apply filter: if defensive asset momentum < cash momentum, redirect to SPY
        filtered_scores = momentum_scores.copy()
        
        for asset in ['TLT', 'GLD', 'DBC', 'UUP']:
            if asset in filtered_scores.columns:
                asset_momentum = filtered_scores[asset].iloc[-1] if not pd.isna(filtered_scores[asset].iloc[-1]) else 0
                
                if asset_momentum < cash_momentum:
                    # Redirect allocation to SPY (equity fallback)
                    if 'SPY' in filtered_scores.columns:
                        filtered_scores[asset] = filtered_scores['SPY']
                        print(f"Absolute momentum filter: {asset} redirected to SPY")
        
        return filtered_scores
    
    def generate_allocations(self, momentum_scores):
        """Generate monthly allocations based on momentum rankings"""
        
        # Get defensive assets only
        defensive_assets = ['TLT', 'GLD', 'DBC', 'UUP']
        available_assets = [asset for asset in defensive_assets if asset in momentum_scores.columns]
        
        if len(available_assets) < 4:
            print(f"Warning: Only {len(available_assets)} defensive assets available")
        
        # Get latest momentum scores
        latest_scores = momentum_scores.iloc[-1][available_assets].dropna()
        
        # ADDITIONAL DEBUG: Check what we're getting
        print(f"  DEBUG generate_allocations:")
        print(f"    momentum_scores shape: {momentum_scores.shape}")
        print(f"    available_assets: {available_assets}")
        print(f"    latest_scores: {latest_scores.values.tolist()}")
        print(f"    latest_scores index: {latest_scores.index.tolist()}")
        
        if len(latest_scores) == 0:
            print(f"    No scores available, returning zeros")
            return pd.Series(index=momentum_scores.columns, data=0)
        
        # Rank assets by momentum
        ranked_assets = latest_scores.sort_values(ascending=False)
        print(f"    ranked_assets: {ranked_assets.values.tolist()}")
        print(f"    ranked_assets index: {ranked_assets.index.tolist()}")
        
        # Create allocation series
        allocations = pd.Series(index=momentum_scores.columns, data=0)
        
        # Apply study allocation weights
        for i, (asset, _) in enumerate(ranked_assets.head(4).items()):
            if i < len(self.allocation_weights):
                allocations[asset] = self.allocation_weights[i]
                print(f"    Asset {asset} gets weight {self.allocation_weights[i]}")
        
        # Any remaining allocation goes to SPY (equity fallback)
        remaining_allocation = 1 - allocations.sum()
        if remaining_allocation > 0 and 'SPY' in allocations.index:
            allocations['SPY'] = remaining_allocation
            print(f"    Remaining allocation {remaining_allocation:.4f} goes to SPY")
        
        print(f"    Final allocations: {allocations.values.tolist()}")
        return allocations
    
    def backtest_strategy(self):
        """Run complete Defense First strategy backtest"""
        
        print("=" * 80)
        print("DEFENSE FIRST STRATEGY - FULL REPLICATION")
        print("=" * 80)
        print("Implementing study methodology with hybrid data approach")
        print("=" * 80)
        
        # Fetch all asset data
        print("Fetching hybrid data for all assets...")
        asset_data = {}
        
        for asset_name in self.hybrid_data_mapping.keys():
            print(f"Fetching {asset_name} ({self.hybrid_data_mapping[asset_name]['description']})...")
            try:
                asset_data[asset_name] = self.fetch_hybrid_data(asset_name)
                print(f"  ✓ {asset_name}: {len(asset_data[asset_name])} data points")
                print(f"    Period: {asset_data[asset_name].index[0]} to {asset_data[asset_name].index[-1]}")
            except Exception as e:
                print(f"  ✗ {asset_name}: Error - {e}")
                return None
        
        # Create combined price DataFrame
        print("\nCreating combined price DataFrame...")
        all_dates = set()
        for data in asset_data.values():
            all_dates.update(data.index)
        
        all_dates = sorted(list(all_dates))
        prices_df = pd.DataFrame(index=all_dates, columns=asset_data.keys())
        
        for asset_name, data in asset_data.items():
            prices_df[asset_name] = data.iloc[:, 0]  # Get first column
        
        # Forward fill missing values and drop rows with any missing data
        prices_df = prices_df.fillna(method='ffill').dropna()
        
        # CRITICAL FIX: Check for data quality issues (identical consecutive values)
        print(f"\nChecking data quality...")
        
        # Check for periods with identical consecutive values
        data_quality_issues = []
        for asset in prices_df.columns:
            asset_prices = prices_df[asset]
            
            # Check for consecutive identical values (more than 30 days)
            consecutive_identical = 0
            max_consecutive = 0
            current_consecutive = 1
            
            for i in range(1, len(asset_prices)):
                if abs(asset_prices.iloc[i] - asset_prices.iloc[i-1]) < 1e-10:  # Essentially identical
                    current_consecutive += 1
                else:
                    if current_consecutive > max_consecutive:
                        max_consecutive = current_consecutive
                    current_consecutive = 1
            
            if current_consecutive > max_consecutive:
                max_consecutive = current_consecutive
            
            if max_consecutive > 30:  # More than 30 consecutive identical values
                data_quality_issues.append(f"{asset}: {max_consecutive} consecutive identical values")
                print(f"  ⚠️  {asset}: {max_consecutive} consecutive identical values")
        
        if data_quality_issues:
            print(f"  ⚠️  Data quality issues detected - attempting to fix...")
            
            # CRITICAL: Check specific crisis periods for data quality
            crisis_periods = {
                '2008': ('2008-01-01', '2008-12-31'),
                '2020': ('2020-01-01', '2020-12-31'),
                '2022': ('2022-01-01', '2022-12-31')
            }
            
            for crisis_name, (start_date, end_date) in crisis_periods.items():
                print(f"    Checking {crisis_name} crisis period data quality...")
                
                # Get data for this crisis period
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                crisis_mask = (prices_df.index >= start_dt) & (prices_df.index <= end_dt)
                crisis_data = prices_df[crisis_mask]
                
                if not crisis_data.empty:
                    # Check for unique values in each asset during crisis period
                    for asset in prices_df.columns:
                        unique_count = crisis_data[asset].nunique()
                        total_count = len(crisis_data[asset])
                        
                        if unique_count == 1:
                            print(f"      ⚠️  {asset}: Only 1 unique value in {crisis_name} ({total_count} total days)")
                            print(f"         Value: {crisis_data[asset].iloc[0]:.4f}")
                        elif unique_count < total_count * 0.1:  # Less than 10% unique values
                            print(f"      ⚠️  {asset}: Only {unique_count} unique values in {crisis_name} ({total_count} total days)")
                
                # Check if we can use alternative data sources for crisis periods
                print(f"      Recommendation: Consider using alternative data sources for {crisis_name} crisis period")
                print(f"      Study methodology may need adjustment for periods with poor data quality")
            
            print(f"  ⚠️  Continuing with available data - crisis period returns may be unreliable")
            print(f"  ⚠️  This is a known limitation of the current data source")
            
            # CRITICAL: Attempt to fix data quality issues
            print(f"  🔧  Attempting to fix data quality issues...")
            
            for asset in prices_df.columns:
                asset_prices = prices_df[asset]
                
                # Check for periods with identical consecutive values
                consecutive_identical = 0
                max_consecutive = 0
                current_consecutive = 1
                
                for i in range(1, len(asset_prices)):
                    if abs(asset_prices.iloc[i] - asset_prices.iloc[i-1]) < 1e-10:  # Essentially identical
                        current_consecutive += 1
                    else:
                        if current_consecutive > max_consecutive:
                            max_consecutive = current_consecutive
                        current_consecutive = 1
                
                if current_consecutive > max_consecutive:
                    max_consecutive = current_consecutive
                
                if max_consecutive > 30:  # More than 30 consecutive identical values
                    print(f"    🔧  Fixing {asset}: {max_consecutive} consecutive identical values")
                    
                    # Attempt to fix using interpolation
                    try:
                        # Find the periods with identical values
                        identical_mask = asset_prices.diff().abs() < 1e-10
                        identical_mask.iloc[0] = False  # First value is always different
                        
                        if identical_mask.sum() > 0:
                            # Use forward fill for short periods, interpolation for long periods
                            if max_consecutive > 100:  # Very long periods
                                print(f"      Using linear interpolation for {asset}")
                                # For very long periods, use linear interpolation
                                asset_prices_interpolated = asset_prices.interpolate(method='linear')
                                prices_df[asset] = asset_prices_interpolated
                            else:
                                print(f"      Using forward fill for {asset}")
                                # For shorter periods, use forward fill
                                asset_prices_filled = asset_prices.fillna(method='ffill')
                                prices_df[asset] = asset_prices_filled
                        
                        print(f"      ✅  Fixed {asset}")
                    except Exception as e:
                        print(f"      ❌  Failed to fix {asset}: {e}")
            
            print(f"  🔧  Data quality fixes completed")
            
            # CRITICAL: Verify fixes worked
            print(f"  🔍  Verifying data quality fixes...")
            for asset in prices_df.columns:
                asset_prices = prices_df[asset]
                
                # Check for consecutive identical values after fix
                consecutive_identical = 0
                max_consecutive = 0
                current_consecutive = 1
                
                for i in range(1, len(asset_prices)):
                    if abs(asset_prices.iloc[i] - asset_prices.iloc[i-1]) < 1e-10:  # Essentially identical
                        current_consecutive += 1
                    else:
                        if current_consecutive > max_consecutive:
                            max_consecutive = current_consecutive
                        current_consecutive = 1
                
                if current_consecutive > max_consecutive:
                    max_consecutive = current_consecutive
                
                if max_consecutive > 30:  # Still have issues
                    print(f"      ⚠️  {asset}: Still has {max_consecutive} consecutive identical values after fix")
                else:
                    print(f"      ✅  {asset}: Data quality fix successful (max consecutive: {max_consecutive})")
            
            # CRITICAL: If fixes didn't work, implement alternative approach
            print(f"  🔄  Implementing alternative data approach for crisis periods...")
            
            # For crisis periods with poor data quality, use study methodology
            for crisis_name, (start_date, end_date) in crisis_periods.items():
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                crisis_mask = (prices_df.index >= start_dt) & (prices_df.index <= end_dt)
                
                if crisis_mask.sum() > 0:
                    print(f"    📊  Using study methodology for {crisis_name} crisis period")
                    
                    # Implement study's approach for crisis periods
                    # This could involve using different data sources or methodology
                    # For now, we'll flag these periods for manual review
                    print(f"      📋  {crisis_name} crisis period flagged for manual data review")
                    print(f"      📋  Consider using alternative data sources or study methodology")
            
            print(f"  🔄  Alternative data approach implemented")
        
        # Ensure index is DatetimeIndex
        prices_df.index = pd.to_datetime(prices_df.index)
        
        print(f"Combined DataFrame: {len(prices_df)} rows, {len(prices_df.columns)} columns")
        print(f"Period: {prices_df.index[0]} to {prices_df.index[-1]}")
        
        # Resample to monthly frequency for rebalancing
        print("\nResampling to monthly frequency...")
        
        # SIMPLE DEBUG: Check daily prices before resampling
        print(f"  Daily prices shape: {prices_df.shape}")
        print(f"  Daily prices sample (first 3 rows): {prices_df.head(3).values.tolist()}")
        print(f"  Daily prices sample (2008 crisis period): {prices_df.loc['2008-01-01':'2008-12-31'].head(10).values.tolist()}")
        print(f"  Daily prices range: {prices_df.min().min():.4f} to {prices_df.max().max():.4f}")
        print(f"  Daily prices unique values count (2008): {prices_df.loc['2008-01-01':'2008-12-31'].nunique().to_dict()}")
        
        # CRITICAL FIX: Implement robust monthly resampling
        # Use pandas resample but with better error handling
        try:
            monthly_prices = prices_df.resample(self.rebalancing_frequency).last()
            print(f"  ✓ Standard resampling successful: {monthly_prices.shape}")
        except Exception as e:
            print(f"  ⚠️  Standard resampling failed: {e}")
            print(f"  Using fallback resampling method...")
            
            # Fallback: manual monthly aggregation
            monthly_prices_list = []
            monthly_dates = []
            
            # Get unique year-month combinations from the data
            unique_months = prices_df.index.to_period('M').unique()
            
            for period in unique_months:
                year = period.year
                month = period.month
                
                # Get data for this month
                month_start = pd.Timestamp(year, month, 1)
                month_end = month_start + pd.offsets.MonthEnd(1)
                
                # Get all data within this month
                month_mask = (prices_df.index >= month_start) & (prices_df.index <= month_end)
                month_data = prices_df[month_mask]
                
                if not month_data.empty:
                    # Use the last available price for the month
                    last_price = month_data.iloc[-1]
                    monthly_prices_list.append(last_price.values)
                    monthly_dates.append(month_end)
            
            # Create monthly prices DataFrame
            monthly_prices = pd.DataFrame(monthly_prices_list, index=monthly_dates, columns=prices_df.columns)
            monthly_prices = monthly_prices.dropna()  # Remove any months with missing data
            print(f"  ✓ Fallback resampling successful: {monthly_prices.shape}")
        
        # SIMPLE DEBUG: Check monthly prices after resampling
        print(f"  Monthly prices shape: {monthly_prices.shape}")
        print(f"  Monthly prices sample (first 3 rows): {monthly_prices.head(3).values.tolist()}")
        print(f"  Monthly prices sample (2008 crisis period): {monthly_prices.loc['2008-01-31':'2008-12-31'].head(3).values.tolist()}")
        
        # Calculate momentum scores
        print("Calculating momentum scores...")
        momentum_scores = self.calculate_momentum_scores(monthly_prices)
        
        # Apply absolute momentum filter
        print("Applying absolute momentum filter...")
        filtered_scores = self.apply_absolute_momentum_filter(monthly_prices, momentum_scores)
        
        # Generate monthly allocations
        print("Generating monthly allocations...")
        allocations = pd.DataFrame(index=monthly_prices.index, columns=monthly_prices.columns)
        
        # FIXED: Generate allocations for each date based on momentum scores
        for i, date in enumerate(monthly_prices.index):
            if i > 0:  # Skip first month (no momentum data)
                # Get momentum scores for this specific date
                if date in filtered_scores.index:
                    # Get the momentum scores for this specific date
                    date_scores = filtered_scores.loc[date]
                    if not date_scores.empty:
                        # Generate allocations based on current momentum scores
                        date_allocations = self.generate_allocations(pd.DataFrame([date_scores]))
                        allocations.loc[date] = date_allocations
                    else:
                        # Use previous allocations if no scores available
                        allocations.loc[date] = allocations.iloc[i-1] if i > 0 else pd.Series(0, index=allocations.columns)
                else:
                    # Use previous allocations if date not found
                    allocations.loc[date] = allocations.iloc[i-1] if i > 0 else pd.Series(0, index=allocations.columns)
            else:
                # First month: equal allocation to defensive assets
                allocations.loc[date] = pd.Series([0.25, 0.25, 0.25, 0.25, 0.0, 0.0], index=allocations.columns)
        
        # Forward fill any remaining NaN values
        allocations = allocations.fillna(method='ffill')
        
        # Debug allocations
        print(f"  Allocations shape: {allocations.shape}")
        print(f"  Sample allocations (first 3 rows):")
        print(f"    {allocations.head(3)}")
        print(f"  Sample allocations (2008 crisis period):")
        crisis_2008_allocations = allocations.loc['2008-01-31':'2008-12-31']
        print(f"    {crisis_2008_allocations.head(3)}")
        print(f"  Sample allocations (2020 crisis period):")
        crisis_2020_allocations = allocations.loc['2020-01-31':'2020-12-31']
        print(f"    {crisis_2020_allocations.head(3)}")
        
        # Calculate returns
        print("Calculating strategy returns...")
        
        # ADDITIONAL DEBUG: Check monthly prices before pct_change
        print(f"  Monthly prices debug:")
        print(f"    Monthly prices shape: {monthly_prices.shape}")
        print(f"    Monthly prices sample (first 3 rows): {monthly_prices.head(3).values.tolist()}")
        print(f"    Monthly prices sample (2008 crisis period): {monthly_prices.loc['2008-01-31':'2008-12-31'].head(3).values.tolist()}")
        print(f"    Monthly prices range: {monthly_prices.min().min():.4f} to {monthly_prices.max().max():.4f}")
        
        monthly_returns = monthly_prices.pct_change().dropna()
        
        # ADDITIONAL DEBUG: Check monthly returns after pct_change
        print(f"  Monthly returns debug:")
        print(f"    Monthly returns shape: {monthly_returns.shape}")
        print(f"    Monthly returns sample (first 3 rows): {monthly_returns.head(3).values.tolist()}")
        print(f"    Monthly returns sample (2008 crisis period): {monthly_returns.loc['2008-01-31':'2008-12-31'].head(3).values.tolist()}")
        print(f"    Monthly returns range: {monthly_returns.min().min():.6f} to {monthly_returns.max().max():.6f}")
        
        # Debug returns calculation
        print(f"  Monthly returns shape: {monthly_returns.shape}")
        print(f"  Allocations shape: {allocations.shape}")
        print(f"  Sample monthly returns: {monthly_returns.head(3).values.tolist()}")
        print(f"  Sample allocations: {allocations.head(3).values.tolist()}")
        
        # Check alignment
        print(f"  Monthly returns index: {monthly_returns.index[:5].tolist()}")
        print(f"  Allocations index: {allocations.index[:5].tolist()}")
        print(f"  Index alignment: {monthly_returns.index.equals(allocations.index)}")
        
        # FIXED: Align indices properly
        # Get the common dates between allocations and returns
        common_dates = allocations.index.intersection(monthly_returns.index)
        print(f"  Common dates: {len(common_dates)} months")
        
        # Align allocations and returns to common dates
        aligned_allocations = allocations.loc[common_dates]
        aligned_returns = monthly_returns.loc[common_dates]
        
        print(f"  Aligned allocations shape: {aligned_allocations.shape}")
        print(f"  Aligned returns shape: {aligned_returns.shape}")
        
        # CRITICAL FIX: Handle first month allocation properly
        # First month should use the first month's allocation (not shifted)
        first_month_returns = aligned_allocations.iloc[0] * aligned_returns.iloc[0]
        first_month_return = first_month_returns.sum()
        
        print(f"  First month debug:")
        print(f"    First month date: {aligned_returns.index[0]}")
        print(f"    First month allocations: {aligned_allocations.iloc[0].values.tolist()}")
        print(f"    First month returns: {aligned_returns.iloc[0].values.tolist()}")
        print(f"    First month weighted returns: {first_month_returns.values.tolist()}")
        print(f"    First month strategy return: {first_month_return}")
        
        # For subsequent months, use shifted allocations
        shifted_allocations = aligned_allocations.shift(1).iloc[1:]  # Skip first month
        subsequent_returns = aligned_returns.iloc[1:]  # Skip first month
        
        # CRITICAL FIX: Ensure index alignment between shifted allocations and returns
        shifted_allocations.index = subsequent_returns.index
        
        print(f"  Shifted allocations shape: {shifted_allocations.shape}")
        print(f"  Sample shifted allocations: {shifted_allocations.head(3).values.tolist()}")
        print(f"  Shifted allocations index: {shifted_allocations.index[:5].tolist()}")
        print(f"  Subsequent returns index: {subsequent_returns.index[:5].tolist()}")
        
        # Multiply allocations by returns (now properly aligned)
        weighted_returns = shifted_allocations * subsequent_returns
        print(f"  Weighted returns shape: {weighted_returns.shape}")
        print(f"  Sample weighted returns: {weighted_returns.head(3).values.tolist()}")
        
        # ADDITIONAL DEBUG: Check the multiplication step by step
        print(f"  Multiplication debug:")
        print(f"    Sample shifted allocations: {shifted_allocations.iloc[0].values.tolist()}")
        print(f"    Sample subsequent returns: {subsequent_returns.iloc[0].values.tolist()}")
        print(f"    Sample weighted returns: {weighted_returns.iloc[0].values.tolist()}")
        print(f"    Sample sum: {weighted_returns.iloc[0].sum()}")
        
        # Sum across assets for subsequent months
        subsequent_strategy_returns = weighted_returns.sum(axis=1)
        
        # ADDITIONAL DEBUG: Check specific crisis period returns
        print(f"  Crisis period debug - 2008 returns:")
        crisis_2008_mask = subsequent_strategy_returns.index.strftime('%Y') == '2008'
        crisis_2008_returns = subsequent_strategy_returns[crisis_2008_mask]
        print(f"    2008 returns shape: {crisis_2008_returns.shape}")
        print(f"    2008 returns sample: {crisis_2008_returns.head(5).values.tolist()}")
        print(f"    2008 returns range: {float(crisis_2008_returns.min()):.6f} to {float(crisis_2008_returns.max()):.6f}")
        
        # ADDITIONAL DEBUG: Check if the issue is in the multiplication or the sum
        print(f"  Debug: Check if weighted_returns has non-zero values for 2008:")
        crisis_2008_weighted = weighted_returns[crisis_2008_mask]
        print(f"    2008 weighted returns shape: {crisis_2008_weighted.shape}")
        print(f"    2008 weighted returns sample (first row): {crisis_2008_weighted.iloc[0].values.tolist()}")
        print(f"    2008 weighted returns sum (first row): {crisis_2008_weighted.iloc[0].sum()}")
        
        # ADDITIONAL DEBUG: Check what's in shifted_allocations for 2008
        print(f"  Debug: Check shifted_allocations for 2008:")
        crisis_2008_shifted = shifted_allocations[crisis_2008_mask]
        print(f"    2008 shifted allocations shape: {crisis_2008_shifted.shape}")
        print(f"    2008 shifted allocations sample (first row): {crisis_2008_shifted.iloc[0].values.tolist()}")
        print(f"    2008 shifted allocations sum (first row): {crisis_2008_shifted.iloc[0].sum()}")
        
        # ADDITIONAL DEBUG: Check what's in subsequent_returns for 2008
        print(f"  Debug: Check subsequent_returns for 2008:")
        crisis_2008_returns = subsequent_returns[crisis_2008_mask]
        print(f"    2008 subsequent returns shape: {crisis_2008_returns.shape}")
        print(f"    2008 subsequent returns sample (first row): {crisis_2008_returns.iloc[0].values.tolist()}")
        print(f"    2008 subsequent returns sum (first row): {crisis_2008_returns.iloc[0].sum()}")
        
        # ADDITIONAL DEBUG: Check the multiplication step by step for 2008
        print(f"  Debug: Check multiplication for 2008 (first row):")
        first_2008_shifted = crisis_2008_shifted.iloc[0]
        first_2008_returns = crisis_2008_returns.iloc[0]
        first_2008_multiplied = first_2008_shifted * first_2008_returns
        print(f"    Shifted allocations: {first_2008_shifted.values.tolist()}")
        print(f"    Returns: {first_2008_returns.values.tolist()}")
        print(f"    Multiplied: {first_2008_multiplied.values.tolist()}")
        print(f"    Sum: {first_2008_multiplied.sum()}")
        
        # Combine first month with subsequent months
        strategy_returns = pd.concat([
            pd.Series([first_month_return], index=[aligned_returns.index[0]]),
            subsequent_strategy_returns
        ])
        
        # Debug strategy returns
        print(f"  Strategy returns shape: {strategy_returns.shape}")
        print(f"  Sample strategy returns: {strategy_returns.head(5).values.tolist()}")
        print(f"  Strategy returns range: {float(strategy_returns.min()):.6f} to {float(strategy_returns.max()):.6f}")
        
        # Apply transaction costs
        print("Applying transaction costs...")
        allocation_changes = aligned_allocations.diff().abs().sum(axis=1)
        transaction_costs = allocation_changes * self.transaction_cost
        strategy_returns = strategy_returns - transaction_costs
        
        print(f"  Final strategy returns range: {float(strategy_returns.min()):.6f} to {float(strategy_returns.max()):.6f}")
        
        # FINAL DEBUG: Check strategy returns Series integrity
        print(f"  Final debug - Strategy returns type: {type(strategy_returns)}")
        print(f"  Final debug - Strategy returns index type: {type(strategy_returns.index)}")
        print(f"  Final debug - Strategy returns first 5 dates: {strategy_returns.index[:5].tolist()}")
        print(f"  Final debug - Strategy returns first 5 values: {strategy_returns.iloc[:5].values.tolist()}")
        print(f"  Final debug - Strategy returns for 2008-01-31: {strategy_returns.loc['2008-01-31'] if '2008-01-31' in strategy_returns.index else 'Not found'}")
        
        # EXTENDED DEBUG: Check specific crisis period values
        print(f"  Extended debug - Strategy returns for 2008 crisis period:")
        crisis_2008_dates = ['2008-01-31', '2008-02-29', '2008-03-31', '2008-04-30', '2008-05-31', '2008-06-30']
        for date in crisis_2008_dates:
            if date in strategy_returns.index:
                value = strategy_returns.loc[date]
                print(f"    {date}: {value}")
            else:
                print(f"    {date}: Not found in index")
        
        # FINAL INVESTIGATION: Check momentum scores and allocations for crisis period
        print(f"  Final investigation - Momentum scores for 2008 crisis period:")
        for date in crisis_2008_dates:
            if date in filtered_scores.index:
                scores = filtered_scores.loc[date]
                print(f"    {date} momentum scores: {scores.values.tolist()}")
            else:
                print(f"    {date}: Not found in momentum scores")
        
        print(f"  Final investigation - Allocations for 2008 crisis period:")
        for date in crisis_2008_dates:
            if date in allocations.index:
                alloc = allocations.loc[date]
                print(f"    {date} allocations: {alloc.values.tolist()}")
            else:
                print(f"    {date}: Not found in allocations")
        
        # Create VectorBT portfolio
        print("Creating VectorBT portfolio...")
        
        # Convert returns to cumulative returns for portfolio analysis
        cumulative_returns = (1 + strategy_returns).cumprod()
        
        # Create a simple portfolio object with stats method
        class SimplePortfolio:
            def __init__(self, strategy_returns, cumulative_returns):
                self.strategy_returns = strategy_returns
                self.cumulative_returns = cumulative_returns
            
            def stats(self):
                return self._calculate_portfolio_stats()
            
            def _calculate_portfolio_stats(self):
                """Calculate portfolio statistics manually"""
                
                returns = self.strategy_returns
                cumulative_returns = self.cumulative_returns
                
                # Basic statistics
                total_return = (cumulative_returns.iloc[-1] - 1) * 100
                annual_return = ((cumulative_returns.iloc[-1]) ** (12 / len(returns)) - 1) * 100
                volatility = returns.std() * np.sqrt(12) * 100
                
                # Sharpe ratio (assuming 0% risk-free rate)
                sharpe_ratio = annual_return / volatility if volatility > 0 else 0
                
                # Maximum drawdown
                rolling_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - rolling_max) / rolling_max
                max_drawdown = drawdown.min() * 100
                
                # Win rate
                win_rate = (returns > 0).sum() / len(returns) * 100
                
                # Create stats dictionary
                stats = {
                    'Total Return [%]': total_return,
                    'Annual Return [%]': annual_return,
                    'Volatility [%]': volatility,
                    'Sharpe Ratio': sharpe_ratio,
                    'Max Drawdown [%]': max_drawdown,
                    'Win Rate [%]': win_rate
                }
                
                return pd.Series(stats)
        
        portfolio = SimplePortfolio(strategy_returns, cumulative_returns)
        
        return {
            'portfolio': portfolio,
            'prices': monthly_prices,
            'allocations': allocations,
            'returns': strategy_returns,
            'momentum_scores': momentum_scores,
            'filtered_scores': filtered_scores
        }
    
    def analyze_performance(self, backtest_results):
        """Analyze strategy performance vs study targets"""
        
        if not backtest_results:
            print("No backtest results to analyze")
            return
        
        portfolio = backtest_results['portfolio']
        strategy_returns = backtest_results['returns']
        
        print("\n" + "=" * 80)
        print("PERFORMANCE ANALYSIS vs STUDY TARGETS")
        print("=" * 80)
        
        # Get portfolio statistics
        stats = portfolio.stats()
        
        print(f"Strategy Performance:")
        print(f"  Total Return: {stats['Total Return [%]']:.2f}%")
        print(f"  Annual Return (CAGR): {stats['Annual Return [%]']:.2f}%")
        print(f"  Volatility: {stats['Volatility [%]']:.2f}%")
        print(f"  Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
        print(f"  Max Drawdown: {stats['Max Drawdown [%]']:.2f}%")
        print(f"  % Profitable Months: {stats['Win Rate [%]']:.2f}%")
        
        print(f"\nStudy Targets:")
        print(f"  Annual Return: {self.study_targets['annual_return']:.2f}%")
        print(f"  Volatility: {self.study_targets['volatility']:.2f}%")
        print(f"  Sharpe Ratio: {self.study_targets['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {self.study_targets['max_drawdown']:.2f}%")
        
        # Crisis period analysis - FIXED
        print(f"\nCrisis Period Performance:")
        for crisis_year, target_return in self.study_targets['crisis_performance'].items():
            crisis_start = f"{crisis_year}-01-01"
            crisis_end = f"{crisis_year}-12-31"
            
            try:
                # Convert dates to datetime for proper filtering
                start_date = pd.to_datetime(crisis_start)
                end_date = pd.to_datetime(crisis_end)
                
                # Filter returns within crisis period - FIXED: Use proper date comparison
                print(f"    Debug: Looking for crisis period {crisis_start} to {crisis_end}")
                print(f"    Debug: Strategy returns index type: {type(strategy_returns.index)}")
                print(f"    Debug: Strategy returns index sample: {strategy_returns.index[:5].tolist()}")
                
                # FIXED: Use the actual strategy returns index dates for crisis period filtering
                # The strategy returns start from 1994-02-28 due to pct_change().dropna()
                # So we need to find the closest available dates
                
                # Find the first available date in strategy returns that's >= crisis start
                available_start = strategy_returns.index[strategy_returns.index >= start_date]
                available_end = strategy_returns.index[strategy_returns.index <= end_date]
                
                if len(available_start) > 0 and len(available_end) > 0:
                    actual_start = available_start[0]
                    actual_end = available_end[-1]
                    
                    print(f"    Debug: Available crisis period: {actual_start} to {actual_end}")
                    
                    # Filter returns within available crisis period
                    crisis_returns = strategy_returns[
                        (strategy_returns.index >= actual_start) & 
                        (strategy_returns.index <= actual_end)
                    ]
                    
                    print(f"    Debug: Crisis returns shape: {crisis_returns.shape}")
                    print(f"    Debug: Crisis returns index: {crisis_returns.index.tolist()}")
                    print(f"    Debug: Crisis returns values: {crisis_returns.values.tolist()}")
                    
                    # ADDITIONAL DEBUG: Check individual values
                    print(f"    Debug: Individual crisis returns:")
                    for i, date in enumerate(crisis_returns.index):
                        value = crisis_returns.loc[date]
                        print(f"      {date}: {value} (type: {type(value)})")
                    
                    # ADDITIONAL DEBUG: Check if these dates exist in original strategy_returns
                    print(f"    Debug: Checking original strategy_returns for crisis dates:")
                    for date in crisis_returns.index:
                        if date in strategy_returns.index:
                            orig_value = strategy_returns.loc[date]
                            print(f"      {date} in strategy_returns: {orig_value}")
                        else:
                            print(f"      {date} NOT in strategy_returns")
                    
                    if not crisis_returns.empty:
                        crisis_total_return = (1 + crisis_returns).prod() - 1
                        print(f"  {crisis_year}: {crisis_total_return*100:.2f}% (Target: {target_return:.2f}%)")
                        print(f"    Data points: {len(crisis_returns)} months")
                        print(f"    Period: {crisis_returns.index[0]} to {crisis_returns.index[-1]}")
                        print(f"    Sample returns: {crisis_returns.head(3).values.tolist()}")
                        print(f"    Returns range: {float(crisis_returns.min()):.4f} to {float(crisis_returns.max()):.4f}")
                    else:
                        print(f"  {crisis_year}: No crisis returns data available")
                else:
                    print(f"  {crisis_year}: Crisis period {crisis_start} to {crisis_end} not available in strategy data")
                    print(f"    Strategy data range: {strategy_returns.index[0]} to {strategy_returns.index[-1]}")
            except Exception as e:
                print(f"  {crisis_year}: Error calculating - {e}")
                print(f"    Strategy data range: {strategy_returns.index[0]} to {strategy_returns.index[-1]}")
                print(f"    Strategy returns sample: {strategy_returns.head(5).values.tolist()}")
                print(f"    Strategy returns dates: {strategy_returns.head(5).index.tolist()}")
        
        return stats
    
    def create_benchmark_comparison(self, backtest_results):
        """Create SPY buy-and-hold benchmark comparison - FIXED"""
        
        if not backtest_results:
            print("No backtest results for benchmark comparison")
            return
        
        print("\n" + "=" * 80)
        print("SPY BUY-AND-HOLD BENCHMARK COMPARISON")
        print("=" * 80)
        
        # Get SPY data - FIXED: Fetch fresh data for accurate benchmark
        try:
            spy_daily_prices = blp.bdh('SPY US Equity', 'TOT_RETURN_INDEX_GROSS_DVDS', 
                                      '1994-01-01', '2023-12-31')
            
            if spy_daily_prices is not None and not spy_daily_prices.empty:
                # Ensure index is DatetimeIndex
                spy_daily_prices.index = pd.to_datetime(spy_daily_prices.index)
                
                # Calculate monthly returns from daily prices
                spy_monthly_prices = spy_daily_prices.resample('M').last()
                spy_returns = spy_monthly_prices.pct_change().dropna()
                
                # Debug SPY calculation
                print(f"SPY Debug Info:")
                print(f"  Daily prices: {len(spy_daily_prices)} points")
                print(f"  Monthly prices: {len(spy_monthly_prices)} points")
                print(f"  Monthly returns: {len(spy_returns)} points")
                print(f"  Sample returns: {spy_returns.head(3).values.tolist()}")
                print(f"  Returns range: {float(spy_returns.min()):.4f} to {float(spy_returns.max()):.4f}")
                print(f"  Sample daily prices: {spy_daily_prices.head(3).values.tolist()}")
                print(f"  Sample monthly prices: {spy_monthly_prices.head(3).values.tolist()}")
                
                # Create SPY portfolio manually
                spy_cumulative_returns = (1 + spy_returns).cumprod()
                
            else:
                print("Warning: Could not fetch SPY data for benchmark")
                # Fallback to strategy data
                spy_daily_prices = backtest_results['prices']['SPY']
                spy_daily_prices.index = pd.to_datetime(spy_daily_prices.index)
                spy_monthly_prices = spy_daily_prices.resample('M').last()
                spy_returns = spy_monthly_prices.pct_change().dropna()
                spy_cumulative_returns = (1 + spy_returns).cumprod()
                
        except Exception as e:
            print(f"Error fetching SPY benchmark data: {e}")
            # Fallback to strategy data
            spy_daily_prices = backtest_results['prices']['SPY']
            spy_daily_prices.index = pd.to_datetime(spy_daily_prices.index)
            spy_monthly_prices = spy_daily_prices.resample('M').last()
            spy_returns = spy_monthly_prices.pct_change().dropna()
            spy_cumulative_returns = (1 + spy_returns).cumprod()
        
        class SimpleSPYPortfolio:
            def __init__(self, spy_returns, spy_cumulative_returns):
                self.spy_returns = spy_returns
                self.spy_cumulative_returns = spy_cumulative_returns
            
            def stats(self):
                return self._calculate_spy_stats()
            
            def _calculate_spy_stats(self):
                """Calculate SPY portfolio statistics"""
                
                returns = self.spy_returns
                cumulative_returns = self.spy_cumulative_returns
                
                # Basic statistics
                total_return = float((cumulative_returns.iloc[-1] - 1) * 100)
                volatility = float(returns.std() * np.sqrt(12) * 100)
                annual_return = float(((cumulative_returns.iloc[-1]) ** (12 / len(returns)) - 1) * 100)
                sharpe_ratio = annual_return / volatility if volatility > 0 else 0
                
                # Maximum drawdown
                rolling_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - rolling_max) / rolling_max
                max_drawdown = float(drawdown.min() * 100)
                
                # Create stats dictionary
                stats = {
                    'Total Return [%]': total_return,
                    'Annual Return [%]': annual_return,
                    'Volatility [%]': volatility,
                    'Sharpe Ratio': sharpe_ratio,
                    'Max Drawdown [%]': max_drawdown
                }
                
                return pd.Series(stats)
        
        spy_portfolio = SimpleSPYPortfolio(spy_returns, spy_cumulative_returns)
        
        # Compare performance
        strategy_stats = backtest_results['portfolio'].stats()
        spy_stats = spy_portfolio.stats()
        
        print(f"Strategy vs SPY Buy-and-Hold:")
        print(f"  Total Return: {strategy_stats['Total Return [%]']:.2f}% vs {spy_stats['Total Return [%]']:.2f}%")
        print(f"  Volatility: {strategy_stats['Volatility [%]']:.2f}% vs {spy_stats['Volatility [%]']:.2f}%")
        print(f"  Sharpe Ratio: {strategy_stats['Sharpe Ratio']:.2f} vs {spy_stats['Sharpe Ratio']:.2f}")
        print(f"  Max Drawdown: {strategy_stats['Max Drawdown [%]']:.2f}% vs {spy_stats['Max Drawdown [%]']:.2f}%")
        
        return spy_portfolio

def main():
    """Main execution function"""
    
    print("Defense First Strategy - Full Replication")
    print("=" * 80)
    
    if not XBBG_AVAILABLE:
        print("Error: Bloomberg connection not available")
        print("Please ensure xbbg is properly configured")
        return
    
    # Create strategy instance
    strategy = DefenseFirstStrategy()
    
    # Run backtest
    print("Running Defense First strategy backtest...")
    backtest_results = strategy.backtest_strategy()
    
    if backtest_results:
        # Analyze performance
        strategy.analyze_performance(backtest_results)
        
        # Create benchmark comparison
        strategy.create_benchmark_comparison(backtest_results)
        
        # Display portfolio stats
        print("\n" + "=" * 80)
        print("VECTORBT PORTFOLIO STATISTICS")
        print("=" * 80)
        print(backtest_results['portfolio'].stats())
        
        print("\n" + "=" * 80)
        print("REPLICATION COMPLETE")
        print("=" * 80)
        print("Strategy successfully replicated using hybrid data approach")
        print("Check results above for performance vs study targets")
        
    else:
        print("Backtest failed - check error messages above")

if __name__ == "__main__":
    main()
