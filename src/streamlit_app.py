import streamlit as st
import os
from src.sidebar import sidebar
from src.dashboard import dashboard
from src.backtest import backtest

st.session_state['PROJECT_DIR'] = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Leverage Strategy", page_icon="📈", layout="wide")

st.title("📈 Leverage Strategy")

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
    ["📊 Dashboard", "🧪 Backtest", "ℹ️ Dataset Info", "⚙️ Settings"],
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

elif page == "ℹ️ Dataset Info":
    st.info("Dataset info is not yet implemented")

elif page == "⚙️ Settings":
    st.info("Settings is not yet implemented")



# --- MAIN SECTION WITH FILTERS AND PLOTS ---
#st.header("2) Filtrado y exploración")

# Slider por días para filtrar (int) — así el usuario puede moverse rápidamente
#min_day = int(df['Days'].min())
#max_day = int(df['Days'].max())
#start_day, end_day = st.slider("Rango (Days) — usa el slider para moverte entre fechas", min_value=min_day, max_value=max_day, value=(min_day, max_day), step=1)
#start_date = (df[date_col].min() + pd.Timedelta(days=start_day)).date()
#end_date = (df[date_col].min() + pd.Timedelta(days=end_day)).date()

#filtered = df[(df['Days'] >= start_day) & (df['Days'] <= end_day)].copy()
#st.write(f"Registros en rango: {len(filtered)} — {start_date} a {end_date}")








#numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
#if numeric_cols:
#    selected_col = st.selectbox("Columna numérica a graficar", options=numeric_cols)
#    st.plotly_chart(plot_timeseries(df, date_col=date_col, value_col=selected_col, title=f"{selected_col} en rango seleccionado"), use_container_width=True)
#else:
#    st.info("No hay columnas numéricas para graficar en el dataset filtrado.")



# Footer: opciones de export
