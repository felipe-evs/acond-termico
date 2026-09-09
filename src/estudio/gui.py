import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import streamlit as st
import pandas as pd
from src.db.connection import init_db
from src.estudio.repository import EstudioRepository, SimulacionRepository
from src.shared.validators import TIPOLOGIAS_VALIDAS

st.set_page_config(page_title="Carga de Resultados - Fase 1", layout="wide")

init_db()

estudio = EstudioRepository.get()
if not estudio:
    EstudioRepository.init()
    estudio = EstudioRepository.get()

st.title("Carga de Resultados de Simulacion Termica")
st.markdown(f"**Estudio**: {estudio.nombre}" if estudio else "")

tab1, tab2, tab3, tab4 = st.tabs(["Carga Individual", "Importar CSV", "Listar Simulaciones", "Exportar"])

with tab1:
    with st.form("carga_individual"):
        col1, col2 = st.columns(2)
        with col1:
            tipologia = st.selectbox("Tipologia", TIPOLOGIAS_VALIDAS)
            zona_termica = st.selectbox("Zona Termica", range(1, 10))
            u_prom = st.number_input("U_prom (W/m2K)", min_value=0.5, max_value=5.0, value=2.5, step=0.1)
            demanda_anual = st.number_input("Demanda Anual (kWh/ano)", min_value=500.0, max_value=20000.0, value=8000.0)
        with col2:
            peak_demanda = st.number_input("Peak Demanda (kW)", min_value=1.0, max_value=20.0, value=5.0)
            gdc = st.number_input("GDC (grados dia)", min_value=200.0, max_value=4000.0, value=1500.0)
            descripcion = st.text_area("Descripcion/Caracterizacion")
            archivo_subido = st.file_uploader("Archivo modelo (opcional)", type=["idf", "eso", "htm"])
        submitted = st.form_submit_button("Guardar Simulacion")
        if submitted:
            data = {
                "tipologia": tipologia,
                "zona_termica": zona_termica,
                "u_prom": u_prom,
                "demanda_anual_kwh": demanda_anual,
                "peak_demanda_kw": peak_demanda,
                "gdc": gdc,
                "descripcion": descripcion,
                "archivo_modelo": archivo_modelo if archivo_modelo else None,
            }
            if archivo_subido is not None:
                import os
                os.makedirs("data/attachments", exist_ok=True)
                ruta_archivo = os.path.join("data/attachments", archivo_subido.name)
                with open(ruta_archivo, "wb") as f:
                    f.write(archivo_subido.getbuffer())
                data["archivo_modelo"] = ruta_archivo
            result, errores = SimulacionRepository.create(data)
            if errores:
                st.error("\n".join(errores))
            else:
                st.success(f"Simulacion {result.id} creada exitosamente!")

with tab2:
    st.subheader("Importar Simulaciones desde CSV")
    archivo = st.file_uploader("Seleccionar archivo CSV", type=["csv"])
    if archivo is not None:
        df = pd.read_csv(archivo)
        st.dataframe(df.head())
        if st.button("Importar"):
            simulaciones = df.to_dict("records")
            from src.estudio.csv_handler import importar_simulaciones
            importados, errores = SimulacionRepository.bulk_create(simulaciones)
            st.success(f"Importados: {importados}")
            if errores:
                st.warning(f"Errores: {len(errores)}")
                for e in errores:
                    st.write(e)

with tab3:
    st.subheader("Simulaciones Registradas")
    rows = SimulacionRepository.list()
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df)
        sim_ids = [r["id"] for r in rows]
        sim_id_to_del = st.selectbox("Seleccionar simulacion para eliminar", sim_ids)
        if st.button("Eliminar seleccionada"):
            SimulacionRepository.delete(sim_id_to_del)
            st.rerun()
    else:
        st.info("No hay simulaciones registradas.")

with tab4:
    st.subheader("Exportar Simulaciones")
    rows = SimulacionRepository.list()
    if rows:
        df = pd.DataFrame(rows)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", csv, "simulaciones.csv", "text/csv")
    else:
        st.info("No hay datos para exportar.")
