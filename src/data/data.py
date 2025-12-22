import pandas as pd
import yfinance as yf
from typing import Tuple, Optional

DEFAULT_DATE_COL = "date"

def filter_by_date_range(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, date_col: str = DEFAULT_DATE_COL) -> pd.DataFrame:
    """
    Filtra df por el rango [start, end] (inclusive).
    Acepta start/end como strings, datetime.date o pd.Timestamp.
    """
    if date_col not in df.columns:
        raise KeyError(f"date column '{date_col}' not found in DataFrame")
    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end)
    mask = (df[date_col] >= start_ts) & (df[date_col] <= end_ts)
    return df.loc[mask].copy()

def get_date_bounds(df: pd.DataFrame, date_col: str = DEFAULT_DATE_COL) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Devuelve (min_date, max_date) del DataFrame según date_col."""
    if date_col not in df.columns:
        raise KeyError(f"date column '{date_col}' not found in DataFrame")
    min_date = pd.to_datetime(df[date_col].min())
    max_date = pd.to_datetime(df[date_col].max())
    return min_date, max_date