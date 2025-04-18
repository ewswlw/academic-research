"""
Script to fetch and print members of the Bloomberg index 'I05510CA Index' using the xbbg library.
- Prints results to console only.
- Includes robust error handling, logging, and inline comments.
- Requires Bloomberg Terminal and API access.
"""

import sys
import logging
from xbbg import blp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def fetch_index_members(index_ticker: str):
    """
    Fetch and print the members of a Bloomberg index using xbbg (BDS API).
    Args:
        index_ticker (str): Bloomberg index ticker (e.g., 'I05510CA Index')
    """
    logging.info(f"Fetching members for index: {index_ticker}")
    try:
        # Fetch members using Bloomberg Data Set (BDS) field
        members = blp.bds(index_ticker, 'INDX_MEMBERS')
        if members is None or members.empty:
            logging.warning(f"No members found for index: {index_ticker}")
            print(f"No members found for index: {index_ticker}")
            return
        # Print header
        print(f"Members of {index_ticker} ({len(members)} constituents):\n")
        # Try to print ticker and name columns if available
        ticker_col = None
        name_col = None
        for col in members.columns:
            if 'member' in col.lower() and ticker_col is None:
                ticker_col = col
            if 'name' in col.lower() and name_col is None:
                name_col = col
        if ticker_col:
            for i, row in members.iterrows():
                ticker = row.get(ticker_col, 'N/A')
                name = row.get(name_col, 'N/A') if name_col else ''
                print(f"{ticker}: {name}")
        else:
            # Fallback: print all columns
            print(members)
        logging.info(f"Successfully fetched {len(members)} members.")
    except Exception as e:
        logging.error(f"Error fetching members for {index_ticker}: {e}", exc_info=True)
        print(f"Failed to fetch members for {index_ticker}. Check Bloomberg connection and permissions.")

def main():
    # Bloomberg index ticker
    index_ticker = 'I05510CA Index'
    fetch_index_members(index_ticker)

if __name__ == "__main__":
    main()
