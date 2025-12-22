import pandas as pd
from datetime import timedelta
import plotly.graph_objects as go


def translate_operation_days_to_dates(df, operations):
    initial_date = df['Date'].min()
    translated_ops = {"buys_tracker": [], "rotate_tracker": [], "sells_tracker": []}
    print(operations)
    for op_type in translated_ops.keys():
        for op_name, days in operations[op_type]:
            date = initial_date + timedelta(days=int(days))
            translated_ops[op_type].append((op_name, date))

    return translated_ops


def add_operations_trace(fig, merged, operations, key, color, date_col):
    ops = operations.get(key, [])
    if not ops:
        return

    names, dates = zip(*ops)

    ops_df = pd.DataFrame({
        "name": names,
        date_col: pd.to_datetime(dates),
    })

    ops_df = ops_df.merge(
        merged[[date_col, "x1"]],
        on=date_col,
        how="inner"
    )

    fig.add_trace(
        go.Scatter(
            x=ops_df[date_col],
            y=ops_df["x1"],
            mode="markers+text",
            name=key.replace("_tracker", ""),
            marker=dict(
                size=9,
                color=color,
                symbol="circle",
                line=dict(width=1, color="white"),
            ),
            text=ops_df["name"],
            textposition="top center",
            textfont=dict(size=9, color=color),
            hovertemplate="<b>%{text}</b><br>%{x|%Y-%m-%d}<br>%{y:.2f}<extra></extra>",
        )
    )



def plot_backtest(df, df_x2, df_x3, operations, date_col="Date"):
    d1 = df[[date_col, "Adj Close"]].rename(columns={"Adj Close": "x1"})
    d2 = df_x2[[date_col, "Adj Close"]].rename(columns={"Adj Close": "x2"})
    d3 = df_x3[[date_col, "Adj Close"]].rename(columns={"Adj Close": "x3"})
    merged = d1.merge(d2, on=date_col).merge(d3, on=date_col).sort_values(date_col).reset_index(drop=True)

    # operations structure:
    # {
    #   "buys_tracker": [(name, <date-1>), ..., (name, <date-n>)],
    #   "rotate_tracker": [(name, <date-1>), ..., (name, <date-n>)],
    #   "sells_tracker": [(name, <date-1>), ..., (name, <date-n>)]
    # }

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=merged[date_col], y=merged["x1"], mode='lines', name='x1', line={"color": "#1f77b4"}))
    fig.add_trace(go.Scatter(x=merged[date_col], y=merged["x2"], mode='lines', name='x2', line={"color": "#9467bd"}))
    fig.add_trace(go.Scatter(x=merged[date_col], y=merged["x3"], mode='lines', name='x3', line={"color": "#7f7f7f"}))

    # Operaciones
    add_operations_trace(fig, merged, operations, "buys_tracker", "#2ecc71", date_col)
    add_operations_trace(fig, merged, operations, "rotate_tracker", "#f39c12", date_col)
    add_operations_trace(fig, merged, operations, "sells_tracker", "#e74c3c", date_col)

    fig.update_layout(xaxis_title=date_col, yaxis_title="Value", height=500, template="plotly_white")
    #fig.update_xaxes(rangeslider_visible=True)
    return fig
