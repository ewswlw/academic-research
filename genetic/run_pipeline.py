import pandas as pd
from feature_engineering import feature_engineering
from ga_search_modular import run_ga_search

# CHANGE THIS to your actual price column name and data file
DATA_FILE = "monthly_all.csv"
PRICE_COL = "cad_ig_er_index"

import vectorbt as vbt
import numpy as np

if __name__ == "__main__":
    print("[Pipeline] Loading data...")
    df = pd.read_csv(DATA_FILE, parse_dates=["Date"], index_col="Date")
    price = df[PRICE_COL]
    print("[Pipeline] Running feature engineering...")
    features = feature_engineering(df)
    print("[Pipeline] Running GA search...")
    results = run_ga_search(features, price)

    # --- Buy and Hold Benchmark (vectorbt) ---
    print("[Pipeline] Running buy-and-hold benchmark backtest...")
    bh_signal = pd.Series(True, index=price.index)  # Always long
    bh_pf = vbt.Portfolio.from_signals(
        price,
        entries=bh_signal & ~bh_signal.shift(1).fillna(False),
        exits=~bh_signal & bh_signal.shift(1).fillna(False),
        freq="30D",
        init_cash=100
    )
    # --- Metrics ---
    print("\n[Pipeline] Collecting stats for best strategy and benchmark...")
    best_pf = vbt.Portfolio.from_signals(
        price,
        entries=results["best_signal"] & ~results["best_signal"].shift(1).fillna(False),
        exits=~results["best_signal"] & results["best_signal"].shift(1).fillna(False),
        freq="30D",
        init_cash=100
    )
    # Print stats for best strategy and buy-and-hold (no benchmark, not supported by Portfolio.stats())
    print("\n[Pipeline] Best Strategy Portfolio Stats (pf.stats()):")
    print(best_pf.stats())
    print("\n[Pipeline] Buy & Hold Portfolio Stats (pf.stats()):")
    print(bh_pf.stats())

    print("\n[Pipeline] Best Rule Logic:")
    print(results["best_rule_text"])
    # Optionally, print a step-by-step explanation here
