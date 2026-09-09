#!/usr/bin/env python3
"""
Portal Principal: Sistema de Evaluación y Climatización Residencial HVAC
========================================================================
Aplicación interactiva Streamlit para explorar:
1. Catálogo completo de 653 equipos HVAC con precios actualizados y especificaciones 2026.
2. Precios de energía investigados por Zona Térmica y Ciudad (Tabla 2 y rangos comerciales).
3. Matriz de Elección y Costo por Gcal.
4. Módulos de Simulación Térmica, Optimización MILP y Modelo Econométrico.
"""

import os
import sys
import sqlite3
import pandas as pd
import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.db.connection import get_connection, init_db
from src.hvac.matrix import calcular_matriz
from src.optimizer.reader import leer_parametros
from src.optimizer.solver import ejecutar_optimizacion, ResultadoRepository, ParametroRepository
from src.estudio.repository import EstudioRepository, SimulacionRepository

# Page configuration
st.set_page_config(
    page_title="Evaluación Energética HVAC Chile",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .main-title {
        color: #1E3A8A;
        font-weight: 700;
    }
    .badge-chip {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def load_catalog_data():
    conn = get_connection()
    query = """
        SELECT e.id, e.id_solotodo, e.marca, e.modelo, t.nombre as tecnologia, c.nombre as combustible,
               e.potencia_nominal_kw, e.rendimiento_termico_pct, e.cop_calor,
               e.costo_adquisicion_clp, e.tasa_consumo, e.unidad_tasa_consumo,
               e.costo_instalacion_clp, e.costo_mantencion_anual_clp,
               e.poder_calorifico_bruto, e.rango_calefaccion, e.tienda, e.url_tienda,
               e.fuente_datos, e.url_fuente, e.otros
        FROM hvac_equipo e
        JOIN hvac_tipo_tecnologia t ON e.tipo_tecnologia_id = t.id
        JOIN hvac_combustible c ON e.combustible_id = c.id
        ORDER BY e.costo_adquisicion_clp DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def load_energy_prices_matrix():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM hvac_matriz_precio_zona ORDER BY zona_termica", conn)
    conn.close()
    return df


def load_detailed_prices():
    conn = get_connection()
    query = """
        SELECT p.id, p.zona_termica, p.ciudad, p.region, c.nombre as combustible,
               p.unidad_comercial, p.precio_min_comercial, p.precio_max_comercial,
               p.precio_prom_comercial, p.divisor_conversion, p.precio_por_unidad,
               c.unidad_medida as unidad_base, p.fecha_vigencia, p.fuente
        FROM hvac_precio_combustible p
        JOIN hvac_combustible c ON p.combustible_id = c.id
        ORDER BY p.zona_termica, c.nombre
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# ------------------------- SIDEBAR NAVIGATION -------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1513694203232-719a280e022f?w=400&q=80", use_container_width=True)
    st.title("Climatización Residencial")
    st.caption("Estudio Energético y CAE - Chile 2026")
    st.markdown("---")

    menu_option = st.radio(
        "Navegación del Sistema:",
        [
            "🏪 Catálogo de Equipos HVAC (653)",
            "💰 Precios de Energía por Zona (Tabla 2)",
            "📊 Matriz de Elección CAE por Gcal",
            "📐 Simulaciones Térmicas (Fase 1)",
            "⚙️ Optimizador MILP (Fase 3)",
            "📈 Modelo Econométrico (Fase 4)",
        ],
        index=0,
    )
    st.markdown("---")
    st.markdown("💡 **Servidor Activo**: `192.168.1.90:8501`")
    st.caption("Base de datos: `acond-termico.db` (SQLite)")


# =====================================================================
# VISTA 1: CATÁLOGO DE EQUIPOS HVAC
# =====================================================================
if menu_option == "🏪 Catálogo de Equipos HVAC (653)":
    st.markdown("<h2 class='main-title'>Catálogo de Equipos de Climatización y Calefacción</h2>", unsafe_allow_html=True)
    st.markdown("Base de datos de **653 modelos vigentes** en el mercado chileno extraídos desde SoloTodo.cl, valorizados con el **precio más alto de lista c/IVA** entre comercios y especificaciones técnicas normalizadas.")

    df_equipos = load_catalog_data()

    # Metrics Summary
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    with col_m1:
        st.metric("Total Equipos", f"{len(df_equipos):,}")
    with col_m2:
        st.metric("Marcas Únicas", f"{df_equipos['marca'].nunique()}")
    with col_m3:
        st.metric("Precio Mínimo", f"${df_equipos['costo_adquisicion_clp'].min():,.0f}")
    with col_m4:
        st.metric("Precio Mediano", f"${df_equipos['costo_adquisicion_clp'].median():,.0f}")
    with col_m5:
        st.metric("Precio Máximo", f"${df_equipos['costo_adquisicion_clp'].max():,.0f}")

    st.markdown("---")

    # Filters
    st.subheader("🔍 Filtros y Búsqueda de Equipos")
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 3])

    with f_col1:
        tec_options = ["Todas"] + sorted(df_equipos["tecnologia"].unique().tolist())
        sel_tec = st.selectbox("Tecnología", tec_options)

    with f_col2:
        comb_options = ["Todos"] + sorted(df_equipos["combustible"].unique().tolist())
        sel_comb = st.selectbox("Combustible", comb_options)

    with f_col3:
        marcas_disponibles = sorted(df_equipos["marca"].dropna().unique().tolist())
        sel_marcas = st.multiselect("Filtrar Marca(s)", marcas_disponibles, placeholder="Todas las marcas")

    with f_col4:
        search_query = st.text_input("Buscar por Modelo / Descripción", placeholder="Ej. KS-27, Inverter, Bosca, Midea...")

    # Price range slider
    p_min_val = float(df_equipos["costo_adquisicion_clp"].min())
    p_max_val = float(df_equipos["costo_adquisicion_clp"].max())
    rango_precios = st.slider(
        "Rango de Precio de Adquisición c/IVA (CLP)",
        min_value=p_min_val,
        max_value=p_max_val,
        value=(p_min_val, p_max_val),
        step=10000.0,
        format="$%d",
    )

    # Apply filters
    filtered_df = df_equipos.copy()
    if sel_tec != "Todas":
        filtered_df = filtered_df[filtered_df["tecnologia"] == sel_tec]
    if sel_comb != "Todos":
        filtered_df = filtered_df[filtered_df["combustible"] == sel_comb]
    if sel_marcas:
        filtered_df = filtered_df[filtered_df["marca"].isin(sel_marcas)]
    if search_query:
        q = search_query.lower()
        filtered_df = filtered_df[
            filtered_df["modelo"].str.lower().str.contains(q, na=False) |
            filtered_df["marca"].str.lower().str.contains(q, na=False) |
            filtered_df["otros"].str.lower().str.contains(q, na=False) |
            filtered_df["tienda"].str.lower().str.contains(q, na=False)
        ]
    filtered_df = filtered_df[
        (filtered_df["costo_adquisicion_clp"] >= rango_precios[0]) &
        (filtered_df["costo_adquisicion_clp"] <= rango_precios[1])
    ]

    st.markdown(f"**Resultados encontrados:** {len(filtered_df)} de {len(df_equipos)} equipos")

    # Display interactive dataframe
    display_cols = [
        "id", "marca", "modelo", "tecnologia", "combustible",
        "potencia_nominal_kw", "rendimiento_termico_pct", "cop_calor",
        "costo_adquisicion_clp", "tienda", "costo_instalacion_clp", "costo_mantencion_anual_clp"
    ]

    st.dataframe(
        filtered_df[display_cols].rename(columns={
            "id": "ID",
            "marca": "Marca",
            "modelo": "Modelo",
            "tecnologia": "Tecnología",
            "combustible": "Combustible",
            "potencia_nominal_kw": "Potencia (kW)",
            "rendimiento_termico_pct": "Rend. (%)",
            "cop_calor": "COP Calor",
            "costo_adquisicion_clp": "Precio c/IVA (CLP)",
            "tienda": "Tienda Precio Máx",
            "costo_instalacion_clp": "Instalación (CLP)",
            "costo_mantencion_anual_clp": "Mantención Anual (CLP)",
        }),
        column_config={
            "Precio c/IVA (CLP)": st.column_config.NumberColumn(format="$ %d"),
            "Instalación (CLP)": st.column_config.NumberColumn(format="$ %d"),
            "Mantención Anual (CLP)": st.column_config.NumberColumn(format="$ %d"),
            "Potencia (kW)": st.column_config.NumberColumn(format="%.2f kW"),
            "Rend. (%)": st.column_config.NumberColumn(format="%.1f%%"),
            "COP Calor": st.column_config.NumberColumn(format="%.2f"),
        },
        use_container_width=True,
        height=450,
    )

    # Detailed item inspector
    st.markdown("### 📋 Ficha Técnica Detallada")
    if not filtered_df.empty:
        selected_id = st.selectbox(
            "Seleccione un equipo para ver su ficha completa:",
            filtered_df["id"].tolist(),
            format_func=lambda x: f"ID {x}: {filtered_df.loc[filtered_df['id'] == x, 'marca'].values[0]} {filtered_df.loc[filtered_df['id'] == x, 'modelo'].values[0]} (${filtered_df.loc[filtered_df['id'] == x, 'costo_adquisicion_clp'].values[0]:,.0f} CLP)",
        )
        item = filtered_df[filtered_df["id"] == selected_id].iloc[0]

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            st.markdown(f"**Marca:** {item['marca']}")
            st.markdown(f"**Modelo:** {item['modelo']}")
            st.markdown(f"**Tecnología:** `{item['tecnologia']}`")
            st.markdown(f"**Combustible:** `{item['combustible']}`")
            st.markdown(f"**Potencia Nominal:** `{item['potencia_nominal_kw']:.2f} kW`")
            if pd.notna(item["cop_calor"]) and item["cop_calor"] > 0:
                st.markdown(f"**COP Modo Calor:** `{item['cop_calor']:.2f}`")
            st.markdown(f"**Rendimiento Térmico:** `{item['rendimiento_termico_pct']:.1f}%`")
        with fc2:
            st.markdown(f"**Precio Máx c/IVA:** `${item['costo_adquisicion_clp']:,.0f} CLP`")
            st.markdown(f"**Tienda Oferente:** {item['tienda']}")
            st.markdown(f"**Costo Instalación:** `${item['costo_instalacion_clp']:,.0f} CLP`")
            st.markdown(f"**Costo Mantención Anual:** `${item['costo_mantencion_anual_clp']:,.0f} CLP`")
            st.markdown(f"**Tasa Consumo Nominal:** `{item['tasa_consumo']} {item['unidad_tasa_consumo']}`")
            st.markdown(f"**Rango de Calefacción:** {item['rango_calefaccion']}")
        with fc3:
            st.markdown(f"**Poder Calorífico Bruto:** {item['poder_calorifico_bruto']}")
            st.markdown(f"**Notas Técnicas y Logística:**")
            st.info(item["otros"] if pd.notna(item["otros"]) else "Sin notas adicionales.")
            if item["url_tienda"]:
                st.link_button("🌐 Ver Ficha en Tienda", item["url_tienda"])
            if item["url_fuente"] and item["url_fuente"] != item["url_tienda"]:
                st.link_button("🔗 Enlace de Referencia", item["url_fuente"])

    # CSV Download Button
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Descargar Catálogo Filtrado en CSV",
        data=csv_bytes,
        file_name="catalogo_hvac_solotodo_filtrado.csv",
        mime="text/csv",
    )


