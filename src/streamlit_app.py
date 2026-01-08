import streamlit as st
import os
from src.sidebar import sidebar
from src.dashboard import dashboard
from src.backtest import backtest
from src.evaluation import evaluation

st.session_state['PROJECT_DIR'] = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Leverage Strategy", page_icon="📈", layout="wide")

st.title("📈 Leveraging Leverage")

# Load style
st.markdown("""
<style>
/* Radio container */
div[role="radiogroup"] {
    display: flex;
    gap: 0.5rem;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;
}

/* Options config */
div[role="radio"] {
    padding: 0.4rem 0.2rem;
    border-radius: 6px 6px 0 0;
    background-color: #f5f5f5;
    border: 1px solid transparent;
    font-weight: 500;
}

/* Hover */
div[role="radio"]:hover {
    background-color: #eaeaea;
}

/* Selected option */
div[role="radio"][aria-checked="true"] {
    background-color: white;
    border: 1px solid e0e0e0;
    border-bottom: 2px solid white;
}
</style>
""", unsafe_allow_html=True)

# Load page selector
page = st.radio(
    "Navigation",
    ["📊 Dashboard", "🧪 Backtest", "🧠 Evaluation", "ℹ️ Dataset Info", "⚙️ Settings"],
    horizontal=True,
    key="page",
    label_visibility="collapsed",
)

# Load sidebar
sidebar.run()

# Load selected page
if page == "📊 Dashboard":
    dashboard.run()

elif page == "🧪 Backtest":
    backtest.run()

elif page == "🧠 Evaluation":
    evaluation.run()

elif page == "ℹ️ Dataset Info":
    st.info("Dataset info is not yet implemented")

elif page == "⚙️ Settings":
    st.info("Settings is not yet implemented")
