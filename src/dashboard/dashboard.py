import streamlit as st
import pandas as pd
from src.visualization import plot_timeseries, plot_combined_original_and_leveraged
from src.utils.utils import _show_day_range_slider


def run():
    if not st.session_state.get('df_loaded', False):
        st.info("Upload a CSV file or download the data from Yahoo Finance")
        st.stop()

    df = st.session_state["df"]
    date_col = "Date"

    selected_plot = st.selectbox("Select plot", options=st.session_state.get('available_plots', {}))
    if not selected_plot:
        st.info("Select a plot to visualize data")
        st.stop()

    # Add days range slider
    start_day, end_day = _show_day_range_slider(df)
    filtered = df[(df['Days'] >= start_day) & (df['Days'] <= end_day)].copy()
    #st.write(f"Selected registers: {len(filtered)} — {start_date} a {end_date}")

    # CODIGO PARA MOSTRAR COMPARACION
    if "Original vs Leveraged" in selected_plot:
        lev_L_str = selected_plot.split(" ")[-1]
        lev_df = st.session_state['leveraged_df'][lev_L_str]
        fig = plot_combined_original_and_leveraged(orig=filtered, leveraged=lev_df, title=selected_plot)
        st.plotly_chart(fig, width='content')
        #st.markdown("Current parameters")
        #st.write(f"L = {lev_L}")
        #st.write(f"Knockout = {knockout}")
        if st.button("Download leveraged dataset (CSV)"):
            st.download_button("Download leveraged dataset (CSV)", data=lev_df.to_csv(index=False).encode('utf-8'), file_name="leveraged.csv", mime="text/csv")

    if selected_plot == "Price over time":
        st.plotly_chart(plot_timeseries(filtered, date_col=date_col, value_col="Adj Close", title=f"Price over time"), width='content')
