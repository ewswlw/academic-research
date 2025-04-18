"""
Fetch monthly G-spreads for all current members of I05510CA Index (Canadian Corporate Bond Index).
- Uses xbbg to fetch index members and G_SPREAD time series.
- Returns a DataFrame: rows = month-end (datetime index), columns = bond names, values = G-spread.
- Bonds with no data are skipped (with logging).
- Standalone script, robust error handling and inline comments.
"""

import sys
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
from xbbg import blp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def fetch_current_members(index_ticker):
    """Fetch current members with ID_CUSIP for Bloomberg ticker construction."""
    try:
        # Fetch ID_CUSIP for each member
        members = blp.bds(index_ticker, 'INDX_MEMBERS', FLDS=['ID_CUSIP'])
        print("\n[DEBUG] Members DataFrame columns:", list(members.columns))
        print("[DEBUG] First 10 rows:\n", members.head(10))
        if members is None or members.empty or 'ID_CUSIP' not in members.columns:
            logging.error(f"No ID_CUSIP data found for index: {index_ticker}")
            return []
        # Build (ticker, name) pairs where ticker is 'CUSIP Corp' and name is CUSIP
        result = []
        for code in members['ID_CUSIP']:
            if pd.isnull(code):
                continue
            ticker = f"{code} Corp"
            result.append((ticker, code))
        return result
    except Exception as e:
        logging.error(f"Error fetching members: {e}", exc_info=True)
        return []

def fetch_g_spreads(members, start_date, end_date):
    """Fetch monthly G_SPREAD_MID_CALC for each bond in members list."""
    gs_data = {}
    for ticker, name in members:
        try:
            df = blp.bdh(
                tickers=ticker,
                flds='G_SPREAD_MID_CALC',
                start_date=start_date,
                end_date=end_date,
                freq='monthly'
            )
            if df is None or df.empty or 'G_SPREAD_MID_CALC' not in df.columns:
                logging.warning(f"No G_SPREAD_MID_CALC data for {name} ({ticker}) - skipping.")
                continue
            # Use code as column label
            gs_data[name] = df['G_SPREAD_MID_CALC']
            logging.info(f"Fetched G_SPREAD_MID_CALC for {name} ({ticker})")
        except Exception as e:
            logging.warning(f"Failed for {name} ({ticker}): {e}")
    # Combine into DataFrame
    gs_df = pd.DataFrame(gs_data)
    gs_df.index = pd.to_datetime(gs_df.index)
    gs_df.sort_index(inplace=True)
    return gs_df

def main():
    index_ticker = 'I05510CA Index'
    end_date = datetime.today()
    start_date = end_date - relativedelta(years=3)
    logging.info(f"Fetching current members of {index_ticker}")
    members = fetch_current_members(index_ticker)
    logging.info(f"Found {len(members)} members. Fetching G_SPREADs...")
    gs_df = fetch_g_spreads(members, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    logging.info(f"Final DataFrame shape: {gs_df.shape}")
    print(gs_df.head())
    # Optionally: gs_df.to_csv('g_spreads_current_members.csv')

if __name__ == "__main__":
    main()
