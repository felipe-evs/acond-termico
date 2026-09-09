import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import streamlit as st
import pandas as pd
from src.db.connection import init_db
from src.optimizer.solver import ejecutar_optimizacion, ParametroRepository, ResultadoRepository

init_db()

st.set_page_config(page_title="Optimizacion MILP - Fase 3", layout="wide")
st.title("Optimizacion MILP - Seleccion Optima de Equipos")

tab1, tab2, tab3 = st.tabs(["Ejecutar", "Configuracion", "Resultados"])

with tab1:
    st.subheader("Ejecutar Optimizacion")
    st.markdown("Resuelve el modelo MILP para los 36 escenarios (4 tipologias x 9 zonas).")
    if st.button("Ejecutar Optimizacion", type="primary"):
        with st.spinner("Resolviendo MILP..."):
            resultado = ejecutar_optimizacion()
        if resultado["status"] == "completed":
            st.success(f"Optimizacion completada: {resultado['escenarios_resueltos']}/{resultado['total_escenarios']} escenarios resueltos")
        else:
            st.error(resultado.get("mensaje", "Error en la optimizacion"))

with tab2:
    st.subheader("Parametros Economicos")
    params = ParametroRepository.get()
    with st.form("config_params"):
        tasa = st.number_input("Tasa de descuento (%)", 0.0, 100.0, params["tasa_descuento_pct"], 0.1)
        vida = st.number_input("Vida util (anos)", 1, 50, params["vida_util_anos"], 1)
        perdida = st.number_input("Perdida sistemica (%)", 0.0, 100.0, params["perdida_sistemica_pct"], 0.1)
        if st.form_submit_button("Guardar"):
            ParametroRepository.update(tasa, vida, perdida)
            st.success("Parametros actualizados!")

with tab3:
    st.subheader("Resultados")
    zona_filtro = st.selectbox("Filtrar por zona", ["Todas"] + list(range(1, 10)))
    zona = None if zona_filtro == "Todas" else zona_filtro
    rows = ResultadoRepository.list(zona)
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", csv, "resultados_optimizacion.csv", "text/csv")
    else:
        st.info("Ejecute la optimizacion primero para ver resultados.")
