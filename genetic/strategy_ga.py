"""
End‑to‑end GA pipeline.
Run: `python strategy_ga.py --csv monthly_all.csv`
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from deap import base, creator, gp, tools, algorithms

import data_io
import features
import metrics
import math

SEED = 42
random.seed(SEED)
np.random.seed(SEED)


def train_val_test_split(
    df: pd.DataFrame, y: pd.Series
) -> Tuple[Tuple[pd.DataFrame, pd.Series], ...]:
    n = len(df)
    train_end = int(n * 0.6)
    val_end = int(n * 0.8)
    return (
        (df.iloc[:train_end], y.iloc[:train_end]),
        (df.iloc[train_end:val_end], y.iloc[train_end:val_end]),
        (df.iloc[val_end:], y.iloc[val_end:]),
    )


def make_primitives(feature_names: List[str]) -> gp.PrimitiveSetTyped:
    pset = gp.PrimitiveSet("MAIN", len(feature_names), prefix="X")
    # arithmetic operations with explicit names
    pset.addPrimitive(lambda a, b: a + b, 2, name="add")
    pset.addPrimitive(lambda a, b: a - b, 2, name="sub")
    pset.addPrimitive(lambda a, b: a * b, 2, name="mul")
    pset.addPrimitive(lambda a, b: a / b if b != 0 else 0.0, 2, name="div_safe")
    # safer division alternatives
    pset.addPrimitive(protected_div, 2, name="div_prot")
    # unary math
    pset.addPrimitive(np.tanh, 1, name="tanh")
    pset.addPrimitive(np.abs, 1, name="abs")
    pset.addPrimitive(np.sign, 1, name="sign")
    pset.addPrimitive(protected_sqrt, 1, name="sqrt_safe")
    pset.addPrimitive(clip10, 1, name="clip10")
    # smooth logistic activation
    pset.addPrimitive(sigmoid_safe, 1, name="sigmoid")
    # Use protected log1p to avoid NaNs during evolution
    pset.addPrimitive(protected_log, 1, name="log1p_safe")
    # terminals
    for i, name in enumerate(feature_names):
        pset.renameArguments(**{f"X{i}": name})
    pset.addEphemeralConstant("rand", lambda: random.random())
    return pset


def protected_log(x: float) -> float:
    """Safe np.log1p that avoids invalid values and returns 0.0 when undefined.

    Args:
        x: Input value.

    Returns:
        float: np.log1p(x) if x > -0.999 else 0.0.
    """
    try:
        if x <= -0.999:
            return 0.0
        return math.log1p(x)
    except Exception:
        return 0.0


def protected_div(x: float, y: float) -> float:
    """Division that avoids blow‑ups when the denominator is ~0."""
    try:
        return x / y if abs(y) > 1e-6 else 0.0
    except Exception:
        return 0.0


def protected_sqrt(x: float) -> float:
    """Always returns a non‑negative real sqrt value."""
    try:
        return math.sqrt(abs(x))
    except Exception:
        return 0.0


def clip10(x: float) -> float:
    """Clip values to the range [‑10, 10] to keep GP trees bounded."""
    try:
        return max(-10.0, min(10.0, x))
    except Exception:
        return 0.0


def sigmoid_safe(x: float) -> float:
    """Numerically stable sigmoid clipped via clip10."""
    try:
        return 1.0 / (1.0 + math.exp(-clip10(x)))
    except Exception:
        return 0.5


def compile_individual(ind, pset, feat_cols):
    """Compile a GP individual into a binary‑signal function.

    The raw GP expression is evaluated for each row, z‑scored, then we go long
    when the standardised value is above +0.5 (≈ top 30 %). This continuous
    mapping gives the GA gradient (many non‑zero signals) but still produces a
    binary {0,1} position series as required.
    """
    func = gp.compile(expr=ind, pset=pset)

    def signal(X: pd.DataFrame) -> pd.Series:
        raw = np.asarray([func(*row) for row in X[feat_cols].values], dtype=float)
        prob = 1.0 / (1.0 + np.exp(-np.clip(raw, -10, 10)))  # smooth 0‑1 mapping
        sig = (prob > 0.55).astype(float)  # long when prob > 55%
        return pd.Series(sig, index=X.index)

    return signal


def fitness_function(signal: pd.Series, returns: pd.Series) -> Tuple[float]:
    """Return‑aligned fitness: maximise cumulative return, penalise drawdown."""
    equity = (1 + returns * signal).cumprod()
    total_ret = equity.iloc[-1] - 1
    mdd = metrics.max_drawdown(returns * signal)

    if total_ret < 0.0:
        return (-1e9,)
    if total_ret < 0.30:
        return (-1000 * total_ret,)

    score = total_ret - 0.3 * mdd  # monotonic in return
    return (score,)


def evolve(train_X, train_y, val_X, val_y):
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

    feat_cols = train_X.columns.tolist()
    pset = make_primitives(feat_cols)
    toolbox = base.Toolbox()
    toolbox.register("expr", gp.genFull, pset=pset, min_=1, max_=3)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("compile", compile_individual, pset=pset, feat_cols=feat_cols)

    def eval_ind(ind):
        signal_fn = toolbox.compile(ind)
        sig_train = signal_fn(train_X)
        return fitness_function(sig_train, train_y)

    toolbox.register("evaluate", eval_ind)
    toolbox.register("select", tools.selTournament, tournsize=5)
    toolbox.register("mate", gp.cxOnePoint)
    toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr, pset=pset)
    toolbox.decorate("mate", gp.staticLimit(key=len, max_value=80))
    toolbox.decorate("mutate", gp.staticLimit(key=len, max_value=80))

    pop = toolbox.population(400)
    hof = tools.HallOfFame(10)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("max", np.max)
    stats.register("mean", np.mean)

    for gen in range(200):
        pop = algorithms.varAnd(pop, toolbox, cxpb=0.5, mutpb=0.4)
        fits = list(map(toolbox.evaluate, pop))
        for ind, fit in zip(pop, fits):
            ind.fitness.values = fit
        hof.update(pop)
        record = stats.compile(pop)
        print(f"Gen {gen:03d} | Max {record['max']:.4f} | Mean {record['mean']:.4f}")

        # early stop check
        best_ind = hof[0]
        signal_fn = toolbox.compile(best_ind)
        val_sig = signal_fn(val_X)
        val_total_ret = (1 + val_y * val_sig).cumprod().iloc[-1] - 1
        if val_total_ret >= 0.80:
            print("Early stop: validation cumulative return ≥ 0.8")
            break
    return hof, pset, feat_cols


def main(args):
    price, returns = data_io.load_and_audit(args.csv, Path("plots"))
    X, y = features.build_features(price)
    (train_X, train_y), (val_X, val_y), (test_X, test_y) = train_val_test_split(X, y)
    hof, pset, feat_cols = evolve(train_X, train_y, val_X, val_y)

    compile_fn = lambda ind: compile_individual(ind, pset, feat_cols)
    results = []
    for ind in hof:
        sig_test = compile_fn(ind)(test_X)
        eq = (1 + sig_test * test_y).cumprod()
        results.append(
            dict(
                total_return=eq.iloc[-1] - 1,
                cagr=metrics.cagr(sig_test * test_y),
                max_dd=metrics.max_drawdown(sig_test * test_y),
            )
        )
    pd.DataFrame(results).to_csv("ga_results.csv", index=False)
    print("Saved ga_results.csv")

    # === Save best GA strategy signals for downstream analysis ===
    # Use the best individual from the hall of fame (hof[0])
    best_ind = hof[0]
    signal_func = compile_fn(best_ind)
    signals = signal_func(test_X)
    signals.to_csv("genetic/ga_signals.csv")
    print("[INFO] Saved best GA strategy signals to genetic/ga_signals.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default="monthly_all.csv")
    main(parser.parse_args())
