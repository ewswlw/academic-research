"""
S&P 500 Regime Timing Strategy
- Detects bull, bear, and neutral regimes using k-means clustering on rolling window features
- Backtests a regime-timing strategy vs. buy-and-hold
- Outputs stats, tables, and interactive Plotly visuals

Dependencies: xbbg, pandas, numpy, scikit-learn, plotly
"""
import os
import sys
import logging
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# --- 1. Download SPX Daily Data ---
try:
    from xbbg import blp
except ImportError:
    logging.error("xbbg not installed. Please install with 'poetry add xbbg'.")
    sys.exit(1)

START_DATE = '1940-01-01'
END_DATE = datetime.today().strftime('%Y-%m-%d')
TICKER = 'SPX Index'
FIELD = 'PX_LAST'

logging.info(f"Fetching {TICKER} daily close from {START_DATE} to {END_DATE}...")
df = blp.bdh(TICKER, FIELD, START_DATE, END_DATE, Per='D')
if df.empty:
    logging.error("No data returned from Bloomberg/xbbg.")
    sys.exit(2)
df = df.droplevel(0, axis=1) if isinstance(df.columns, pd.MultiIndex) else df

# --- 2. Feature Engineering ---
df['logret'] = np.log(df[FIELD]).diff()
df = df.dropna()

# Add advanced rolling features
from scipy.stats import skew, kurtosis
window_feat = 60  # default for feature calculation

def compute_all_features(series, window):
    X, dates = [], []
    for i in range(window, len(series)):
        window_data = series.iloc[i-window:i]
        feat = [
            window_data.mean(),
            window_data.std(),
            np.sqrt((window_data**2).mean()),  # realized vol
            skew(window_data),
            kurtosis(window_data),
            window_data.sum(),  # momentum
        ]
        X.append(feat)
        dates.append(series.index[i])
    return np.array(X), dates

from sklearn.preprocessing import StandardScaler

# --- 3. Rolling Window Feature Matrix ---
def compute_features(series, window):
    X = []
    dates = []
    for i in range(window, len(series)):
        window_data = series.iloc[i-window:i]
        mean = window_data.mean()
        std = window_data.std()
        X.append([mean, std])
        dates.append(series.index[i])
    return np.array(X), dates

# --- 4. Grid Search for Optimal Window ---
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

best_cagr = -np.inf
best_window = None
best_labels = None
best_dates = None
best_X = None
window_grid = list(range(40, 251, 10))

logging.info("Optimizing window size for max CAGR...")
for window in window_grid:
    X, dates = compute_all_features(df['logret'], window)
    if len(X) < 100:
        continue
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=3, n_init=20, random_state=42)
    labels = kmeans.fit_predict(X_scaled)
    cluster_means = [np.mean(df['logret'].iloc[window:][labels==k]) for k in range(3)]
    regime_order = np.argsort(cluster_means)[::-1]
    ordered_labels = np.zeros_like(labels)
    for i, k in enumerate(regime_order):
        ordered_labels[labels==k] = i
    # Regime persistence filter
    persistence = 5
    filtered_labels = ordered_labels.copy()
    for j in range(persistence, len(filtered_labels)):
        if not np.all(filtered_labels[j-persistence:j] == filtered_labels[j]):
            filtered_labels[j] = filtered_labels[j-1]
    # Simulate strategy
    strat_returns = np.zeros(len(df))
    prev_regime = None
    in_market = False
    for idx, (date, regime) in enumerate(zip(dates, filtered_labels)):
        i = df.index.get_loc(date)
        if regime == 0:  # bull
            strat_returns[i] = df['logret'].iloc[i]
        elif regime == 1:  # neutral (partial exposure)
            strat_returns[i] = 0.5 * df['logret'].iloc[i]
        else:  # bear
            strat_returns[i] = 0
        prev_regime = regime
    strat_cum = np.cumprod(1+strat_returns)
    years = (df.index[-1] - df.index[0]).days / 365.25
    cagr = strat_cum[-1]**(1/years) - 1
    if cagr > best_cagr:
        best_cagr = cagr
        best_window = window
        best_labels = filtered_labels.copy()
        best_dates = dates.copy()
        best_X = X.copy()

logging.info(f"Best window size: {best_window}, max CAGR: {best_cagr:.2%}")

# --- 5. Final Regime Assignment ---
X, dates = compute_all_features(df['logret'], best_window)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
kmeans = KMeans(n_clusters=3, n_init=20, random_state=42)
labels = kmeans.fit_predict(X_scaled)
cluster_means = [np.mean(df['logret'].iloc[best_window:][labels==k]) for k in range(3)]
regime_order = np.argsort(cluster_means)[::-1]
ordered_labels = np.zeros_like(labels)
for i, k in enumerate(regime_order):
    ordered_labels[labels==k] = i
