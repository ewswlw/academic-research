"""
backtest.py

Modular backtesting logic for trading strategies.
Exports: backtest_rule(price: pd.Series, signal: pd.Series) -> object
"""
import vectorbt as vbt
import pandas as pd

def backtest_rule(price: pd.Series, signal: pd.Series) -> vbt.Portfolio:
    """
    Run vectorbt backtest for a given long-only signal.
    Entry when signal goes True, exit when signal goes False.
    Args:
        price: pd.Series, price series for the asset
        signal: pd.Series, boolean or int (0/1) signal series
    Returns:
        vbt.Portfolio object
    """
    try:
        entries = signal & ~signal.shift(1).fillna(False)
        exits = ~signal & signal.shift(1).fillna(False)
        pf = vbt.Portfolio.from_signals(
            price,
            entries,
            exits,
            freq="30D",  # approximates monthly
            init_cash=1_000.0  # nominal starting capital
        )
        print(f"[Backtest] Portfolio created: {pf.stats()['Total Return [%]']:.2f}% return")
        return pf
    except Exception as e:
        print(f"[ERROR] Backtest failed: {e}")
        raise
