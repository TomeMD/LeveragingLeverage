import pandas as pd
from datetime import timedelta
import plotly.graph_objects as go


def translate_operation_days_to_dates(df, operations):
    initial_date = df['Date'].min()
    translated_ops = {"buy_tracker": [], "rotate_tracker": [], "sell_tracker": []}
    for op_type in translated_ops.keys():
        for op_name, days in operations[op_type]:
            date = initial_date + timedelta(days=int(days))
            translated_ops[op_type].append((op_name, date))

    return translated_ops


def add_operations_trace(fig, merged, lev_factor_str, ops, color, label, date_col, legendgroup=None, showlegend=True):
    if not ops:
        return

    names, dates = zip(*ops)

    ops_df = pd.DataFrame({
        "name": names,
        date_col: pd.to_datetime(dates),
    })

    ops_df = ops_df.merge(
        merged[[date_col, lev_factor_str]],
        on=date_col,
        how="inner"
    )

    fig.add_trace(
        go.Scatter(
            x=ops_df[date_col],
            y=ops_df[lev_factor_str],
            mode="markers+text",
            name=label,
            legendgroup=legendgroup,
            showlegend=showlegend,
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


def plot_wallet_chart(assets):

    bar_fig = go.Figure()

    names = [label for label, _, _ in assets]
    bar_fig.add_bar(
        name="Invested",
        x=names,
        y=[invested for _, invested, _ in assets],
    )

    bar_fig.add_bar(
        name="Current value",
        x=names,
        y=[value for _, _, value in assets],
    )

    bar_fig.update_layout(
        barmode="group",
        height=260,
        margin=dict(l=10, r=10, t=30, b=10),
        title="Invested vs Current value",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return bar_fig


def plot_backtest(df, df_x2, df_x3, operations, date_col="Date"):
    d1 = df[[date_col, "Adj Close"]].rename(columns={"Adj Close": "x1"})
    d2 = df_x2[[date_col, "Adj Close"]].rename(columns={"Adj Close": "x2"})
    d3 = df_x3[[date_col, "Adj Close"]].rename(columns={"Adj Close": "x3"})
    merged = d1.merge(d2, on=date_col).merge(d3, on=date_col).sort_values(date_col).reset_index(drop=True)

    base = merged.iloc[0]  # Initial value for each asset
    for col in ["x1", "x2", "x3"]:
        merged[f"{col}_norm"] = merged[col] / base[col] * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=merged[date_col], y=merged["x1_norm"], mode='lines', name='x1', line={"color": "#1f77b4"}))
    fig.add_trace(go.Scatter(x=merged[date_col], y=merged["x2_norm"], mode='lines', name='x2', line={"color": "#9467bd"}))
    fig.add_trace(go.Scatter(x=merged[date_col], y=merged["x3_norm"], mode='lines', name='x3', line={"color": "#7f7f7f"}))

    # Operations
    x1_save = [("x1", day) for (name, day) in operations["buy_tracker"] if "x1_save" in name]
    add_operations_trace(fig, merged, "x1_norm", x1_save, "#3498db", "Save", date_col, legendgroup="Save", showlegend=True)

    x1_buys = [(name, day) for (name, day) in operations["buy_tracker"] if "x1" == name]
    x2_buys = [(name, day) for (name, day) in operations["buy_tracker"] if "x2" in name]
    x3_buys = [(name, day) for (name, day) in operations["buy_tracker"] if "x3" in name]
    add_operations_trace(fig, merged, "x1_norm", x1_buys, "#2ecc71", "Buy", date_col, legendgroup="buy", showlegend=True)
    add_operations_trace(fig, merged, "x2_norm", x2_buys, "#2ecc71", "Buy", date_col, legendgroup="buy", showlegend=(not x1_buys))
    add_operations_trace(fig, merged, "x3_norm", x3_buys, "#2ecc71", "Buy", date_col, legendgroup="buy", showlegend=(not x2_buys))

    x1_rotations = [(name, day) for (name, day) in operations["rotate_tracker"] if "x1" == name]
    x2_rotations = [(name, day) for (name, day) in operations["rotate_tracker"] if "x2" in name]
    x3_rotations = [(name, day) for (name, day) in operations["rotate_tracker"] if "x3" in name]
    add_operations_trace(fig, merged, "x1_norm", x1_rotations, "#f39c12", "Rotate", date_col, legendgroup="rotate", showlegend=True)
    add_operations_trace(fig, merged, "x2_norm", x2_rotations, "#f39c12", "Rotate", date_col, legendgroup="rotate", showlegend=(not x1_buys))
    add_operations_trace(fig, merged, "x3_norm", x3_rotations, "#f39c12", "Rotate", date_col, legendgroup="rotate", showlegend=(not x2_buys))

    x1_sells = [(name, day) for (name, day) in operations["sell_tracker"] if "x1" == name]
    x2_sells = [(name, day) for (name, day) in operations["sell_tracker"] if "x2" in name]
    x3_sells = [(name, day) for (name, day) in operations["sell_tracker"] if "x3" in name]
    add_operations_trace(fig, merged, "x1_norm", x1_sells, "#e74c3c", "Sell", date_col, legendgroup="sell", showlegend=True)
    add_operations_trace(fig, merged, "x2_norm", x2_sells, "#e74c3c", "Sell", date_col, legendgroup="sell", showlegend=(not x1_buys))
    add_operations_trace(fig, merged, "x3_norm", x3_sells, "#e74c3c", "Sell", date_col, legendgroup="sell", showlegend=(not x2_buys))

    fig.update_layout(xaxis_title=date_col, yaxis_title="Normalized Value (%)", height=500, template="plotly_white")

    return fig
