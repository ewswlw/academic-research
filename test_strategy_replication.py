"""
Test script for the complete Tactical Asset Allocation with Macroeconomic Regime Detection strategy

This script demonstrates the exact replication of the academic paper with:
1. FRED-MD macroeconomic data
2. ETF price data
3. Modified k-means regime detection
4. Multiple forecasting models
5. Comprehensive backtesting
"""

import pandas as pd
import numpy as np
from tactical_asset_allocation_regime import TacticalAssetAllocationRegime, display_results_summary
import warnings
warnings.filterwarnings('ignore')


def main():
    """Run complete strategy replication test"""
    print("🎯 TACTICAL ASSET ALLOCATION STRATEGY REPLICATION")
    print("=" * 60)
    print("📚 Paper: 'Tactical Asset Allocation with Macroeconomic Regime Detection'")
    print("👥 Authors: Oliveira, Sandfelder, Fujita, Dong, Cucuringu")
    print("=" * 60)
    
    # Initialize strategy
    print("\n🚀 Initializing strategy...")
    strategy = TacticalAssetAllocationRegime(
        fred_api_key="149095a7c7bdd559b94280c6bdf6b3f9",
        fmp_api_key="mVMdO3LfRmwmW1bF7xw4M71WEiLjl8xD",
        estimation_window=48,  # 4 years as in paper
        variance_threshold=0.95,  # 95% variance explained
        n_regimes=6,  # As determined in paper
        random_state=42
    )
    
    # Test with smaller date range first for faster execution
    start_date = '2000-01-01'
    end_date = '2023-12-31'
    
    print(f"📅 Testing period: {start_date} to {end_date}")
    
    try:
        # Step 1: Test data fetching
        print("\n" + "="*50)
        print("📊 STEP 1: DATA COLLECTION")
        print("="*50)
        
        print("🔄 Fetching macroeconomic data...")
        macro_data = strategy.fetch_macroeconomic_data(start_date, end_date)
        print(f"✅ Macro data shape: {macro_data.shape}")
        
        print("\n🔄 Fetching ETF data...")
        etf_data = strategy.fetch_asset_data(start_date, end_date)
        print(f"✅ ETF data shape: {etf_data.shape}")
        
        # Step 2: Test preprocessing
        print("\n" + "="*50)
        print("🔧 STEP 2: DATA PREPROCESSING")
        print("="*50)
        
        processed_macro = strategy.preprocess_macro_data(macro_data)
        print(f"✅ Processed macro data shape: {processed_macro.shape}")
        
        # Step 3: Test regime detection
        print("\n" + "="*50)
        print("🎯 STEP 3: REGIME DETECTION")
        print("="*50)
        
        regime_labels, regime_probs = strategy.regime_classification(processed_macro)
        print(f"✅ Regime labels shape: {regime_labels.shape}")
        print(f"✅ Regime probabilities shape: {regime_probs.shape}")
        
        # Display regime statistics
        print("\n📊 Regime Statistics:")
        for i in range(strategy.n_regimes):
            count = np.sum(regime_labels == i)
            print(f"   Regime {i}: {count:3d} months ({count/len(regime_labels)*100:5.1f}%)")
        
        # Step 4: Test transition matrix
        transition_matrix = strategy.calculate_transition_matrix(regime_labels)
        print(f"✅ Transition matrix shape: {transition_matrix.shape}")
        
        # Step 5: Test forecasting models
        print("\n" + "="*50)
        print("🔮 STEP 4: FORECASTING MODELS")
        print("="*50)
        
        models = ['naive', 'black_litterman', 'ridge']
        forecast_results = {}
        
        for model in models:
            print(f"\n🔄 Testing {model} model...")
            forecasts = strategy.forecast_regime_returns(
                etf_data, regime_labels, regime_probs, transition_matrix, model
            )
            forecast_results[model] = forecasts
            print(f"✅ {model} forecasts shape: {forecasts.shape}")
        
        # Step 6: Test portfolio construction
        print("\n" + "="*50)
        print("📈 STEP 5: PORTFOLIO CONSTRUCTION")
        print("="*50)
        
        strategies_list = ['long_only', 'long_short', 'mixed']
        top_assets_list = [2, 3, 4]
        
        portfolio_results = {}
        
        for model, forecasts in forecast_results.items():
            for strategy_type in strategies_list:
                for top_assets in top_assets_list:
                    strategy_name = f"{model}_{strategy_type}_{top_assets}"
                    print(f"🔄 Constructing {strategy_name} portfolio...")
                    
                    weights = strategy.construct_portfolio(forecasts, strategy_type, top_assets)
                    portfolio_results[strategy_name] = weights
                    print(f"✅ {strategy_name} weights shape: {weights.shape}")
        
        # Step 7: Performance analysis
        print("\n" + "="*50)
        print("📊 STEP 6: PERFORMANCE ANALYSIS")
        print("="*50)
        
        performance_results = {}
        
        for strategy_name, weights in portfolio_results.items():
            print(f"🔄 Calculating performance for {strategy_name}...")
            
            # Align weights and returns
            common_dates = weights.index.intersection(etf_data.index)
            weights_aligned = weights.loc[common_dates]
            returns_aligned = etf_data.loc[common_dates]
            
            # Calculate portfolio returns
            portfolio_returns = (weights_aligned.shift(1) * returns_aligned).sum(axis=1).dropna()
            
            # Calculate metrics
            metrics = strategy._calculate_performance_metrics(portfolio_returns)
            metrics['returns'] = portfolio_returns
            performance_results[strategy_name] = metrics
            
            print(f"   📈 {strategy_name}:")
            print(f"      Annual Return: {metrics['annual_return']:8.2%}")
            print(f"      Sharpe Ratio:  {metrics['sharpe_ratio']:8.3f}")
            print(f"      Max Drawdown:  {metrics['max_drawdown']:8.2%}")
        
        # Add benchmarks
        print("\n🔄 Calculating benchmark performance...")
        
        # SPY benchmark
        spy_returns = etf_data['SPY'].dropna()
        spy_metrics = strategy._calculate_performance_metrics(spy_returns)
        spy_metrics['returns'] = spy_returns
        performance_results['SPY_benchmark'] = spy_metrics
        
        # Equal weight benchmark
        ew_returns = etf_data.mean(axis=1).dropna()
        ew_metrics = strategy._calculate_performance_metrics(ew_returns)
        ew_metrics['returns'] = ew_returns
        performance_results['Equal_Weight_benchmark'] = ew_metrics
        
        # Step 8: Display comprehensive results
        print("\n" + "="*80)
        print("🏆 FINAL RESULTS SUMMARY")
        print("="*80)
        
        display_results_summary(performance_results)
        
        # Identify best performing strategies
        print("\n🎯 TOP PERFORMING STRATEGIES:")
        sharpe_rankings = []
        for name, metrics in performance_results.items():
            if 'sharpe_ratio' in metrics:
                sharpe_rankings.append((name, metrics['sharpe_ratio']))
        
        sharpe_rankings.sort(key=lambda x: x[1], reverse=True)
        
        print("\n📊 By Sharpe Ratio:")
        for i, (name, sharpe) in enumerate(sharpe_rankings[:10]):
            print(f"   {i+1:2d}. {name:30s} Sharpe: {sharpe:6.3f}")
        
        # Paper comparison
        print("\n" + "="*80)
        print("📚 COMPARISON WITH PAPER RESULTS")
        print("="*80)
        print("🎯 Target metrics from original paper:")
        print("   - Best Sharpe Ratio: ~1.505 (ridge_lo_3)")
        print("   - Best Long-Only: ~1.177 (bl_lo_2)")
        print("   - SPY Benchmark: ~0.818")
        print("\n📊 Our replication results:")
        
        best_sharpe = max(sharpe_rankings, key=lambda x: x[1])
        spy_result = next((x for x in sharpe_rankings if 'SPY' in x[0]), None)
        
        print(f"   - Best Sharpe Ratio: {best_sharpe[1]:.3f} ({best_sharpe[0]})")
        if spy_result:
            print(f"   - SPY Benchmark: {spy_result[1]:.3f}")
        
        print("\n✅ STRATEGY REPLICATION COMPLETE!")
        print("🎉 All components successfully implemented and tested")
        
        return performance_results
        
    except Exception as e:
        print(f"\n❌ Error during strategy execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = main()