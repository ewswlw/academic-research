"""
ga_search_modular.py

Modular genetic algorithm search for trading rule optimization.
Exports: run_ga_search(features: pd.DataFrame, ...) -> dict
"""
import pandas as pd
from typing import Dict, Any

import random
from rules import generate_random_rule
from backtest import backtest_rule
from analysis import compute_all_stats

N_POP = 30
N_GEN = 30
random_seed = 42


def run_ga_search(features: pd.DataFrame, price: pd.Series, n_pop: int = N_POP, n_gen: int = N_GEN, seed: int = random_seed) -> Dict[str, Any]:
    """
    Run the genetic algorithm search for trading rules.
    Args:
        features: Engineered features DataFrame.
        price: Price series for backtesting.
        n_pop: Population size.
        n_gen: Number of generations.
        seed: Random seed for reproducibility.
    Returns:
        dict: Results including best rule, stats, diagnostics, etc.
    """
    rng = random.Random(seed)
    population = []
    diagnostics = {"fitness": [], "rules": []}
    best_fitness = -float('inf')
    best_signal = None
    best_rule_text = None
    best_stats = None

    # Initialize population
    for _ in range(n_pop):
        signal, rule_text = generate_random_rule(features, rng)
        pf = backtest_rule(price, signal)
        returns = pf.total_return() if hasattr(pf, 'total_return') else pf.get_total_return()
        stats = compute_all_stats(pf.value(), pf.returns())
        sharpe = stats.get('Sharpe', 0)
        population.append({"signal": signal, "rule_text": rule_text, "stats": stats, "sharpe": sharpe})
        diagnostics["fitness"].append(sharpe)
        diagnostics["rules"].append(rule_text)
        if sharpe > best_fitness:
            best_fitness = sharpe
            best_signal = signal
            best_rule_text = rule_text
            best_stats = stats

    # Evolution loop (simple version: just keep best so far)
    for gen in range(1, n_gen + 1):
        print(f"[GA] Generation {gen}/{n_gen}")
        new_population = []
        for _ in range(n_pop):
            signal, rule_text = generate_random_rule(features, rng)
            pf = backtest_rule(price, signal)
            stats = compute_all_stats(pf.value(), pf.returns())
            sharpe = stats.get('Sharpe', 0)
            new_population.append({"signal": signal, "rule_text": rule_text, "stats": stats, "sharpe": sharpe})
            if sharpe > best_fitness:
                best_fitness = sharpe
                best_signal = signal
                best_rule_text = rule_text
                best_stats = stats
        population = new_population
        diagnostics["fitness"].append([ind["sharpe"] for ind in population])
        diagnostics["rules"].append([ind["rule_text"] for ind in population])
        print(f"[GA] Best Sharpe so far: {best_fitness:.2f}")

    return {
        "best_signal": best_signal,
        "best_rule_text": best_rule_text,
        "best_stats": best_stats,
        "diagnostics": diagnostics
    }
