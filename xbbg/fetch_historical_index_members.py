"""
Fetch historical monthly members of a Bloomberg index using xbbg, with built-in checks and debugging.
- Prints date, number of members, and first 5 tickers for each month-end over the last 5 years.
- Warns if members are unchanged from previous month (likely override not working).
- Handles errors and logs issues for reproducibility.
- Requires Bloomberg Terminal and API access.
"""

import sys
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from xbbg import blp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def get_month_ends(start, end):
    """Generate list of month-end dates between start and end (inclusive)."""
    dates = []
    current = start.replace(day=1)
    while current <= end:
        next_month = (current + relativedelta(months=1)).replace(day=1)
        last_day = next_month - timedelta(days=1)
        if last_day > end:
            last_day = end
        dates.append(last_day)
        current = next_month
    return dates

def fetch_historical_members(index_ticker, start_date, end_date):
    """
    Fetch and print historical members for each month-end, with debugging and checks.
    """
    dates = get_month_ends(start_date, end_date)
    prev_members_set = None
    for dt in dates:
        date_str = dt.strftime('%Y%m%d')
        try:
            # Attempt to fetch with END_DATE_OVERRIDE
            members = blp.bds(index_ticker, 'INDX_MEMBERS', overrides={'END_DATE_OVERRIDE': date_str})
            if members is None or members.empty:
                logging.warning(f"{date_str}: No members returned.")
                print(f"{date_str}: No members returned.")
                continue
            # Find ticker column
            ticker_col = None
            for col in members.columns:
                if 'member' in col.lower():
                    ticker_col = col
                    break
            tickers = members[ticker_col].tolist() if ticker_col else members.iloc[:,0].tolist()
            members_set = set(tickers)
            # Print debug info
            print(f"{date_str}: {len(tickers)} members. Sample: {tickers[:5]}")
            # Check for repeated membership sets
            if prev_members_set is not None and members_set == prev_members_set:
                logging.warning(f"{date_str}: Members identical to previous month! Override may not be working.")
                print(f"{date_str}: WARNING: Members identical to previous month!")
            prev_members_set = members_set
        except Exception as e:
            logging.error(f"{date_str}: Error fetching members: {e}", exc_info=True)
            print(f"{date_str}: Error fetching members: {e}")

def main():
    index_ticker = 'I05510CA Index'
    end_date = datetime.today()
    start_date = end_date - relativedelta(years=5)
    fetch_historical_members(index_ticker, start_date, end_date)

if __name__ == "__main__":
    main()
