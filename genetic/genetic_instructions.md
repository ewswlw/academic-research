# GA‑Driven Long‑Only Strategy for `cad_ig_er_index`

- Act like an expert in algo trading/stats
- everything must be done within my poetry environment

## 0. Scope & Success Criteria
- everything should be in the same directory

- **Instrument**: `cad_ig_er_index`
- **Data**: monthly observations, no extensions or external data
- **Position Space**: Binary only (0% cash or 100% long)
- **Constraints**: 
  - No shorting
  - No leverage
  - Rebalance only at month-end
- **Objective**: Achieve **≥ 80% cumulative return** over full sample
- **Secondary Goals**: 
  - Maximise CAGR
  - Minimise Max Drawdown
  - Never compromise on 80% total return requirement
- **Assumptions**:
  - No transaction costs
  - Flat months = 0% return

---

## 1. Environment Setup (Python 3)

- all required libraries should be in my poetry env, if not poetry install them.

- Use:
  - `pandas` for I/O
  - `numpy` for vectorized calculations
  - `deap` or `pygad` for GA
  - `gplearn` for GP symbolic expression trees
- Coding style: PEP‑8
- Include: Docstrings, type hints

---

## 2. Data Ingestion & Audit

- Load `monthly_all.csv`
- Ensure index is a **monotonic monthly `DatetimeIndex`**
- Check:
  - Exactly 91 rows
  - Drop NaNs or duplicates
- Visual sanity checks:
  - Raw price plot
  - Log return plot

---

## 3. Target Engineering

- **Monthly log return**:
  
  ```math
  r_t = \ln\left(\frac{P_t}{P_{t-1}}\right)
  ```

- **Cumulative strategy return**:

  ```math
  R_{cum} = \prod_{t=1}^T \left(1 + r_t \cdot pos_t\right) - 1
  ```

- Target for GA fitness: equity curve of the candidate rule must achieve **R_cum ≥ 0.80**

---

## 4. Feature Engineering Blueprint

### Price-based Features:
- Momentum: \( \frac{P_t}{P_{t-k}} - 1 \) for \( k = 1 \ldots 10 \)
- Moving averages:
  - SMA_k, EMA_k
  - Price/MA - 1
- MA crossovers:
  - SMA(2–5) vs SMA(6–10)
- Volatility:
  - Rolling σ, CV = σ / |mean|
- Z-scores:
  - Z-score of return
  - Z-score of price change

### Regime/Anomaly Flags:
- Rolling Sharpe (mean/σ)
- Volatility regime (e.g. 2-state dummy via MS model)

### Allowed Nonlinear Transforms:
- `np.log`, `np.exp`, `np.tanh`, `np.abs`, `np.sign`, conditional step functions

### Optional:
- PCA on standardized features, retain ≤ 3 components

> **All features must be lagged by 1 month** to eliminate lookahead bias

---

## 5. Rule Representation

- **Boolean logic rules** (via GP): Output is {0, 1}
- **Continuous score rules**:
  - Compute score \( S_t \)
  - Enter long if \( S_t > \theta \)

### GP Primitive Set:
- Operations: `add`, `sub`, `mul`, `div`, `log`, `sqrt`, `tanh`, `gt`, `lt`, `and`, `or`, `if`
- Terminals: feature names, constants

---

## 6. Genetic Algorithm Configuration

- **Population**: ~300
- **Generations**: ~200 (early stop if R_cum ≥ 0.8 on validation)
- **Selection**: Tournament (size = 5)
- **Elitism**: 5%
- **Operators**:
  - Crossover: 0.6
  - Mutation: 0.3
  - Reproduction: 0.1

### Bloat Control:
- Max tree depth: 5
- Parsimony pressure (penalize tree size)

### Fitness Function:

```math
\text{score} = 
\begin{cases} 
-∞ & \text{if } R_{cum} < 0.8 \\
0.7 \times \text{CAGR} - 0.3 \times \text{MaxDD} & \text{otherwise}
\end{cases}
```

> Note: MaxDD is negative so lower drawdown improves the score.

---

## 7. Train / Validation / Test Protocol

- **Split**:
  - Train: 60% (~55 months)
  - Validation: 20% (~18 months)
  - Test: 20% (~18 months)

- **Workflow**:
  - Optimize on training
  - Tune / early-stop using validation
  - Freeze top-N rules (e.g., N = 10), evaluate on test

- **Pass criteria**:
  - Train return ≥ 80%
  - Test return ≥ 40% (≥ 50% of train as guideline)

- If none pass, return best validation rule, label as *sub-par*

---

## 8. Robustness & Over-fit Checks

- **White's Reality Check** / **Deflated Sharpe**
- **Monte Carlo**: 500 runs of monthly block shuffling → test equity curve should land in **top 10%**
- **Perturbation Test**:
  - Mutate best tree 50×
  - New equity curves must stay within ±20% of original

---

## 9. Post‑Processing

- Simplify rules (algebraic simplification, prune dead branches)
- Ensemble similar rules using voting
- Final outputs:
  - Final equity curve
  - Monthly return series
  - Metrics table: CAGR, Total Return, MaxDD, Sharpe, Calmar

---

## 10. Deliverables

- `strategy_ga.py`: complete pipeline
- `cad_ig_er_report.ipynb`: interactive notebook with plots + commentary
- **Saved Plots (make them interactive in plotly**:
  - Price vs Strategy Equity Curve
  - Drawdown Chart
  - Rolling 12M Return
  - Feature Importance Heatmap
- `README.md`: setup, commands, interpretation
- **Reproducibility**:
  - All random seeds fixed and printed at script start

---

## 11. Run‑Time Interaction Pattern for LLM

At every major step:

1. **Explain** upcoming task in 1–2 sentences
2. **Present** the code snippet
3. If writing to disk, **list created/modified files**
4. **Show** key intermediate stats
5. **Ask** for confirmation only if there's a design tradeoff
6. **Document** every assumption & decision

> Even if 80% return is achieved early, **do not skip** validation or robustness steps.
