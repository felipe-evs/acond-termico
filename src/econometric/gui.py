import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", ".."))
import streamlit as st
import tempfile
import os
from src.db.connection import init_db
from src.econometric.engine import ejecutar_modelo
from src.db.connection import get_connection

init_db()

st.set_page_config(page_title="Modelo Econometrico - Fase 4", layout="wide")
st.title("Modelacion Econometrica y Validacion")

tab1, tab2 = st.tabs(["Ejecutar Modelo", "Resultados"])

with tab1:
    st.subheader("Cargar datos desde Feature 003")
    archivo = st.file_uploader("Seleccionar CSV de resultados de optimizacion", type=["csv"])
    if archivo is not None:
        st.success(f"Archivo cargado: {archivo.name}")
        if st.button("Ejecutar Modelo Econometrico", type="primary"):
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
                f.write(archivo.getbuffer())
                ruta = f.name
            with st.spinner("Estimando modelo OLS y ejecutando tests..."):
                resultado = ejecutar_modelo(ruta)
            os.unlink(ruta)
            if resultado["status"] == "error":
                st.error(resultado.get("mensaje", "Error"))
            else:
                st.success(f"Modelo estimado. R2: {resultado['R2']:.4f}")
                st.metric("R2", f"{resultado['R2']:.4f}")
                st.metric("R2 ajustado", f"{resultado['R2_ajustado']:.4f}")
                st.metric("ECM", f"{resultado['ECM']:.2f}")
                st.metric("Tests aprobados", f"{resultado['tests_aprobados']}/{resultado['total_tests']}")
                val = "VALIDADO" if resultado["validacion"] == "validado" else "NO VALIDADO"
                st.metric("Estado", val)

with tab2:
    st.subheader("Resultados del modelo")
    conn = get_connection()
    cur = conn.execute("SELECT * FROM eco_modelo ORDER BY id DESC LIMIT 1")
    modelo = cur.fetchone()
    if modelo:
        st.json(dict(modelo))
        mid = modelo["id"]
        cur = conn.execute("SELECT * FROM eco_coeficiente WHERE modelo_id=?", (mid,))
        coefs = cur.fetchall()
        if coefs:
            st.write("**Coeficientes:**")
            for c in coefs:
                st.write(f"- {c['variable_nombre']}: beta={c['beta']:.4f}, t={c['t_statistic']:.2f}, p={c['pvalue']:.4f}, VIF={c['VIF']}")
        cur = conn.execute("SELECT * FROM eco_test_diagnostico WHERE modelo_id=?", (mid,))
        tests = cur.fetchall()
        if tests:
            st.write("**Tests de diagnostico:**")
            for t in tests:
                st.write(f"- {t['test_nombre']}: estadistico={t['estadistico']:.4f}, pvalue={t['pvalue']:.4f}, **{t['resultado'].upper()}**")
        cur = conn.execute("SELECT * FROM eco_validacion WHERE modelo_id=?", (mid,))
        val = cur.fetchone()
        if val:
            st.write(f"**Validacion**: {val['resultado_global'].upper()}")
            if val["razon_rechazo"]:
                st.warning(val["razon_rechazo"])
    else:
        st.info("Ejecute el modelo primero.")
    conn.close()
