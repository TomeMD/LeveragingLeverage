import streamlit as st
import pandas as pd
from datetime import date, datetime
from src.utils.utils import _show_day_range_slider, _leverage_dataset
from src.backtest.utils import plot_backtest, translate_operation_days_to_dates
from src.backtest.strategy import thresholds


def compute_backtest(capital, window):
    # Very hard computations
    return {"capital": capital, "window": window}


def render_backtest_result(df, df_x2, df_x3, start_day, end_day, result):
    x1_filtered = df[(df['Days'] >= start_day) & (df['Days'] <= end_day)].copy()
    translated_ops = translate_operation_days_to_dates(st.session_state["df"], result)
    fig = plot_backtest(x1_filtered, df_x2, df_x3, translated_ops)
    st.plotly_chart(fig, width='content')


def run():

    if not st.session_state.get('df_loaded', False):
        st.info("Upload a CSV file or download the data from Yahoo Finance")
        st.stop()

    df = st.session_state["df"]

    # Parameters
    initial_capital = st.number_input("Initial capital", 1_000, 1_000_000, 10_000)
    start_date = st.date_input("Start date", value=date(2020, 1, 1), min_value=date(1900, 1, 1))
    end_date = st.date_input("End date", value="today", min_value=date(1900, 1, 1))
    # strategy = st.selectbox("Investment strategy", options=["thresholds"])

    params = (initial_capital, start_date, end_date)

    if st.session_state.get('backtest_params', ()) != params:
        filtered = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))].copy()
        lev_df_x2 = _leverage_dataset(filtered, L=2, knockout_zero=True)
        lev_df_x3 = _leverage_dataset(filtered, L=3, knockout_zero=True)
        st.session_state.backtest_data = {
            "x1": filtered,
            "x2": lev_df_x2,
            "x3": lev_df_x3
        }
    else:
        filtered = st.session_state.get("backtest_data", {}).get("x1", None)
        lev_df_x2 = st.session_state.get("backtest_data", {}).get("x2", None)
        lev_df_x3 = st.session_state.get("backtest_data", {}).get("x3", None)

    run = st.button("▶ Run backtest")
    # Run backtest if button is pressed and parameters have changed
    if run and st.session_state.get('backtest_params', ()) != params:
        with st.spinner("Doing a really hard work to backtest your strategy..."):
            st.session_state.backtest_result = thresholds.backtest(filtered, lev_df_x2, lev_df_x3, initial_capital)
            st.session_state.backtest_params = params

    # Show results
    if st.session_state.get("backtest_result", None) is not None:
        start_day, end_day = _show_day_range_slider(filtered)
        render_backtest_result(filtered, lev_df_x2, lev_df_x3, start_day, end_day, st.session_state.backtest_result)
    else:
        st.info("Run backtest to see results")

    #with st.spinner("Doing a really hard work to backtest your strategy..."):
    #    st.info("START BACKTEST")
    #    time.sleep(5)
    #    st.info("END BACKTEST")