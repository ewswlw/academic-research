"""
replicate_ep_spread_strategy.py

Replicates the E/P spread vs. T-bill yield market timing strategy from
"Timing is Everything" using xbbg and vectorbt, with full logging, error handling,
and detailed comments for reproducibility.

Requirements:
- xbbg
- vectorbt
- pandas, numpy
- Bloomberg Terminal access

Run with: poetry run python replicate_ep_spread_strategy.py
"""
import logging
import pandas as pd
import numpy as np
from xbbg import blp
import vectorbt as vbt
from datetime import datetime

# Set up logging for reproducibility and debugging
logging.basicConfig(
    filename='replicate_ep_spread_strategy.log',
    level=logging.INFO,

    
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    # --- 1. Download Data ---
    start_date = '1990-01-01'  # Bloomberg EPS data usually starts late 80s/early 90s
    end_date = datetime.today().strftime('%Y-%m-%d')
    logging.info(f"Fetching data from {start_date} to {end_date}")

    # S&P 500 Index (monthly close)
    try:
        px_raw = blp.bdh('SPX Index', 'PX_LAST', start_date, end_date, Per='M')
        print("Raw SPX DataFrame:")
        print(px_raw.head(10))
        print("SPX DataFrame columns:", list(px_raw.columns))
        logging.info(f"Raw SPX DataFrame head:\n{px_raw.head()}\nColumns: {list(px_raw.columns)}")
        # Handle MultiIndex columns
        if ('SPX Index', 'PX_LAST') in px_raw.columns:
            px = px_raw[('SPX Index', 'PX_LAST')].rename('SPX')
        elif 'PX_LAST' in px_raw.columns:
            px = px_raw['PX_LAST'].rename('SPX')
        else:
            logging.error(f"Neither 'PX_LAST' nor ('SPX Index', 'PX_LAST') found in columns: {list(px_raw.columns)}")
            print(f"ERROR: Neither 'PX_LAST' nor ('SPX Index', 'PX_LAST') found in columns: {list(px_raw.columns)}")
            return
        logging.info(f"SPX data: {px.index[0]} to {px.index[-1]}, n={len(px)}")
    except Exception as e:
        logging.error(f"Failed to fetch SPX Index: {e}")
        print(f"ERROR: Failed to fetch SPX Index: {e}")
        return

    # S&P 500 Trailing 12M EPS (BEST_EPS)
    try:
        eps_raw = blp.bdh('SPX Index', 'BEST_EPS', start_date, end_date, Per='M')
        print("Raw EPS DataFrame:")
        print(eps_raw.head(10))
        print("EPS DataFrame columns:", list(eps_raw.columns))
        logging.info(f"Raw EPS DataFrame head:\n{eps_raw.head()}\nColumns: {list(eps_raw.columns)}")
        if ('SPX Index', 'BEST_EPS') in eps_raw.columns:
            eps = eps_raw[('SPX Index', 'BEST_EPS')].rename('EPS')
        elif 'BEST_EPS' in eps_raw.columns:
            eps = eps_raw['BEST_EPS'].rename('EPS')
        else:
            logging.error(f"Neither 'BEST_EPS' nor ('SPX Index', 'BEST_EPS') found in columns: {list(eps_raw.columns)}")
            print(f"ERROR: Neither 'BEST_EPS' nor ('SPX Index', 'BEST_EPS') found in columns: {list(eps_raw.columns)}")
            return
        logging.info(f"EPS data: {eps.index[0]} to {eps.index[-1]}, n={len(eps)}")
    except Exception as e:
        logging.error(f"Failed to fetch SPX EPS: {e}")
        print(f"ERROR: Failed to fetch SPX EPS: {e}")
        return

    # 3M US Treasury Bill Yield (Try multiple tickers/fields)
    tbill = None
    tbill_sources = [
        # (ticker, field, divisor, description)
        ('USGG3M Index', 'YLD_YTM_MID', 100, 'USGG3M Index, YLD_YTM_MID (original)'),
        ('US0003M Index', 'PX_LAST', 100, 'US0003M Index, PX_LAST (3M LIBOR proxy)'),
        ('FDTR Index', 'PX_LAST', 100, 'FDTR Index, PX_LAST (Fed Funds Target Rate)')
    ]
    for ticker, field, divisor, desc in tbill_sources:
        try:
            tbill_raw = blp.bdh(ticker, field, start_date, end_date, Per='M')
            print(f"Raw T-bill DataFrame [{desc}]:")
            print(tbill_raw.head(10))
            print(f"T-bill DataFrame columns: {list(tbill_raw.columns)}")
            logging.info(f"Raw T-bill DataFrame [{desc}] head:\n{tbill_raw.head()}\nColumns: {list(tbill_raw.columns)}")
            if (ticker, field) in tbill_raw.columns:
                tbill_candidate = tbill_raw[(ticker, field)].rename('TBill') / divisor
            elif field in tbill_raw.columns:
                tbill_candidate = tbill_raw[field].rename('TBill') / divisor
            else:
                continue
            if not tbill_candidate.dropna().empty:
                tbill = tbill_candidate
                logging.info(f"T-bill data [{desc}]: {tbill.index[0]} to {tbill.index[-1]}, n={len(tbill)}")
                print(f"Selected T-bill source: {desc}")
                break
        except Exception as e:
            logging.warning(f"Failed to fetch {desc}: {e}")
            print(f"WARNING: Failed to fetch {desc}: {e}")
    if tbill is None or tbill.dropna().empty:
        logging.error("Failed to fetch any valid 3M T-bill or proxy data. Please check tickers/fields or download manually.")
        print("ERROR: Failed to fetch any valid 3M T-bill or proxy data. Please check tickers/fields or download manually.")
        return

    # --- 2. Align Data ---
    df = pd.concat([px, eps, tbill], axis=1)
    df = df.dropna()
    logging.info(f"Aligned data shape: {df.shape}, head:\n{df.head()}")
    print(f"Data aligned from {df.index[0]} to {df.index[-1]} ({len(df)} months)")

    # --- 3. Signal Construction ---
    df['EP'] = df['EPS'] / df['SPX']  # Earnings/Price (annualized)
    df['Spread'] = df['EP'] - df['TBill']
    df['Signal'] = np.where(df['Spread'] > 0, 1, 0)  # 1=equity, 0=cash
    logging.info(f"Signal summary:\n{df['Signal'].value_counts()}")
    print(f"Signal distribution: {df['Signal'].value_counts().to_dict()}")

    # --- 4. Return Series ---
    df['SPX_ret'] = df['SPX'].pct_change().shift(-1)  # Forward return for next month
    df['TBill_ret'] = df['TBill'] / 12  # Approximate monthly yield
    df = df.dropna()

    # --- 5. Strategy Returns ---
    df['Strategy_ret'] = df['Signal'] * df['SPX_ret'] + (1 - df['Signal']) * df['TBill_ret']

    # --- 6. Backtest with vectorbt ---
    # --- 4. Backtest E/P Spread Strategy ---
    pf = vbt.Portfolio.from_orders(
        close=df['SPX'],
        size=df['Signal'].diff().fillna(df['Signal']),
        direction='longonly',
        cash_sharing=True,
        fees=0.0,
        init_cash=1.0
    )
    stats_ep = pf.stats()
    print("\n--- vectorbt .stats() (E/P Spread Strategy) ---")
    print(stats_ep)
    stats_ep.to_csv('ep_spread_stats.csv')
    print("E/P Spread stats saved to ep_spread_stats.csv")

    # --- 5. Buy-and-Hold Comparison ---
    pf_bh = vbt.Portfolio.from_orders(
        close=df['SPX'],
        size=1.0,  # always fully invested
        direction='longonly',
        cash_sharing=True,
        fees=0.0,
        init_cash=1.0
    )
    stats_bh = pf_bh.stats()
    print("\n--- vectorbt .stats() (Buy-and-Hold) ---")
    print(stats_bh)
    stats_bh.to_csv('buy_and_hold_stats.csv')
    print("Buy-and-Hold stats saved to buy_and_hold_stats.csv")

    # --- 7. Save Results ---
    df.to_csv('ep_spread_strategy_data.csv')
    logging.info("Saved data to ep_spread_strategy_data.csv")

if __name__ == "__main__":
    main()
