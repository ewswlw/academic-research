"""
Test for xbbg Bloomberg API integration: fetch SPX daily data for the last 5 years.

This script checks that the xbbg library is installed and functional in your Poetry environment.
It will print and log the shape and head/tail of the resulting DataFrame, and handle errors gracefully.
"""
import sys
import logging
from datetime import datetime, timedelta

# Setup logging for debugging and reproducibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

try:
    from xbbg import blp
except ImportError as e:
    logging.error("xbbg library is not installed. Please install it in your Poetry environment.")
    print("ERROR: xbbg library is not installed. Run 'poetry add xbbg' and try again.")
    sys.exit(1)

# Define parameters for data fetch
ticker = 'SPX Index'
field = 'PX_LAST'
end_date = datetime.today()
start_date = end_date - timedelta(days=5*365)

logging.info(f"Attempting to fetch daily {ticker} data from {start_date.date()} to {end_date.date()} using xbbg...")

try:
    df = blp.bdh(
        tickers=ticker,
        flds=field,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        Per='D',
        Fill='P',
    )
    if df is None or df.empty:
        logging.error("No data returned. Check your Bloomberg connection and permissions.")
        print("ERROR: No data returned. Is your Bloomberg Terminal/API running and configured?")
        sys.exit(2)
    # Print and log DataFrame info
    logging.info(f"Data shape: {df.shape}")
    print("First 5 rows:\n", df.head())
    print("Last 5 rows:\n", df.tail())
    print(f"Total rows returned: {df.shape[0]}")
except Exception as ex:
    logging.exception("Failed to fetch data from Bloomberg API via xbbg.")
    print(f"ERROR: Exception occurred while fetching data: {ex}")
    sys.exit(3)

print("xbbg Bloomberg API test completed successfully.")
