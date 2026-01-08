import streamlit as st
import pandas as pd
from datetime import date
from src.utils.utils import _show_day_range_slider, _leverage_dataset
from src.backtest.utils import plot_backtest, translate_operation_days_to_dates, plot_wallet_chart
from src.backtest.strategy.builders import STRATEGY_BUILDERS
from src.evaluation.configs import ENTRY_THRESHOLDS_SPACE

def thresholds_df_to_dict(df):
    thresholds = {}
    for _, row in df.iterrows():
        if pd.isna(row["drawdown"]) or pd.isna(row["buy_pct"]) or pd.isna(row["asset"]):
            continue
        thresholds[float(row["drawdown"])] = (float(row["buy_pct"]), str(row["asset"]))

    if any(d >= 0 for d in thresholds):
        st.error("Drawdowns must be negative values")
        st.stop()

    if any(p <= 0 or p > 1 for p, _ in thresholds.values()):
        st.error("Buy percentage must be between 0 and 1")
        st.stop()

    return dict(sorted(thresholds.items(), reverse=True))


def create_entry_thresholds_input():
    st.markdown("### Entry thresholds")

    thresholds_key = st.selectbox(
        "Select predefined template",
        options=sorted(list(ENTRY_THRESHOLDS_SPACE.keys()))
    )

    data = [{"drawdown": k, "buy_pct": v[0], "asset": v[1]} for k, v in ENTRY_THRESHOLDS_SPACE[thresholds_key].items()]
    default_thresholds_df=pd.DataFrame(data)

    thresholds_df = st.data_editor(
        default_thresholds_df,
        num_rows="dynamic",
        width='stretch',
        column_config={
            "drawdown": st.column_config.NumberColumn(
                "Drawdown",
                help="Negative value, e.g. -0.2 = -20%",
                format="%.2f",
            ),
            "buy_pct": st.column_config.NumberColumn(
                "% of total to buy",
                help="Fraction of initial capital (0.1 = 10%)",
                format="%.2f",
            ),
            "asset": st.column_config.SelectboxColumn(
                "Asset",
                options=["x1", "x2", "x3"],
            ),
        },
    )
    return thresholds_df_to_dict(thresholds_df)


def create_yields_input(entry_thresholds):
    assets = sorted({asset for _, asset in entry_thresholds.values()})
    yield_targets = {}
    yield_values = {}
    for asset in assets:
        with st.container():
            c1, c2 = st.columns([1, 2])

            with c1:
                target_type = st.selectbox(
                    f"{asset} – Yield target type",
                    options=["auto", "num", "none"],
                    key=f"yield_type_{asset}",
                    format_func=lambda k: {
                        "num": "Numerical value",
                        "auto": "Automatic yield based on current drawdown",
                        "none": "No yield target (only accumulate)",
                    }[k]
                )

            yield_targets[asset] = target_type

            if target_type == "num":
                with c2:
                    value = st.number_input(
                        f"{asset} – Yield value",
                        min_value=0.0,
                        step=0.01,
                        value=0.5,
                        key=f"yield_value_{asset}",
                    )
                yield_values[asset] = value
            else:
                yield_values[asset] = None

    return yield_targets, yield_values


def render_backtest_result(start_day, end_day, strategy_params, input_dfs, result):
    # Unpack strategy parameters
    initial_capital, strategy_key, entry_thresholds, rotate, risk_control, yield_targets, yield_values, debt_yield, allow_fractional = strategy_params

    # Translate operations tracked days to DataFrame dates, in order to plot them properly in the X-axis
    x1 = input_dfs["x1"]
    x1_filtered = x1[(x1['Days'] >= start_day) & (x1['Days'] <= end_day)].copy()
    translated_ops = translate_operation_days_to_dates(st.session_state["df"], result)

    # Plot input DataFrames with the performed operations (buy, rotate and sell)
    fig = plot_backtest(x1_filtered, input_dfs["x2"], input_dfs["x3"], translated_ops)
    st.plotly_chart(fig, width='stretch')

    st.markdown("### Analysis of results")
    assets = []
    invested_value = 0.0
    for asset in result["assets"]:
        invested = result[asset].get_invested_eur()
        value = result[asset].get_invested_value()
        invested_value += value
        assets.append((asset, invested, value))

    cash = result["cash"]
    total_value = cash + invested_value

    # Compute base scenario
    first_price = x1.loc[x1['Date'].idxmin(), 'Adj Close']
    last_price = x1.loc[x1['Date'].idxmax(), 'Adj Close']
    expected_value = initial_capital * last_price / first_price
    base_debt_time = end_day - start_day
    base_debt_cost = initial_capital * base_debt_time * (debt_yield / 360)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cash", f"{cash:,.2f} €")
    c2.metric("Fees", f"{result['fees_paid']:,.2f} €")
    c3.metric("Assets value", f"{invested_value:,.2f} €")
    c4.metric("Total value", f"{total_value:,.2f} €", delta=f"Debt cost: {-result['debt_cost']:,.2f} € ({result['debt_time']} days)", delta_color="inverse", delta_arrow="down")
    c5.metric("Base scenario", f"{expected_value:,.2f} €", delta=f"Debt cost: {-base_debt_cost:,.2f} € ({base_debt_time} days)", delta_color="inverse", delta_arrow="down")

    fig = plot_wallet_chart(assets)
    st.plotly_chart(fig, width='stretch')


