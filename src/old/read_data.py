from datetime import datetime, timedelta
import os
import yfinance as yf
import pandas as pd

# ------------------------------------------------------------------------------------------------------------------
# READ DATA
# ------------------------------------------------------------------------------------------------------------------
def read_dataset(index, interval, start_year, save=False, force_download=False):
    yf_tickers = {'sp500': '^GSPC', 'nasdaq': 'QQQ'}
    yf_intervals = {'daily': '1d', 'monthly': '1mo'}
    dataset_path = f"{index}_daily_{start_year}_2025.csv"

    # First check if CSV file with the data already exists
    if not force_download and os.path.exists(dataset_path):
        df = pd.read_csv(dataset_path, index_col=0)
        df['Date'] = pd.to_datetime(df['Date'])
    else:
        # Check that the index is currently supported for Yahoo Finance
        if index not in yf_tickers:
            raise ValueError(f"Index {index} is not supported")
    
        # Download dataset from Yahoo Finance
        df = yf.download(yf_tickers[index], start=f'{start_year}-01-01', interval=yf_intervals.get(interval, "1d"), auto_adjust=False)
    
        # Clean dataset
        df = df.reset_index() # Set date as another column
        df.columns = df.columns.get_level_values(0) # Remove MultiIndex for ticker
        df.columns.name = None
        df['Date'] = pd.to_datetime(df['Date'])
        df['Days'] = (df['Date'] - df['Date'].min()).dt.days
    
        # Save dataset if specified
        if save:
            df.to_csv(dataset_path)
    
    return df
