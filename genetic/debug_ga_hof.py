"""Debug script to inspect Hall‑of‑Fame (HOF) individuals.

Run:
    poetry run python genetic/debug_ga_hof.py --csv genetic/monthly_all.csv

It will:
1. Re‑create the dataset splits.
2. Re‑run the GA (using the same seed) to obtain the HOF.
3. For each HOF individual, print cumulative returns on Train / Val / Test.
4. For the top individual (hof[0]), print raw GP outputs, z‑scores, and signal counts on the test set.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import data_io
import features
from deap import gp
from strategy_ga import (
    evolve,
    compile_individual,
    make_primitives,
    train_val_test_split,
)


def cum_return(signal: pd.Series, ret: pd.Series) -> float:
    """Helper to get cumulative return."""
    return (1 + signal * ret).cumprod().iloc[-1] - 1


def debug_hof(csv_path: str) -> None:
    price, returns = data_io.load_and_audit(csv_path, Path("plots"))
    X, y = features.build_features(price)
    (train_X, train_y), (val_X, val_y), (test_X, test_y) = train_val_test_split(X, y)

    # Rerun GA (same seed is fixed inside strategy_ga) to regenerate HOF
    hof, pset, feat_cols = evolve(train_X, train_y, val_X, val_y)
    compile_fn = lambda ind: compile_individual(ind, pset, feat_cols)

    print("==== HOF Cumulative Returns ====")
    for idx, ind in enumerate(hof):
        sig_train = compile_fn(ind)(train_X)
        sig_val = compile_fn(ind)(val_X)
        sig_test = compile_fn(ind)(test_X)
        print(
            f"[{idx}] Train {cum_return(sig_train, train_y):.2%} | "
            f"Val {cum_return(sig_val, val_y):.2%} | "
            f"Test {cum_return(sig_test, test_y):.2%}"
        )
        # Deep dive on the top individual
        if idx == 0:
            print("--- Threshold sweep for top individual ---")
            func = gp.compile(ind, pset)

            def build_signal(df: pd.DataFrame, thr: float) -> pd.Series:
                raw = np.asarray([func(*row) for row in df[feat_cols].values])
                z = (raw - raw.mean()) / (raw.std() + 1e-8)
                return pd.Series((z > thr).astype(float), index=df.index)

            for thr in (0.0, 0.25, 0.5):
                s_train = build_signal(train_X, thr)
                s_val = build_signal(val_X, thr)
                s_test = build_signal(test_X, thr)
                print(
                    f"thr={thr:>4}: Train {cum_return(s_train, train_y):6.2%} | "
                    f"Val {cum_return(s_val, val_y):6.2%} | "
                    f"Test {cum_return(s_test, test_y):6.2%} | "
                    f"signal counts test {s_test.value_counts().to_dict()}"
                )

            # Raw diagnostics once at thr=0.5 (original)
            raw_test = np.asarray([func(*row) for row in test_X[feat_cols].values])
            mu, sigma = raw_test.mean(), raw_test.std()
            z = (raw_test - mu) / (sigma + 1e-8)
            print("Raw mean/std:", mu, sigma)
            print("First 20 raw:", raw_test[:20])
            print("First 20 z:", z[:20])
            print("Raw GP expression:", ind)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default="genetic/monthly_all.csv")
    args = parser.parse_args()
    debug_hof(args.csv)