def update_data(start_date, end_date, df):
    _data = {}
    _updated = False
    start_dt, end_dt = pd.to_datetime(start_date), pd.to_datetime(end_date)
    if end_dt < start_dt:
        st.error("End date must be later than the start date")
        st.stop()

    if st.session_state.get('data_params', ()) != (start_date, end_date):
        _data["x1"] = df[(df['Date'] >= start_dt) & (df['Date'] <= end_dt)].copy()
        _data["x2"] = _leverage_dataset(_data["x1"], L=2, knockout_zero=True)
        _data["x3"] = _leverage_dataset(_data["x1"], L=3, knockout_zero=True)
        _updated = True
        st.session_state.backtest_data = _data
        st.session_state.data_params = (start_date, end_date)
    else:
        _data = st.session_state.backtest_data

    return _updated, _data


def run():

    if not st.session_state.get('df_loaded', False):
        st.info("Upload a CSV file or download the data from Yahoo Finance")
        st.stop()

    df = st.session_state["df"]

    # Parameters
    initial_capital = st.number_input("Initial capital", 1_000, 1_000_000, 10_000)
    start_date = st.date_input("Start date", value=date(2020, 1, 1), min_value=date(1900, 1, 1))
    end_date = st.date_input("End date", value="today", min_value=date(1900, 1, 1))
    strategy_key = st.selectbox(
        "Investment strategy",
        options=list(STRATEGY_BUILDERS.keys()),
        format_func=lambda k: {
            "thresholds": "Threshold-based buys + Yield-based sales",
        }[k],
    )
    entry_thresholds = create_entry_thresholds_input()
    yield_targets, yield_values = create_yields_input(entry_thresholds)
    rotate = st.toggle("Rotate between leverage factors", value=False)
    risk_control = st.toggle("Risk control", value=False)
    allow_fractional = st.toggle("Allow fractional shares", value=True)
    debt_yield = st.number_input("Debt yield", min_value=0.0000, max_value=1.0000, step=0.0001, value=0.0325, format="%0.4f")

    # Check if data has been updated
    updated_data, input_dfs = update_data(start_date, end_date, df)

    # Check if strategy has been updated
    strategy_params = (initial_capital, strategy_key, entry_thresholds, rotate, risk_control, yield_targets, yield_values, debt_yield, allow_fractional)
    updated_strategy = st.session_state.get('strategy_params', ()) != strategy_params

    run = st.button("▶ Run backtest")
    # Run backtest if button is pressed and parameters have changed
    if run and (updated_data or updated_strategy):
        with st.spinner("Doing a really hard work to backtest your strategy..."):
            if updated_strategy:
                strategy = STRATEGY_BUILDERS[strategy_key](initial_capital, entry_thresholds, input_dfs, rotate, risk_control, yield_targets, yield_values, debt_yield, allow_fractional)
                st.session_state.backtest_strategy = strategy
            else:
                strategy = st.session_state.get("backtest_strategy", None)
            st.session_state.backtest_result = strategy.backtest()

    # Show results
    if st.session_state.get("backtest_result", None) is not None:
        start_day, end_day = _show_day_range_slider(input_dfs["x1"])
        render_backtest_result(start_day, end_day, strategy_params, input_dfs, st.session_state.backtest_result)
    else:
        st.info("Run backtest to see results")