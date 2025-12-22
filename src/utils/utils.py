import streamlit as st
import pandas as pd

def _add_available_plot(title):
    if 'available_plots' not in st.session_state:
        st.session_state['available_plots'] = set()
    st.session_state['available_plots'].add(title)


def _set_df_loaded():
    st.session_state['df_loaded'] = True

def _clear_data():
    for k in ['df', 'leveraged_df', 'df_loaded', 'leveraged_created', 'available_plots']:
        if k in st.session_state:
            del st.session_state[k]


def _show_day_range_slider(df):
    # Add days range slider
    min_day = int(df['Days'].min())
    max_day = int(df['Days'].max())
    start_day, end_day = st.slider("Days range slider", min_value=min_day, max_value=max_day, value=(min_day, max_day), step=1)
    return start_day, end_day


def _leverage_dataset(_df, L=5, knockout_zero=True):
    # Get prices from original dataset as a Pandas Series
    prices = pd.Series(_df["Adj Close"])
    # Create new Series with the price percentage change (daily returns)
    daily_returns = prices.pct_change().fillna(0.0)
    # Compute leveraged performance
    leveraged_daily_returns = L * daily_returns
    # Add base 1 to make compounding effect
    factor = 1 + leveraged_daily_returns

    if knockout_zero:
        # Look for negative returns and limit them to zero
        factor = factor.where(factor > 0.0, 0.0)
        # Create a mask with the first value equal to zero
        # Use cummax to ensure all values after first 0 are included
        zero_mask = (factor == 0.0).cummax()
        # After ETP arrives value 0, it "dissappears"
        factor[zero_mask] = 0.0

    # Get initial price from original dataset
    initial_nav = _df['Adj Close'].iloc[0]
    # Accumulate all the performances starting on initial price (compound effect)
    nav = initial_nav * factor.cumprod()

    return pd.DataFrame({"Date": _df["Date"], "Days": _df["Days"], "Og Adj Close": _df['Close'], "Adj Close": nav})