# Regime persistence filter
persistence = 5
filtered_labels = ordered_labels.copy()
for j in range(persistence, len(filtered_labels)):
    if not np.all(filtered_labels[j-persistence:j] == filtered_labels[j]):
        filtered_labels[j] = filtered_labels[j-1]
df['regime'] = np.nan
df.loc[dates, 'regime'] = filtered_labels

# --- DEBUGGING: Regime assignment ---
regime_counts = pd.Series(filtered_labels).value_counts()
print("\nDEBUG: Regime counts after filtering:")
print(regime_counts)
print("\nDEBUG: First 100 regime assignments:")
print(filtered_labels[:100])

# --- 6. Backtest Strategies ---
def backtest(df, regime_col, in_regime=[0,1], neutral_weight=0.5, tc_per_switch=0.0005):
    strat_returns = np.zeros(len(df))
    prev_regime = None
    trades = 0
    time_in_market = 0
    trade_log = []
    last_trade_idx = None
    last_trade_regime = None
    for i, regime in enumerate(df[regime_col]):
        if np.isnan(regime):
            strat_returns[i] = 0
            continue
        if regime == 0:
            strat_returns[i] = df['logret'].iloc[i]
            time_in_market += 1
        elif regime == 1:
            strat_returns[i] = neutral_weight * df['logret'].iloc[i]
            time_in_market += neutral_weight
        else:
            strat_returns[i] = 0
        # Transaction cost and trade log
        if prev_regime is not None and regime != prev_regime:
            strat_returns[i] -= tc_per_switch
            trades += 1
            # Log trade: (entry idx, exit idx, regime, pnl, holding period)
            if last_trade_idx is not None:
                trade_log.append({
                    'EntryIdx': last_trade_idx,
                    'ExitIdx': i,
                    'Regime': last_trade_regime,
                    'PnL': np.exp(np.sum(df['logret'].iloc[last_trade_idx:i]))-1,
                    'HoldingPeriod': i-last_trade_idx
                })
            last_trade_idx = i
            last_trade_regime = regime
        prev_regime = regime
    # Log last trade if open
    if last_trade_idx is not None and last_trade_idx < len(df)-1:
        trade_log.append({
            'EntryIdx': last_trade_idx,
            'ExitIdx': len(df)-1,
            'Regime': last_trade_regime,
            'PnL': np.exp(np.sum(df['logret'].iloc[last_trade_idx:]))-1,
            'HoldingPeriod': len(df)-1-last_trade_idx
        })
    strat_cum = np.cumprod(1+strat_returns)
    pct_time_in_market = time_in_market / len(df)
    return strat_returns, strat_cum, trades, pct_time_in_market, trade_log

strat_returns, strat_cum, trades, pct_time_in_market, trade_log = backtest(df, 'regime')
bh_returns = df['logret'].values
bh_cum = np.cumprod(1+bh_returns)

# --- DEBUGGING: Trade log and regime transitions ---
print("\nDEBUG: Trade log (first 10 entries):")
print(pd.DataFrame(trade_log).head(10))

# Regime duration stats
df['regime_shift'] = df['regime'].ne(df['regime'].shift())
df['regime_block'] = df['regime_shift'].cumsum()
regime_durations = df.groupby(['regime','regime_block']).size().groupby('regime').describe()
print("\nRegime Duration Stats:")
print(regime_durations)

# Drawdown table
def drawdown_table(equity):
    roll_max = np.maximum.accumulate(equity)
    dd = (roll_max - equity) / roll_max
    dd_start = np.where((dd[:-1] == 0) & (dd[1:] > 0))[0] + 1
    dd_end = np.where((dd[:-1] > 0) & (dd[1:] == 0))[0] + 1
    dd_depth = [dd[s:e].max() for s,e in zip(dd_start, dd_end)] if len(dd_start) and len(dd_end) else []
    return pd.DataFrame({'Start': dd_start, 'End': dd_end, 'Depth': dd_depth})
dd_tbl = drawdown_table(strat_cum)
print("\nDrawdown Table (first 10):")
print(dd_tbl.head(10))
dd_tbl.to_csv('drawdown_table.csv')

# --- 7. Stats & Tables ---
def max_drawdown(equity):
    roll_max = np.maximum.accumulate(equity)
    drawdown = (roll_max - equity) / roll_max
    return np.max(drawdown), np.argmax(drawdown), np.argmin(drawdown)

