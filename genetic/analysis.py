"""
analysis.py

Modular analysis and statistics for trading strategies and backtests.
Exports: compute_all_stats, rolling_sharpe, etc.
"""
import pandas as pd
import numpy as np

def compute_all_stats(equity: pd.Series, returns: pd.Series) -> dict:
    """
    Compute summary statistics for a strategy.
    Ported from previous analysis scripts.
    """
    stats = {}
    try:
        stats['Total Return'] = equity.iloc[-1] / equity.iloc[0] - 1
        stats['CAGR'] = (equity.iloc[-1] / equity.iloc[0]) ** (12 / len(equity)) - 1
        stats['Volatility (Ann)'] = returns.std() * np.sqrt(12)
        stats['Sharpe'] = returns.mean() / returns.std() * np.sqrt(12)
        stats['Sortino'] = returns.mean() / returns[returns < 0].std() * np.sqrt(12)
        stats['Calmar'] = stats['CAGR'] / abs(((equity / equity.cummax()) - 1).min())
        stats['Omega'] = returns[returns > 0].sum() / abs(returns[returns < 0].sum())
        stats['Skew'] = returns.skew()
        stats['Kurtosis'] = returns.kurtosis()
        stats['Max Drawdown'] = ((equity / equity.cummax()) - 1).min()
        stats['Avg Drawdown'] = ((equity / equity.cummax()) - 1).mean()
        stats['Ulcer Index'] = np.sqrt(np.mean(np.square(np.minimum(0, (equity / equity.cummax() - 1)))))
        stats['Downside Deviation'] = returns[returns < 0].std() * np.sqrt(12)
        stats['VaR 5%'] = returns.quantile(0.05)
        stats['CVaR 5%'] = returns[returns <= stats['VaR 5%']].mean()
        stats['Tail Ratio'] = abs(returns[returns > 0].mean() / returns[returns < 0].mean())
        stats['Gain-to-Pain'] = returns.sum() / abs(returns[returns < 0].sum())
        stats['% Positive Months'] = (returns > 0).mean()
        stats['Best Month'] = returns.max()
        stats['Worst Month'] = returns.min()
        stats['Median Month'] = returns.median()
        stats['Std Monthly Return'] = returns.std()
        stats['Rolling 12m Sharpe (mean)'] = (returns.rolling(12).mean() / returns.rolling(12).std() * np.sqrt(12)).mean()
        print(f"[Analysis] Stats computed: Total Return={stats['Total Return']:.2%}, Sharpe={stats['Sharpe']:.2f}")
    except Exception as e:
        print(f"[ERROR] Failed to compute stats: {e}")
        raise
    return stats

def rolling_sharpe(returns: pd.Series, window: int = 12) -> pd.Series:
    """
    Compute rolling Sharpe ratio.
    """
    try:
        roll = returns.rolling(window)
        rsharpe = roll.mean() / roll.std() * np.sqrt(12)
        print(f"[Analysis] Rolling Sharpe computed (window={window})")
        return rsharpe
    except Exception as e:
        print(f"[ERROR] Failed to compute rolling Sharpe: {e}")
        raise