# =====================================================================
# VISTA 2: PRECIOS DE ENERGÍA (TABLA 2)
# =====================================================================
elif menu_option == "💰 Precios de Energía por Zona (Tabla 2)":
    st.markdown("<h2 class='main-title'>Costos de Fuentes de Energía por Zona Térmica y Ciudad</h2>", unsafe_allow_html=True)
    st.markdown("Investigación de precios de mercado consolidada para las **9 ciudades / zonas térmicas de referencia** (Zonas A a I) para las 6 fuentes energéticas del estudio.")

    ptab1, ptab2, ptab3 = st.tabs(["Tabla 2 Oficial (Unidad Base)", "Cotizaciones Comerciales Detalladas", "Comparativa Gráfica por Ciudad"])

    df_matrix = load_energy_prices_matrix()
    df_detalles = load_detailed_prices()

    with ptab1:
        st.subheader("Tabla 2. Matriz de Precios Base por Zona Térmica y Ciudad de Referencia")
        st.caption("Valores expresados en pesos chilenos (CLP) por unidad física base requerida por los modelos termodinámicos y el solver MILP.")

        st.dataframe(
            df_matrix[[
                "zona_termica", "ciudad", "region", "electricidad_clp_kwh", "kerosene_clp_litro",
                "glp_clp_kg", "gas_natural_clp_m3", "lena_clp_kg", "pellet_clp_kg"
            ]].rename(columns={
                "zona_termica": "Zona",
                "ciudad": "Ciudad de Referencia",
                "region": "Región",
                "electricidad_clp_kwh": "Electricidad [$/kWh]",
                "kerosene_clp_litro": "Kerosene [$/L]",
                "glp_clp_kg": "GLP [$/kg]",
                "gas_natural_clp_m3": "Gas Natural [$/m³]",
                "lena_clp_kg": "Leña [$/kg]*",
                "pellet_clp_kg": "Pellet [$/kg]",
            }),
            column_config={
                "Electricidad [$/kWh]": st.column_config.NumberColumn(format="$ %.2f"),
                "Kerosene [$/L]": st.column_config.NumberColumn(format="$ %.2f"),
                "GLP [$/kg]": st.column_config.NumberColumn(format="$ %.2f"),
                "Gas Natural [$/m³]": st.column_config.NumberColumn(format="$ %.2f"),
                "Leña [$/kg]*": st.column_config.NumberColumn(format="$ %.2f"),
                "Pellet [$/kg]": st.column_config.NumberColumn(format="$ %.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )
        st.caption("*Leña normalizada considerando saco comercial de 25 kg con humedad <= 25%.")

        csv_mat = df_matrix.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Descargar Tabla 2 en CSV", csv_mat, "tabla2_matriz_precios_zonas.csv", "text/csv")

    with ptab2:
        st.subheader("Cotizaciones Comerciales con Rangos Min / Max / Promedio")
        st.caption("Precios comerciales en sus unidades de venta habituales (Cilindros de 15 kg, Sacos de leña, Bolsas de pellet de 15 kg, Litros, kWh y m³).")

        st.dataframe(
            df_detalles[[
                "zona_termica", "ciudad", "combustible", "unidad_comercial",
                "precio_min_comercial", "precio_max_comercial", "precio_prom_comercial",
                "divisor_conversion", "precio_por_unidad", "unidad_base"
            ]].rename(columns={
                "zona_termica": "Zona",
                "ciudad": "Ciudad",
                "combustible": "Combustible",
                "unidad_comercial": "Unidad Comercial",
                "precio_min_comercial": "Precio Mín",
                "precio_max_comercial": "Precio Máx",
                "precio_prom_comercial": "Precio Promedio",
                "divisor_conversion": "Divisor a Base",
                "precio_por_unidad": "Precio $/Unidad Base",
                "unidad_base": "Unidad Base",
            }),
            column_config={
                "Precio Mín": st.column_config.NumberColumn(format="$ %d"),
                "Precio Máx": st.column_config.NumberColumn(format="$ %d"),
                "Precio Promedio": st.column_config.NumberColumn(format="$ %d"),
                "Precio $/Unidad Base": st.column_config.NumberColumn(format="$ %.2f"),
            },
            use_container_width=True,
            height=500,
        )

        csv_det = df_detalles.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Descargar Detalle Comercial en CSV", csv_det, "cotizaciones_energia_detalladas.csv", "text/csv")

    with ptab3:
        st.subheader("Comparativa Visual de Costos por Ciudad")
        ciudades_lista = df_matrix["ciudad"].tolist()
        sel_c = st.selectbox("Seleccione Ciudad para Analizar:", ciudades_lista)

        c_data = df_detalles[df_detalles["ciudad"] == sel_c]
        if not c_data.empty:
            tipo_grafico = st.radio(
                "Modalidad de Comparación Visual:",
                [
                    "🔬 Costo Normalizado por Energía Térmica Útil ($/kWh_t) [Recomendado]",
                    "⚖️ Costo por Unidad Base Física ($/kg, $/L, $/m³, $/kWh)",
                    "🛒 Cotizaciones Comerciales de Venta al Público (Unidades Mixtas)",
                ],
                horizontal=True,
            )

            pci_kwh = {
                "electricidad": 1.0,
                "parafina": 9.93,
                "gas_licuado": 12.66,
                "gas_natural": 9.91,
                "lena": 3.87,
                "pellet": 3.87,
            }
            rend_ref = {
                "electricidad": 1.0,
                "parafina": 0.90,
                "gas_licuado": 0.85,
                "gas_natural": 0.90,
                "lena": 0.65,
                "pellet": 0.85,
            }

            if "🔬 Costo Normalizado" in tipo_grafico:
                st.caption("Muestra el costo en pesos chilenos para entregar **1 kWh de calor útil** al recinto, integrando el poder calorífico (PCI) y el rendimiento térmico nominal. Resuelve la distorsión del cilindro de 15 kg al evaluar la energía neta aprovechada.")
                chart_df = c_data[["combustible", "precio_min_comercial", "precio_prom_comercial", "precio_max_comercial", "divisor_conversion"]].copy()

                def to_thermal_kwh(val, comb, div):
                    if pd.isna(val) or val is None:
                        return 0.0
                    p_base = float(val) / float(div or 1.0)
                    pci = pci_kwh.get(comb, 1.0)
                    rend = rend_ref.get(comb, 0.85)
                    return round(p_base / (pci * rend), 1)

                chart_df["Min [$/kWh_t]"] = chart_df.apply(lambda r: to_thermal_kwh(r["precio_min_comercial"], r["combustible"], r["divisor_conversion"]), axis=1)
                chart_df["Promedio [$/kWh_t]"] = chart_df.apply(lambda r: to_thermal_kwh(r["precio_prom_comercial"], r["combustible"], r["divisor_conversion"]), axis=1)
                chart_df["Máx [$/kWh_t]"] = chart_df.apply(lambda r: to_thermal_kwh(r["precio_max_comercial"], r["combustible"], r["divisor_conversion"]), axis=1)

                elec_rows = chart_df[chart_df["combustible"] == "electricidad"]
                if not elec_rows.empty:
                    er = elec_rows.iloc[0]
                    split_row = {
                        "combustible": "bomba_calor_split",
                        "precio_min_comercial": er["precio_min_comercial"],
                        "precio_prom_comercial": er["precio_prom_comercial"],
                        "precio_max_comercial": er["precio_max_comercial"],
                        "divisor_conversion": 1.0,
                        "Min [$/kWh_t]": round(er["Min [$/kWh_t]"] / 3.2, 1),
                        "Promedio [$/kWh_t]": round(er["Promedio [$/kWh_t]"] / 3.2, 1),
                        "Máx [$/kWh_t]": round(er["Máx [$/kWh_t]"] / 3.2, 1),
                    }
                    chart_df = pd.concat([chart_df, pd.DataFrame([split_row])], ignore_index=True)

                labels_map = {
                    "electricidad": "Electricidad (Resistivo η=100%)",
                    "bomba_calor_split": "Electricidad (Split Inverter COP=3.2)",
                    "parafina": "Kerosene / Parafina (η=90%)",
                    "gas_licuado": "Gas Licuado GLP (η=85%)",
                    "gas_natural": "Gas Natural (η=90%)",
                    "pellet": "Pellet Biomasa (η=85%)",
                    "lena": "Leña Biomasa (η=65%)",
                }
                chart_df["Rótulo"] = chart_df["combustible"].map(labels_map).fillna(chart_df["combustible"])
                st.bar_chart(chart_df.set_index("Rótulo")[["Min [$/kWh_t]", "Promedio [$/kWh_t]", "Máx [$/kWh_t]"]])

            elif "⚖️ Costo por Unidad Base" in tipo_grafico:
                st.caption("Precios unitarios en las unidades físicas base ($/kg para GLP, leña y pellet; $/L para kerosene; $/m³ para gas natural; $/kWh para electricidad). El GLP se expresa en $/kg ($1.600 - $2.000/kg) en lugar de $25.000 por cilindro, permitiendo visualizar todas las fuentes en la misma escala.")
                chart_df = c_data[["combustible", "precio_min_comercial", "precio_prom_comercial", "precio_max_comercial", "divisor_conversion", "unidad_base"]].copy()
                chart_df["Min [$/Unidad Base]"] = (chart_df["precio_min_comercial"] / chart_df["divisor_conversion"]).round(1)
                chart_df["Promedio [$/Unidad Base]"] = (chart_df["precio_prom_comercial"] / chart_df["divisor_conversion"]).round(1)
                chart_df["Máx [$/Unidad Base]"] = (chart_df["precio_max_comercial"] / chart_df["divisor_conversion"]).round(1)
                chart_df["Rótulo"] = chart_df["combustible"].str.upper() + " ($/" + chart_df["unidad_base"] + ")"
                st.bar_chart(chart_df.set_index("Rótulo")[["Min [$/Unidad Base]", "Promedio [$/Unidad Base]", "Máx [$/Unidad Base]"]])

            else:
                st.info("ℹ️ **Nota sobre la distorsión de escala comercial:** El Gas Licuado (GLP) se comercializa en cilindros de 15 kg ($23.000 a $30.600 CLP), mientras que la electricidad se comercializa por kWh individual ($220 a $310 CLP) y el kerosene por litro (~$1.050 CLP). Al graficar valores brutos comerciales en un solo eje, la magnitud del cilindro de GLP aplasta visualmente a los demás combustibles. Se recomienda usar la pestaña de **Costo Normalizado** o **Unidad Base**.")
                mcols = st.columns(min(len(c_data), 4))
                for idx, (_, row) in enumerate(c_data.iterrows()):
                    with mcols[idx % len(mcols)]:
                        st.metric(
                            label=f"{row['combustible'].title()} ({row['unidad_comercial']})",
                            value=f"${row['precio_prom_comercial']:,.0f}",
                            delta=f"Rango: ${row['precio_min_comercial']:,.0f} - ${row['precio_max_comercial']:,.0f}",
                        )
                chart_df = c_data[["combustible", "precio_min_comercial", "precio_prom_comercial", "precio_max_comercial", "unidad_comercial"]].copy()
                chart_df["Rótulo"] = chart_df["combustible"] + " (" + chart_df["unidad_comercial"] + ")"
                st.bar_chart(chart_df.set_index("Rótulo")[["precio_min_comercial", "precio_prom_comercial", "precio_max_comercial"]])


# =====================================================================
# VISTA 3: MATRIZ DE ELECCIÓN CAE POR GCAL Y ANÁLISIS ECONÓMICO
# =====================================================================
elif menu_option == "📊 Matriz de Elección CAE por Gcal":
    st.markdown("<h2 class='main-title'>Matriz de Elección y Costo por Gcal Útil</h2>", unsafe_allow_html=True)
    st.markdown("Evaluación tecno-económica integral del ciclo de vida para los **653 equipos HVAC**, calculando Costos Fijos Anualizados, Costos Variables por Gcal/kWh, Gasto Horario y LCOH.")

    # -------------------------------------------------------------
    # EXPANDER PEDAGÓGICO: METODOLOGÍA, FÓRMULAS Y RESPUESTAS
    # -------------------------------------------------------------
    with st.expander("📘 Fundamento Metodológico: ¿Cómo se calculan el CAE, LCOH y Costos Fijos/Variables?", expanded=False):
        st.markdown("""
        ### 1. ¿Cómo se utiliza la Tasa de Descuento ($r$)?
        La tasa de descuento representa el **costo de oportunidad del capital** o la tasa social de preferencia temporal (MIDESO fija habitualmente un 6% u 8% para proyectos sociales; en evaluación familiar privada suele ubicarse entre 8% y 12%).
        
        Permite convertir una inversión inicial única ($I_{\\text{adquisición}} + C_{\\text{instalación}}$) en una **cuota anual equivalente** a lo largo de los $N$ años de vida útil del calefactor mediante el **Factor de Recuperación de Capital (FRC)**:
        
        $$FRC(r, N) = \\frac{r \\cdot (1 + r)^N}{(1 + r)^N - 1}$$
        
        * **Ejemplo Práctico:** Con $r = 8\\%$ y vida útil $N = 15\\text{ años}$, el $FRC \\approx 0{,}1168$. Esto significa que por cada \\$1.000.000 invertido en comprar e instalar el sistema, el costo de amortización anualizado es de **\\$116.829 al año**.
        * **Impacto en la Selección:** Una tasa de descuento alta castiga a las tecnologías eficientes de mayor inversión inicial (como Bombas de Calor / Split Inverter o estufas a pellet), favoreciendo erróneamente a artefactos muy baratos de comprar pero carísimos de operar (como termoventiladores o estufas halógenas).
        
        ---
        
        ### 2. ¿Cómo se calculan los Costos Fijos Anualizados ($C_{\\text{fijo}}$)?
        Agrupan todos los costos que no dependen de cuántas horas funcione el equipo en el invierno:
        
        $$C_{\\text{fijo}} = N_{\\text{equipos}} \\times \\left[ (I_{\\text{adquisición}} + C_{\\text{instalación}}) \\times FRC(r, N) + C_{\\text{mantención anual}} \\right] \\quad [\\$/\\text{año}]$$
        
        * **$I_{\\text{adquisición}}$:** Precio de compra en el comercio minorista c/IVA (rescatado de SoloTodo al precio vigente más alto del mercado para resguardar holgura presupuestaria).
        * **$C_{\\text{instalación}}$:** Costo de instalación técnica (\\$100.000 para Splits Inverter; \\$120.000 para estufas a pellet y leña por cañones y pasamuros; \\$0 para estufas móviles).
        * **$C_{\\text{mantención anual}}$:** Costo de inspección preventiva anual, limpieza de filtros/quemadores y deshollinado SEC (\\$10.000 a \\$45.000/año según tecnología).
        * **$N_{\\text{equipos}}$:** Número de unidades requeridas según la demanda peak de la vivienda (ver punto 4).
        
        ---
        
        ### 3. ¿Cómo se calculan los Costos Variables ($C_{\\text{variable}}$)?
        Representan el gasto directo en energía por cada unidad de calor útil transferido al espacio interior habitado.
        
        Sabiendo que $1\\text{ Gcal} = 1.000.000\\text{ kcal} = 1.162{,}79\\text{ kWh}_{\\text{térmicos}}$:
        
        $$C_{\\text{var, kWh}} = \\frac{P_{\\text{combustible}}}{PCI \\times \\eta} \\quad [\\$/\\text{kWh}_t] \\qquad \\text{y} \\qquad C_{\\text{var, Gcal}} = C_{\\text{var, kWh}} \\times 1.162{,}79 \\quad [\\$/\\text{Gcal}]$$
        
        * **$P_{\\text{combustible}}$:** Precio unitario de la energía en la ciudad o zona térmica seleccionada (Tabla 2).
        * **$PCI$:** Poder Calorífico Inferior del combustible en $\\text{kWh/unidad}$ (Electricidad: 1.0, Parafina: 9.93, GLP: 12.66, Gas Natural: 9.91, Pellet: 3.87, Leña: 3.87).
        * **$\\eta$ / COP:** Rendimiento térmico real del equipo. En Bombas de Calor (Split Inverter), se utiliza el **$COP$ en modo calefacción** (3.0 a 4.2), lo que reduce el consumo eléctrico a $1/COP$.
        
        ---
        
        ### 4. ¿Cómo se incorpora la Potencia ($P_{\\text{nominal}}$) en los análisis?
        La potencia nominal de un calefactor (kW) no debe evaluarse de forma aislada; debe compararse contra la **Demanda Térmica Peak de la Vivienda ($P_{\\text{peak}}$ en kW)**:
        
        1. **Número de Equipos Requeridos ($N_{\\text{equipos}}$):**
           $$N_{\\text{equipos}} = \\max\\left(1, \\left\\lceil \\frac{P_{\\text{peak, vivienda}}}{P_{\\text{nominal, equipo}}} \\right\\rceil\\right)$$
           * *Ejemplo:* Si una vivienda social en Temuco requiere $5{,}0\\text{ kW}$ peak para no pasar frío y se evalúa un convector de $1{,}5\\text{ kW}$, se requieren $N = \\lceil 5{,}0 / 1{,}5 \\rceil = 4\\text{ convectores}$.
           * Esto multiplica automáticamente la inversión inicial ($4 \\times \\$35.000 = \\$140.000$) y el consumo total, evitando la falacia de creer que un artefacto pequeño es suficiente para calentar una casa completa.
        2. **Superficie Máxima Calefaccionable ($m^2$):**
           $$S_{\\text{máx}} = \\frac{P_{\\text{nominal}} \\times 1.000}{q_{\\text{específica}}} \\quad [m^2]$$
           Con $q_{\\text{específica}} \\approx 60\\text{ W/m}^2$ para viviendas sociales estándar aisladas.
        3. **Horas Equivalentes a Plena Carga ($FLH$):**
           $$FLH = \\frac{\\text{Demanda Anual [kWh]}}{P_{\\text{nominal}} \\times N_{\\text{equipos}}} \\quad [\\text{horas/año}]$$
        
        ---
        
        ### 5. ¿Qué otros cálculos avanzados se pueden realizar?
        * **LCOH (Levelized Cost of Heat / Costo Nivelado del Calor):** Costo total anual dividido por la demanda anual entregada:
          $$LCOH = \\frac{CAE_{\\text{total}}}{\\text{Demanda Anual [kWh}_t\\text{]}} \\quad [\\$/\\text{kWh}_t] \\qquad \\text{y en UF/kWh}_t = \\frac{LCOH}{\\text{Valor UF}}$$
          *(Métrica oficial exigida en el informe borrador de la investigación)*.
        * **Costo Operativo Horario a Potencia Nominal ($/hora):**
          $$C_{\\text{horario}} = \\text{Tasa de Consumo} \\times P_{\\text{combustible}} \\times N_{\\text{equipos}} \\quad [\\$/\\text{h}]$$
          Muestra en pesos cuánto cuesta tener el sistema encendido 1 hora a plena capacidad.
        * **Costo Anual Equivalente Total ($CAE_{\\text{total}}$ en $/año):**
          $$CAE_{\\text{total}} = C_{\\text{fijo anualizado}} + (C_{\\text{var, kWh}} \\times \\text{Demanda Anual [kWh]})$$
        * **Período de Retorno (Payback):** Tiempo necesario para recuperar la mayor inversión de un equipo eficiente mediante el ahorro operacional generado frente a una estufa base ineficiente.
        """)

    # -------------------------------------------------------------
    # CONTROLES INTERACTIVOS DE CONFIGURACIÓN
    # -------------------------------------------------------------
    st.markdown("### ⚙️ Parámetros de Simulación Económica y Demanda")
    
    ciudades_opt = ["Promedio Nacional", "Antofagasta", "Calama", "Valparaiso", "Santiago", "Concepcion", "Temuco", "Puerto Montt", "Los Andes", "Punta Arenas"]
    
    pcol1, pcol2, pcol3, pcol4 = st.columns(4)
    with pcol1:
        sel_ciudad_matriz = st.selectbox("Ciudad / Precios de Energía:", ciudades_opt, index=4)  # Default: Santiago
    with pcol2:
        tasa_val = st.number_input("Tasa de Descuento (%)", 0.0, 30.0, 8.0, step=0.5, help="Tasa de descuento anual (MIDESO usa 6-8%, evaluación privada 8-12%).")
    with pcol3:
        vida_val = st.number_input("Vida Útil (años)", 1, 30, 15, step=1, help="Horizonte de evaluación económica de los equipos.")
    with pcol4:
        valor_uf_val = st.number_input("Valor Unidad de Fomento (CLP)", 20000.0, 60000.0, 39000.0, step=500.0)

    pcol5, pcol6, pcol7 = st.columns(3)
    with pcol5:
        demanda_kwh_val = st.number_input(
            "Demanda Térmica Anual Residencial (kWh/año):",
            500.0, 50000.0, 6000.0, step=500.0,
            help="Demanda de calefacción anual de la vivienda social simulada (6.000 kWh ≈ 5,16 Gcal/año)."
        )
        st.caption(f"Equivalente a: **{demanda_kwh_val / 1162.79:.2f} Gcal/año** útiles.")
    with pcol6:
        preset_peak = st.selectbox(
            "Carga Peak Requerida por la Vivienda:",
            [
                "Demanda Peak 5.0 kW (Casa Social 60 m²)",
                "Demanda Peak 3.0 kW (Depto Social 45 m²)",
                "Demanda Peak 7.5 kW (Casa 80 m² - Zona Fría)",
                "Demanda Peak 10.0 kW (Zona Extrema Sur)",
                "Sin escala (1 equipo unitario)",
                "Ingresar Manualmente...",
            ],
            index=0,
        )
        if "5.0 kW" in preset_peak:
            peak_kw_val = 5.0
        elif "3.0 kW" in preset_peak:
            peak_kw_val = 3.0
        elif "7.5 kW" in preset_peak:
            peak_kw_val = 7.5
        elif "10.0 kW" in preset_peak:
            peak_kw_val = 10.0
        elif "Sin escala" in preset_peak:
            peak_kw_val = 0.0
        else:
            peak_kw_val = st.number_input("Peak Manual (kW):", 0.5, 30.0, 5.0, step=0.5)
    with pcol7:
        st.write("")
        st.write("")
        recalc_btn = st.button("🔄 Recalcular y Optimizar Matriz", type="primary", use_container_width=True)

    ciudad_param = None if sel_ciudad_matriz == "Promedio Nacional" else sel_ciudad_matriz

    # Ejecutar cálculo de la matriz ampliada
    matriz = calcular_matriz(
        tasa_descuento=tasa_val,
        vida_util=vida_val,
        ciudad=ciudad_param,
        demanda_anual_kwh=demanda_kwh_val,
        potencia_peak_kw=peak_kw_val if peak_kw_val > 0 else None,
        valor_uf=valor_uf_val,
    )

    if matriz:
        df_matriz = pd.DataFrame(matriz)

        # -------------------------------------------------------------
        # KPIS RESUMEN DEL MERCADO EVALUADO
        # -------------------------------------------------------------
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        best_lcoh = df_matriz.loc[df_matriz["lcoh_clp_kwh"].idxmin()]
        best_var = df_matriz.loc[df_matriz["costo_variable_por_gcal"].idxmin()]
        best_fijo = df_matriz.loc[df_matriz["costo_fijo_anualizado_clp"].idxmin()]

        with kpi1:
            st.metric(
                label="🌟 Menor LCOH (Costo Nivelado)",
                value=f"{best_lcoh['lcoh_uf_kwh']:.5f} UF/kWh",
                delta=f"${best_lcoh['lcoh_clp_kwh']:.1f} CLP/kWh ({best_lcoh['modelo'][:15]})",
            )
        with kpi2:
            st.metric(
                label="⚡ Menor Costo Variable",
                value=f"${best_var['costo_variable_por_gcal']:,.0f} /Gcal",
                delta=f"${best_var['costo_variable_por_kwh']:.1f}/kWh_t ({best_var['combustible']})",
            )
        with kpi3:
            st.metric(
                label="🏷️ Menor Costo Fijo Anualizado",
                value=f"${best_fijo['costo_fijo_anualizado_clp']:,.0f}/año",
                delta=f"{best_fijo['modelo'][:18]}",
            )
        with kpi4:
            st.metric(
                label="📊 Equipos Analizados",
                value=f"{len(df_matriz)} modelos",
                delta=f"Precios: {sel_ciudad_matriz}",
            )

        # -------------------------------------------------------------
        # FILTROS Y BÚSQUEDA EN LA MATRIZ
        # -------------------------------------------------------------
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            filt_tec = st.multiselect("Filtrar por Tecnología:", df_matriz["tecnologia"].unique().tolist())
        with fcol2:
            filt_comb = st.multiselect("Filtrar por Combustible:", df_matriz["combustible"].unique().tolist())
        with fcol3:
            filt_orden = st.selectbox(
                "Ordenar Tabla por:",
                [
                    "Costo Anual Total ($/año) [Menor a Mayor]",
                    "LCOH [UF/kWh_t] (Menor a Mayor)",
                    "Costo Variable ($/Gcal) [Menor a Mayor]",
                    "Costo Fijo Anualizado ($/año) [Menor a Mayor]",
                    "Potencia Nominal (kW) [Mayor a Menor]",
                ],
            )

        df_view = df_matriz.copy()
        if filt_tec:
            df_view = df_view[df_view["tecnologia"].isin(filt_tec)]
        if filt_comb:
            df_view = df_view[df_view["combustible"].isin(filt_comb)]

        if "Costo Anual Total" in filt_orden:
            df_view = df_view.sort_values("costo_anual_total_clp", ascending=True)
        elif "LCOH" in filt_orden:
            df_view = df_view.sort_values("lcoh_uf_kwh", ascending=True)
        elif "Costo Variable" in filt_orden:
            df_view = df_view.sort_values("costo_variable_por_gcal", ascending=True)
        elif "Costo Fijo" in filt_orden:
            df_view = df_view.sort_values("costo_fijo_anualizado_clp", ascending=True)
        elif "Potencia Nominal" in filt_orden:
            df_view = df_view.sort_values("potencia_nominal_kw", ascending=False)

        st.markdown(f"**Mostrando {len(df_view)} de {len(df_matriz)} alternativas evaluadas:**")

        st.dataframe(
            df_view[[
                "equipo_id", "marca", "modelo", "tecnologia", "combustible",
                "potencia_nominal_kw", "equipos_requeridos", "costo_fijo_anualizado_clp",
                "costo_variable_por_kwh", "costo_variable_por_gcal", "costo_hora_nominal_clp",
                "costo_anual_total_clp", "lcoh_clp_kwh", "lcoh_uf_kwh", "superficie_estimada_m2"
            ]].rename(columns={
                "equipo_id": "ID",
                "marca": "Marca",
                "modelo": "Modelo",
                "tecnologia": "Tecnología",
                "combustible": "Combustible",
                "potencia_nominal_kw": "Potencia (kW)",
                "equipos_requeridos": "N° Eq.",
                "costo_fijo_anualizado_clp": "Costo Fijo ($/año)",
                "costo_variable_por_kwh": "Costo Var ($/kWh_t)",
                "costo_variable_por_gcal": "Costo Var ($/Gcal)",
                "costo_hora_nominal_clp": "Gasto ($/hora)",
                "costo_anual_total_clp": "CAE Total ($/año)",
                "lcoh_clp_kwh": "LCOH ($/kWh_t)",
                "lcoh_uf_kwh": "LCOH (UF/kWh_t)",
                "superficie_estimada_m2": "Sup. Cubierta (m²)",
            }),
            column_config={
                "Potencia (kW)": st.column_config.NumberColumn(format="%.2f kW"),
                "Costo Fijo ($/año)": st.column_config.NumberColumn(format="$ %d"),
                "Costo Var ($/kWh_t)": st.column_config.NumberColumn(format="$ %.1f"),
                "Costo Var ($/Gcal)": st.column_config.NumberColumn(format="$ %d"),
                "Gasto ($/hora)": st.column_config.NumberColumn(format="$ %d /h"),
                "CAE Total ($/año)": st.column_config.NumberColumn(format="$ %d"),
                "LCOH ($/kWh_t)": st.column_config.NumberColumn(format="$ %.2f"),
                "LCOH (UF/kWh_t)": st.column_config.NumberColumn(format="%.5f UF"),
                "Sup. Cubierta (m²)": st.column_config.NumberColumn(format="%.1f m²"),
            },
            use_container_width=True,
            height=500,
        )

        # -------------------------------------------------------------
        # GRÁFICA COMPARATIVA TOP 10 MÁS CONVENIENTES
        # -------------------------------------------------------------
        st.markdown("### 🏆 Top 10 Alternativas con Menor Costo Anual Equivalente Total ($/año)")
        top10 = df_view.head(10).copy()
        top10["Rótulo"] = top10["marca"] + " " + top10["modelo"] + " (" + top10["tecnologia"] + ")"
        
        chart_top10 = top10.set_index("Rótulo")[["costo_fijo_anualizado_clp", "costo_anual_total_clp"]].rename(columns={
            "costo_fijo_anualizado_clp": "Costo Fijo Anualizado ($/año)",
            "costo_anual_total_clp": "CAE Total Anual ($/año)"
        })
        st.bar_chart(chart_top10)

        csv_m = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Descargar Matriz Económica Completa en CSV",
            csv_m,
            f"matriz_economica_hvac_{sel_ciudad_matriz.lower().replace(' ', '_')}.csv",
            "text/csv"
        )


# =====================================================================
# VISTA 4: SIMULACIONES TÉRMICAS (FASE 1)
# =====================================================================
elif menu_option == "📐 Simulaciones Térmicas (Fase 1)":
    st.markdown("<h2 class='main-title'>Resultados de Simulación Térmica (Fase 1)</h2>", unsafe_allow_html=True)
    estudio = EstudioRepository.get()
    st.info(f"**Estudio Activo:** {estudio.nombre if estudio else 'Sin estudio inicializado'}")

    conn = get_connection()
    sim_df = pd.read_sql("""
        SELECT s.id, s.tipologia, s.zona_termica, r.u_prom, r.demanda_anual_kwh, r.peak_demanda_kw, r.gdc, s.fecha_carga
        FROM sim_simulacion s
        JOIN sim_resultado r ON s.id = r.simulacion_id
        ORDER BY s.zona_termica, s.tipologia
    """, conn)
    conn.close()

    if not sim_df.empty:
        st.markdown(f"**Simulaciones registradas:** {len(sim_df)}")
        st.dataframe(
            sim_df.rename(columns={
                "id": "ID",
                "tipologia": "Tipología",
                "zona_termica": "Zona Térmica",
                "u_prom": "U Prom (W/m²K)",
                "demanda_anual_kwh": "Demanda Anual (kWh/año)",
                "peak_demanda_kw": "Peak Demanda (kW)",
                "gdc": "Grados Día (GDC)",
                "fecha_carga": "Fecha de Carga"
            }),
            column_config={
                "Demanda Anual (kWh/año)": st.column_config.NumberColumn(format="%d kWh"),
                "Peak Demanda (kW)": st.column_config.NumberColumn(format="%.2f kW"),
                "U Prom (W/m²K)": st.column_config.NumberColumn(format="%.2f"),
                "Grados Día (GDC)": st.column_config.NumberColumn(format="%d"),
            },
            use_container_width=True,
        )
    else:
        st.warning("No hay simulaciones cargadas en la tabla sim_simulacion.")


# =====================================================================
# VISTA 5: OPTIMIZADOR MILP (FASE 3)
# =====================================================================
elif menu_option == "⚙️ Optimizador MILP (Fase 3)":
    st.markdown("<h2 class='main-title'>Optimizador MILP: Selección de Equipos y CAE</h2>", unsafe_allow_html=True)
    st.markdown("Resuelve el modelo MILP para los escenarios de tipologías y zonas térmicas con el catálogo poblado de **653 equipos**.")

    otab1, otab2 = st.tabs(["Ejecutar Solver", "Resultados Históricos"])

    with otab1:
        st.subheader("Ejecución del Modelo de Optimización")
        if st.button("🚀 Ejecutar Optimización MILP", type="primary"):
            with st.spinner("Resolviendo modelo MILP en paralelo..."):
                res = ejecutar_optimizacion()
            if res.get("status") == "completed":
                st.success(f"Optimización completada: {res['escenarios_resueltos']} escenarios resueltos exitosamente.")
            else:
                st.error(res.get("mensaje", "Ocurrió un error durante la optimización."))

    with otab2:
        st.subheader("Resultados de Selección y CAE")
        rows = ResultadoRepository.list()
        if rows:
            df_opt = pd.DataFrame(rows)
            st.dataframe(df_opt, use_container_width=True)
        else:
            st.info("Aún no hay resultados de optimización guardados. Presione 'Ejecutar Optimización MILP'.")


# =====================================================================
# VISTA 6: MODELO ECONOMÉTRICO (FASE 4)
# =====================================================================
elif menu_option == "📈 Modelo Econométrico (Fase 4)":
    st.markdown("<h2 class='main-title'>Modelo Econométrico y Tests Diagnósticos</h2>", unsafe_allow_html=True)
    st.markdown("Estimación OLS de la curva de Costo Anual Equivalente (CAE), 8 tests diagnósticos de especificación y análisis What-If.")

    conn = get_connection()
    cur = conn.execute("SELECT * FROM eco_modelo ORDER BY id DESC LIMIT 1")
    mod = cur.fetchone()
    if mod:
        st.subheader("Último Modelo Estimado")
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("R²", f"{mod['R2']:.4f}")
        mcol2.metric("R² Ajustado", f"{mod['R2_ajustado']:.4f}")
        mcol3.metric("F-Statistic", f"{mod['F_statistic']:.2f}")
        mcol4.metric("Observaciones", f"{mod['n_observaciones']}")

        st.markdown(f"**Fórmula:** `{mod['formula']}`")

        # Tests
        cur_tests = conn.execute("SELECT test_nombre, estadistico, pvalue, resultado FROM eco_test_diagnostico WHERE modelo_id=?", (mod["id"],))
        t_rows = cur_tests.fetchall()
        if t_rows:
            st.markdown("### Tests Diagnósticos")
            st.dataframe(pd.DataFrame([dict(r) for r in t_rows]), use_container_width=True)
    else:
        st.info("No hay modelo econométrico estimado registrado en la base de datos.")
    conn.close()