def perf_stats(returns, cum, name, trades, pct_time, trade_log):
    years = (df.index[-1] - df.index[0]).days / 365.25
    total_return = cum[-1] - 1
    cagr = cum[-1]**(1/years) - 1
    vol = np.std(returns)*np.sqrt(252)
    sharpe = np.mean(returns)/np.std(returns)*np.sqrt(252)
    sortino = np.mean(returns)/np.std(returns[returns<0])*np.sqrt(252) if np.any(returns<0) else np.nan
    mdd, dd_peak, dd_trough = max_drawdown(cum)
    calmar = cagr/mdd if mdd > 0 else np.nan
    mar = total_return/np.sum(returns[returns<0]) if np.any(returns<0) else np.nan
    skew_ = skew(returns)
    kurt_ = kurtosis(returns)
    win_rate = np.mean(returns>0)
    avg_trade = np.mean(returns[returns!=0])
    longest_dd = (dd_trough - dd_peak) if dd_trough > dd_peak else 0
    avg_dd = np.mean((np.maximum.accumulate(cum)-cum)[cum<np.maximum.accumulate(cum)])
    avg_holding = np.mean([t['HoldingPeriod'] for t in trade_log]) if trade_log else 0
    avg_pnl = np.mean([t['PnL'] for t in trade_log]) if trade_log else 0
    return {
        'CAGR': cagr, 'Total Return': total_return, 'Volatility': vol,
        'Sharpe': sharpe, 'Sortino': sortino, 'Max Drawdown': mdd,
        'Calmar': calmar, 'MAR': mar, 'Num Trades': trades,
        '% Time in Market': pct_time, 'Win Rate': win_rate, 'Avg Trade': avg_trade,
        'Longest DD': longest_dd, 'Avg DD': avg_dd, 'Skew': skew_, 'Kurtosis': kurt_,
        'Avg Holding Period': avg_holding, 'Avg Trade PnL': avg_pnl
    }

strat_stats = perf_stats(strat_returns, strat_cum, 'Regime Timing', trades, pct_time_in_market, trade_log)
bh_stats = perf_stats(bh_returns, bh_cum, 'Buy & Hold', 0, 1.0, [])

import pandas as pd
stats_df = pd.DataFrame([strat_stats, bh_stats], index=['Regime Timing', 'Buy & Hold']).T
print("\nPerformance Comparison Table:")
print(stats_df)
stats_df.to_csv('performance_comparison.csv')

# Regime transition matrix
from collections import Counter
regimes = df['regime'].dropna().astype(int)
transitions = Counter(zip(regimes[:-1], regimes[1:]))
trans_mat = np.zeros((3,3))
for (i,j), cnt in transitions.items():
    trans_mat[i,j] = cnt
trans_mat = trans_mat / trans_mat.sum(axis=1, keepdims=True)
print("\nRegime Transition Matrix (rows: from, cols: to):")
print(trans_mat)
pd.DataFrame(trans_mat).to_csv('regime_transition_matrix.csv')

# --- 8. Interactive Plotly Visuals ---
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                   subplot_titles=("Equity Curves", "Regime Assignment"))
fig.add_trace(go.Scatter(x=df.index, y=bh_cum, name='Buy & Hold', line=dict(color='blue')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=strat_cum, name='Regime Timing', line=dict(color='green')), row=1, col=1)
regime_colors = {0:'green', 1:'orange', 2:'red'}
regime_names = {0:'Bull', 1:'Neutral', 2:'Bear'}
regime_series = df['regime'].copy()
for k in [0,1,2]:
    mask = (regime_series==k)
    fig.add_trace(go.Scatter(x=df.index[mask], y=[k+1]*mask.sum(),
                             mode='markers', marker=dict(color=regime_colors[k]),
                             name=regime_names[k], showlegend=False), row=2, col=1)
fig.update_yaxes(title_text="Cumulative Return", row=1, col=1)
fig.update_yaxes(title_text="Regime (Bull=3, Neutral=2, Bear=1)", row=2, col=1)
fig.update_layout(title="S&P 500 Regime Timing Strategy vs. Buy & Hold",
                  height=800)
fig.show()

# --- 9. Save Outputs ---
outdir = os.path.dirname(os.path.abspath(__file__))
df.to_csv(os.path.join(outdir, 'spx_regime_timing_results.csv'))
fig.write_html(os.path.join(outdir, 'spx_regime_timing_equity.html'))

print("\nAll results saved to:")
print(f"  {os.path.join(outdir, 'spx_regime_timing_results.csv')}")
print(f"  {os.path.join(outdir, 'spx_regime_timing_equity.html')}")

logging.info("Script completed successfully.")
