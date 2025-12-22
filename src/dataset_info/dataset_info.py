

# Mostrar resumen y controles principales
st.sidebar.markdown("### Estado del dataset")
st.sidebar.write(f"Registros: {len(df)}")
min_date, max_date = get_date_bounds(df, date_col=date_col)
st.sidebar.write(f"Fechas: {min_date.date()} → {max_date.date()}")

# Botones de features: se muestran y ejecutan solo al hacer click
st.sidebar.markdown("### 3) Features (activa según quieras)")
if st.sidebar.button("Añadir time features"):
    st.session_state['df'] = add_basic_time_features(df, date_col=date_col)
    st.success("Features temporales añadidos")