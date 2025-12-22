import streamlit as st
from datetime import date
from src.sidebar.utils import load_csv, download_dataset
from src.utils.utils import _add_available_plot, _clear_data, _leverage_dataset


def run():
    st.sidebar.header("Data source")
    data_source = st.sidebar.radio("Source", ("CSV file", "Yahoo Finance"))

    if data_source == "CSV file":
        uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"], on_change=_clear_data)
        if uploaded_file is not None:
            # Load dataset and save in session state
            try:
                df = load_csv(uploaded_file)
                st.session_state['df'] = df
                st.session_state['df_loaded'] = True
                st.sidebar.success("CSV loaded")
            except Exception as e:
                st.sidebar.error(f"Error reading CSV file: {e}")
    else:
        st.sidebar.markdown("Download data from Yahoo Finance")
        ticker = st.sidebar.selectbox("Ticker", options=["sp500", "nasdaq"])
        interval = st.sidebar.selectbox("Interval", options=["daily", "monthly"])
        start_year = st.sidebar.number_input("Start year", min_value=1900, max_value=date.today().year, value=1927, step=1)
        if st.sidebar.button("Download"):
            _clear_data()
            # Download dataset and save in session state
            try:
                df = download_dataset(ticker=ticker, interval=interval, start_year=int(start_year), save=True)
                st.session_state['df'] = df
                st.session_state['df_loaded'] = True
                st.sidebar.success("Dataset downloaded")
            except Exception as e:
                st.sidebar.error(f"Error downloading {ticker} from Yahoo Finance: {e}")

    if st.session_state.get('df_loaded', False):
        _add_available_plot("Price over time")
        df = st.session_state['df']


        st.sidebar.markdown("#### Create leveraged dataset")
        lev_L = st.sidebar.number_input("Leverage Factor (L)", value=3.0, step=0.5)
        knockout = st.sidebar.checkbox("Zero knockout (Ignore negative returns)", value=True)
        if st.sidebar.button("Create"):
            try:
                lev_df = _leverage_dataset(df, L=lev_L, knockout_zero=knockout)
                st.session_state.setdefault('leveraged_df', {})[f"x{lev_L}"] = lev_df
                print(st.session_state.keys())
                st.session_state['leveraged_created'] = True
                _add_available_plot(f"Original vs Leveraged x{lev_L}")
                st.success("Leveraged dataset successfully created")
            except Exception as e:
                st.sidebar.error(f"Error while creating leveraged dataset: {e}")


    st.sidebar.markdown("---")
    if st.sidebar.button("Clean data"):
        _clear_data()
        st.rerun()