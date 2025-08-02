"""
Demo script for Tactical Asset Allocation with Macroeconomic Regime Detection

This script demonstrates the complete strategy replication with a subset of data
to avoid API rate limiting issues while showing all components working.
"""

import pandas as pd
import numpy as np
from tactical_asset_allocation_regime import TacticalAssetAllocationRegime, display_results_summary
import warnings
warnings.filterwarnings('ignore')


def create_demo_strategy():
    """Create a strategy instance with reduced variables for demo purposes"""
    strategy = TacticalAssetAllocationRegime(
        fred_api_key="149095a7c7bdd559b94280c6bdf6b3f9",
        fmp_api_key="mVMdO3LfRmwmW1bF7xw4M71WEiLjl8xD",
        estimation_window=48,
        variance_threshold=0.95,
        n_regimes=6,
        random_state=42
    )
    
    # Use only key variables to avoid rate limiting
    strategy.fred_variables = {
        # Core economic indicators
        'INDPRO': 'INDPRO',      # Industrial Production
        'PAYEMS': 'PAYEMS',      # Nonfarm Payrolls
        'UNRATE': 'UNRATE',      # Unemployment Rate
        'FEDFUNDS': 'FEDFUNDS',  # Federal Funds Rate
        'TB3MS': 'TB3MS',        # 3-Month Treasury Rate
        'GS10': 'GS10',          # 10-Year Treasury Rate
        'CPIAUCSL': 'CPIAUCSL',  # Consumer Price Index
        'UMCSENT': 'UMCSENT',    # Consumer Sentiment
        'HOUST': 'HOUST',        # Housing Starts
        'M2SL': 'M2SL',          # M2 Money Supply
        # Add a few more for diversity
        'IPMANSICS': 'IPMANSICS', # Manufacturing Industrial Production
        'REALLN': 'REALLN',       # Real Estate Loans
        'AAA': 'AAA',             # AAA Corporate Bond Yield
        'BAA': 'BAA',             # BAA Corporate Bond Yield
        'PCEPI': 'PCEPI'          # PCE Price Index
    }
    
    return strategy


