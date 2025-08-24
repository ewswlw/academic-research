
import pandas as pd
import numpy as np
from datetime import datetime

def load_defense_first_data(file_format='parquet', file_path='defense_first_data'):
    """
    Load Defense First dataset with proper datetime index
    
    Parameters:
    file_format: 'csv', 'parquet', or 'excel'
    file_path: base filename (without extension)
    
    Returns:
    DataFrame with datetime index
    """
    
    if file_format.lower() == 'csv':
        # Load CSV with proper datetime parsing
        data = pd.read_csv(
            f'{file_path}.csv',
            index_col=0,
            parse_dates=True
        )
        
    elif file_format.lower() == 'parquet':
        # Load Parquet (datetime index preserved automatically)
        data = pd.read_parquet(f'{file_path}.parquet')
        
    elif file_format.lower() == 'excel':
        # Load Excel with proper datetime parsing
        data = pd.read_excel(
            f'{file_path}.xlsx',
            sheet_name='Price_Data',
            index_col=0,
            parse_dates=True
        )
        
    else:
        raise ValueError("file_format must be 'csv', 'parquet', or 'excel'")
    
    # Ensure index is datetime and properly named
    data.index = pd.to_datetime(data.index)
    data.index.name = 'Date'
    
    # Sort by date to ensure proper chronological order
    data = data.sort_index()
    
    return data

def load_returns_data(file_path='defense_first_data'):
    """Load monthly returns with datetime index"""
    try:
        returns = pd.read_excel(
            f'{file_path}.xlsx',
            sheet_name='Monthly_Returns',
            index_col=0,
            parse_dates=True
        )
        returns.index = pd.to_datetime(returns.index)
        returns.index.name = 'Date'
        return returns.sort_index()
    except Exception as e:
        print(f"Could not load returns from Excel: {e}")
        # Calculate returns from main data
        data = load_defense_first_data('parquet', file_path)
        returns = data.pct_change().dropna()
        return returns

def get_data_summary(file_path='defense_first_data'):
    """Get comprehensive data summary"""
    
    # Load main data
    data = load_defense_first_data('parquet', file_path)
    
    summary = {
        'shape': data.shape,
        'date_range': (data.index.min(), data.index.max()),
        'frequency': pd.infer_freq(data.index),
        'assets': list(data.columns),
        'missing_data': data.isnull().sum().to_dict(),
        'data_coverage': ((len(data) - data.isnull().sum()) / len(data) * 100).to_dict()
    }
    
    return summary

# Example usage:
if __name__ == "__main__":
    # Load data
    data = load_defense_first_data('parquet')  # Recommended format
    print(f"Loaded data shape: {data.shape}")
    print(f"Date range: {data.index.min()} to {data.index.max()}")
    print(f"Assets: {', '.join(data.columns)}")
    
    # Display sample
    print("\nSample data (last 5 observations):")
    print(data.tail())
    
    # Load returns
    returns = load_returns_data()
    print(f"\nReturns data shape: {returns.shape}")
    
    # Get summary
    summary = get_data_summary()
    print(f"\nData Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
