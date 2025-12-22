import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional, List


def plot_timeseries(df: pd.DataFrame, date_col: str, value_col: str, title: Optional[str] = None):
    df_sorted = df.sort_values(date_col)
    fig = px.line(df_sorted, x=date_col, y=value_col, title=title or f"{value_col} over time")
    fig.update_layout(xaxis_title=date_col, yaxis_title=value_col, height=450, template="plotly_white")
    #fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(tickformat=".2f", showgrid=True)
    return fig

def plot_combined_original_and_leveraged(orig: pd.DataFrame, leveraged: pd.DataFrame,
                                         date_col: str = "Date", value_col_orig: str = "Adj Close",
                                         value_col_lev: str = "Adj Close", title: Optional[str] = None):
    """
    Crea una figura con ambas series en el mismo eje y (misma unidad) — útil para comparar NAVs.
    Acepta que los DataFrames tengan las mismas fechas; en caso contrario hace un merge por date_col.
    """
    o = orig[[date_col, value_col_orig]].rename(columns={value_col_orig: "Original"})
    l = leveraged[[date_col, value_col_lev]].rename(columns={value_col_lev: "Leveraged"})
    merged = pd.merge(o, l, on=date_col, how="inner").sort_values(date_col)
    merged = merged.reset_index(drop=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=merged[date_col], y=merged["Original"], mode='lines', name='Original'))
    fig.add_trace(go.Scatter(x=merged[date_col], y=merged["Leveraged"], mode='lines', name='Leveraged'))
    fig.update_layout(title=title or "Original vs Leveraged", xaxis_title=date_col, yaxis_title="Value", height=500, template="plotly_white")
    #fig.update_xaxes(rangeslider_visible=True)
    return fig