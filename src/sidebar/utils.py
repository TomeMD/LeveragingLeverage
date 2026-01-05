import pandas as pd
import yfinance as yf

DEFAULT_DATE_COL = "date"


def load_csv(path):
    df = pd.read_csv(path, index_col=0)
    df['Date'] = pd.to_datetime(df['Date'])
    return df


def download_dataset(ticker, interval, start_year, save=False):
    yf_tickers = {'sp500': '^GSPC', 'nasdaq': 'QQQ'}
    yf_intervals = {'daily': '1d', 'monthly': '1mo'}

    if ticker not in yf_tickers:
        raise ValueError(f"Asset {ticker} is not supported. Supported: {list(yf_tickers.keys())}")

    interval_code = yf_intervals.get(interval, '1d')
    start = f"{start_year}-01-01"

    df = yf.download(yf_tickers[ticker], start=start, interval=interval_code, auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError("No data downloaded from Yahoo Finance for given parameters")
    df = df.reset_index()
    # If multiindex columns, flatten
    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)
        df.columns.name = None

    df['Date'] = pd.to_datetime(df['Date'])
    df['Days'] = (df['Date'] - df['Date'].min()).dt.days

    if save:
        df.to_csv(f"data/{ticker}_{interval}_{start_year}_2025.csv")

    return df