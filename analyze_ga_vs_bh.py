import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. Load data
signals = pd.read_csv('genetic/ga_signals.csv', index_col=0, squeeze=True)
prices = pd.read_csv('genetic/monthly_all.csv', parse_dates=['Date'], index_col='Date')
price_series = prices['cad_ig_er_index']

# 2. Align signals with price data (fill missing with 0 = no position)
signals = signals.reindex(price_series.index).fillna(0)

# 3. Compute returns and equity curves
returns = price_series.pct_change().fillna(0)
ga_returns = returns * signals
ga_equity = (1 + ga_returns).cumprod()
bh_equity = (1 + returns).cumprod()

# 4. Extensive statistics
def compute_all_stats(equity, returns):
    stats = {}
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
    # Add more as needed...
    return stats

ga_stats = compute_all_stats(ga_equity, ga_returns)
bh_stats = compute_all_stats(bh_equity, returns)

# 5. Trade statistics (if signal is 0/1 or -1/1)
def compute_trade_stats(signal, returns):
    stats = {}
    trades = signal.diff().abs().sum() / 2
    stats['Number of Trades'] = trades
    # Win/loss stats, streaks, average/median win/loss, etc.
    # TODO: implement detailed trade stats
    return stats

# 6. Rolling stats (example: 12-month rolling Sharpe)
rolling_sharpe = ga_returns.rolling(12).mean() / ga_returns.rolling(12).std() * np.sqrt(12)

# 7. Output
print('==== Summary Statistics ====')
print(pd.DataFrame([ga_stats, bh_stats], index=['GA Strategy', 'Buy & Hold']))
print('==== Trade Statistics ====')
# print(pd.DataFrame([compute_trade_stats(...), ...]))
print('==== Rolling Sharpe (last 24 months) ====')
print(rolling_sharpe.tail(24))

# 8. Visualization (optional)
plt.figure(figsize=(10,6))
plt.plot(ga_equity, label='GA Strategy')
plt.plot(bh_equity, label='Buy & Hold')
plt.legend()
plt.title('Equity Curves')
plt.show()

# Add more plots as needed...

# Debugging: print key intermediate values
print('First few rows of signals:', signals.head())
print('Signal value counts:', signals.value_counts())
print('First few rows of GA returns:', ga_returns.head())
