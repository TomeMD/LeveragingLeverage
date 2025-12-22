import pandas as pd
from typing import Optional

def add_basic_time_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """
    Añade columnas temporales: year, month, day, weekday.
    No modifica el original (devuelve copia).
    """
    df2 = df.copy()
    df2[date_col] = pd.to_datetime(df2[date_col])
    df2["year"] = df2[date_col].dt.year
    df2["month"] = df2[date_col].dt.month
    df2["day"] = df2[date_col].dt.day
    df2["weekday"] = df2[date_col].dt.day_name()
    return df2




# Aquí añade más funciones de feature engineering que tengas en el notebook,
# por ejemplo: leverage_ratio, moving averages, returns, etc.
# Convierte cada cell en una función que reciba el DataFrame y parámetros.