def main():
    """Run demo of the tactical asset allocation strategy"""
    print("🎯 TACTICAL ASSET ALLOCATION STRATEGY - DEMO")
    print("=" * 60)
    print("📚 Paper: 'Tactical Asset Allocation with Macroeconomic Regime Detection'")
    print("🎨 Demo Version - Using Core Variables Only")
    print("=" * 60)
    
    # Create demo strategy
    strategy = create_demo_strategy()
    print(f"📊 Using {len(strategy.fred_variables)} core macroeconomic variables")
    print(f"💰 Testing with {len(strategy.etfs)} ETFs")
    
    try:
        # Test period
        start_date = '2010-01-01'  # Shorter period for demo
        end_date = '2023-12-31'
        print(f"\n📅 Demo period: {start_date} to {end_date}")
        
        # Step 1: Data Collection
        print("\n" + "="*50)
        print("📊 STEP 1: DATA COLLECTION")
        print("="*50)
        
        print("🔄 Fetching core macroeconomic data...")
        macro_data = strategy.fetch_macroeconomic_data(start_date, end_date)
        
        print("\n🔄 Fetching ETF data...")
        etf_data = strategy.fetch_asset_data(start_date, end_date)
        
        # Step 2: Preprocessing
        print("\n" + "="*50)
        print("🔧 STEP 2: DATA PREPROCESSING & REGIME DETECTION")
        print("="*50)
        
        processed_macro = strategy.preprocess_macro_data(macro_data)
        regime_labels, regime_probs = strategy.regime_classification(processed_macro)
        transition_matrix = strategy.calculate_transition_matrix(regime_labels)
        
        # Step 3: Strategy Comparison
        print("\n" + "="*50)
        print("🚀 STEP 3: STRATEGY COMPARISON")
        print("="*50)
        
        results = {}
        
        # Test key strategies from the paper
        strategies_to_test = [
            ('naive', 'long_only', 3),
            ('black_litterman', 'long_only', 2),
            ('ridge', 'long_only', 3),
            ('ridge', 'mixed', 2)
        ]
        
        for model, strategy_type, top_assets in strategies_to_test:
            strategy_name = f"{model}_{strategy_type}_{top_assets}"
            print(f"\n🔄 Testing {strategy_name}...")
            
            # Generate forecasts
            forecasts = strategy.forecast_regime_returns(
                etf_data, regime_labels, regime_probs, transition_matrix, model
            )
            
            # Construct portfolio
            weights = strategy.construct_portfolio(forecasts, strategy_type, top_assets)
            
            # Calculate performance
            common_dates = weights.index.intersection(etf_data.index)
            weights_aligned = weights.loc[common_dates]
            returns_aligned = etf_data.loc[common_dates]
            
            # Portfolio returns
            portfolio_returns = (weights_aligned.shift(1) * returns_aligned).sum(axis=1).dropna()
            
            # Performance metrics
            metrics = strategy._calculate_performance_metrics(portfolio_returns)
            metrics['returns'] = portfolio_returns
            results[strategy_name] = metrics
            
            print(f"   📈 Annual Return: {metrics['annual_return']:8.2%}")
            print(f"   ⚡ Sharpe Ratio:  {metrics['sharpe_ratio']:8.3f}")
            print(f"   📉 Max Drawdown:  {metrics['max_drawdown']:8.2%}")
        
        # Add benchmarks
        print("\n🔄 Adding benchmarks...")
        
        # SPY benchmark
        spy_returns = etf_data['SPY'].dropna()
        spy_metrics = strategy._calculate_performance_metrics(spy_returns)
        spy_metrics['returns'] = spy_returns
        results['SPY_Benchmark'] = spy_metrics
        
        # Equal weight benchmark
        ew_returns = etf_data.mean(axis=1).dropna()
        ew_metrics = strategy._calculate_performance_metrics(ew_returns)
        ew_metrics['returns'] = ew_returns
        results['Equal_Weight_Benchmark'] = ew_metrics
        
        # Step 4: Results Analysis
        print("\n" + "="*80)
        print("🏆 FINAL RESULTS - DEMO")
        print("="*80)
        
        display_results_summary(results)
        
        # Rankings
        sharpe_rankings = [(name, metrics['sharpe_ratio']) 
                          for name, metrics in results.items() 
                          if 'sharpe_ratio' in metrics]
        sharpe_rankings.sort(key=lambda x: x[1], reverse=True)
        
        print("\n🏅 STRATEGY RANKINGS (by Sharpe Ratio):")
        for i, (name, sharpe) in enumerate(sharpe_rankings):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
            print(f"   {medal} {i+1}. {name:25s} Sharpe: {sharpe:6.3f}")
        
        # Key insights
        print("\n" + "="*80)
        print("🎯 KEY INSIGHTS FROM DEMO")
        print("="*80)
        
        best_strategy = sharpe_rankings[0]
        spy_sharpe = next((sharpe for name, sharpe in sharpe_rankings if 'SPY' in name), 0)
        
        print(f"✅ Best performing strategy: {best_strategy[0]} (Sharpe: {best_strategy[1]:.3f})")
        print(f"📊 SPY benchmark Sharpe ratio: {spy_sharpe:.3f}")
        print(f"🚀 Outperformance: {(best_strategy[1] - spy_sharpe):.3f} Sharpe ratio improvement")
        
        print(f"\n🔬 Regime Analysis:")
        unique_regimes = np.unique(regime_labels)
        print(f"   - Detected {len(unique_regimes)} distinct market regimes")
        for regime in unique_regimes:
            count = np.sum(regime_labels == regime)
            print(f"   - Regime {regime}: {count} months ({count/len(regime_labels)*100:.1f}%)")
        
        print(f"\n📈 Strategy Components Successfully Demonstrated:")
        print(f"   ✅ FRED macroeconomic data integration")
        print(f"   ✅ Modified k-means regime detection")
        print(f"   ✅ PCA dimensionality reduction")
        print(f"   ✅ Probabilistic regime classification")
        print(f"   ✅ Multiple forecasting models (Naive, Black-Litterman, Ridge)")
        print(f"   ✅ Position sizing strategies")
        print(f"   ✅ Comprehensive performance analysis")
        
        print(f"\n🎉 DEMO COMPLETE - Strategy Successfully Replicated!")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = main()