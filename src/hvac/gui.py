import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import streamlit as st
import pandas as pd
from src.db.connection import init_db
from src.hvac.constants import (
    TIPOS_COMBUSTIBLE,
    TIPOS_TECNOLOGIA,
    REGIONES_CHILE_NOMBRES,
    FUENTES_VALIDAS,
    FUENTES_DATOS_PERMITIDAS,
)
from src.hvac.repository import (
    CombustibleRepository,
    PrecioCombustibleRepository,
    TipoTecnologiaRepository,
    EquipoHVACRepository,
)
from src.hvac.matrix import calcular_matriz
from src.hvac.cne_fetcher import fetch_precio_cne, fetch_all_regions

init_db()

HELP_COMBUSTIBLE = {
    "nombre": "Tipo de combustible utilizado por el equipo HVAC.",
    "unidad_medida": "Unidad en que se mide el combustible (litro, kg, m³, kWh, etc.).",
    "pci": "Poder Calorífico Inferior: energía liberada por unidad de combustible.",
    "pcs": "Poder Calorífico Superior: energía total incluyendo calor de condensación.",
    "rendimiento_transformacion": "Eficiencia con que el combustible se transforma en calor útil (%).",
    "unidades_por_gcal": "Cantidad de unidades de combustible necesarias para producir 1 Gcal.",
}

HELP_PRECIO = {
    "combustible": "Combustible al que corresponde el precio.",
    "region": "Región de Chile donde aplica el precio.",
    "precio_por_unidad": "Precio en pesos chilenos (CLP) por unidad de medida del combustible.",
    "fecha_vigencia": "Fecha desde la cual el precio es válido.",
    "fuente": "Origen del dato: ingreso manual o API de la CNE "
              "(requiere CNE_API_EMAIL y CNE_API_PASSWORD configuradas).",
}

HELP_EQUIPO = {
    "tipo_tecnologia": "Tecnología de climatización (split, estufa a leña, pellet, etc.).",
    "combustible": "Combustible que utiliza el equipo.",
    "modelo": "Nombre comercial o código del modelo.",
    "potencia_nominal_kw": "Potencia nominal de calefacción en kilovatios (kW).",
    "rendimiento_termico_pct": "Eficiencia térmica del equipo (%).",
    "costo_adquisicion_clp": "Precio de compra del equipo en CLP.",
    "tasa_consumo": "Consumo por hora de funcionamiento en la unidad indicada.",
    "unidad_tasa_consumo": "Unidad de la tasa de consumo (kWh/h, kg/h, etc.).",
    "costo_instalacion_clp": "Costo de instalación del equipo en CLP.",
    "costo_mantencion_anual_clp": "Costo anual de mantención en CLP.",
    "fuente_datos": "Fuente comercial de los datos del equipo.",
    "url_fuente": "Enlace web de la fuente de datos (opcional).",
}


def region_nombre(codigo):
    return REGIONES_CHILE_NOMBRES.get(codigo, f"Región {codigo}")


def glosario(titulo, help_dict):
    with st.expander(f"¿Qué significa cada campo? ({titulo})"):
        for campo, texto in help_dict.items():
            st.markdown(f"**{campo}**: {texto}")


def confirmar_eliminacion(entidad, item_id, delete_fn, key_prefix):
    if st.session_state.get(f"confirm_del_{key_prefix}") == item_id:
        st.warning(f"¿Está seguro de eliminar este {entidad}? Esta acción no se puede deshacer.")
        col_si, col_no = st.columns(2)
        with col_si:
            if st.button(f"Sí, eliminar {entidad}", key=f"confirm_si_{key_prefix}_{item_id}"):
                resultado = delete_fn(item_id)
                if isinstance(resultado, tuple):
                    ok, errores = resultado
                else:
                    ok, errores = resultado, []
                if ok:
                    st.success(f"{entidad.capitalize()} eliminado.")
                    st.session_state.pop(f"confirm_del_{key_prefix}", None)
                    st.rerun()
                else:
                    st.error("\n".join(errores))
        with col_no:
            if st.button("Cancelar", key=f"confirm_no_{key_prefix}_{item_id}"):
                st.session_state.pop(f"confirm_del_{key_prefix}", None)
                st.rerun()


st.set_page_config(page_title="Catalogo HVAC - Fase 2", layout="wide")
st.title("Catalogo de Alternativas de Climatizacion")

tab1, tab2, tab3, tab4 = st.tabs(["Combustibles", "Precios", "Equipos HVAC", "Matriz de Eleccion"])

# ------------------------- COMBUSTIBLES -------------------------
with tab1:
    st.subheader("Gestionar Combustibles")
    glosario("Combustibles", HELP_COMBUSTIBLE)

    combustibles = CombustibleRepository.list()
    if combustibles:
        for c in combustibles:
            cols = st.columns([5, 1, 1])
            with cols[0]:
                st.write(
                    f"**{c['nombre']}** — {c['unidad_medida']} | "
                    f"PCI {c['pci']} | PCS {c['pcs']} | "
                    f"Rend. {c['rendimiento_transformacion']}% | "
                    f"{c['unidades_por_gcal']} un/Gcal"
                )
            with cols[1]:
                if st.button("Editar", key=f"edit_comb_{c['id']}"):
                    st.session_state.edit_combustible_id = c["id"]
            with cols[2]:
                if st.button("Eliminar", key=f"del_comb_{c['id']}"):
                    st.session_state.confirm_del_combustible = c["id"]
            confirmar_eliminacion(
                "combustible", c["id"], CombustibleRepository.delete, "combustible"
            )
    else:
        st.info("No hay combustibles registrados.")

    edit_id = st.session_state.get("edit_combustible_id")
    if edit_id:
        registro = CombustibleRepository.get_by_id(edit_id)
        if not registro:
            st.error("Combustible no encontrado.")
            st.session_state.pop("edit_combustible_id", None)
        else:
            st.markdown("### Editar combustible")
            with st.form("form_edit_combustible"):
                cols = st.columns(3)
                with cols[0]:
                    nombre = st.selectbox(
                        "Nombre",
                        TIPOS_COMBUSTIBLE,
                        index=TIPOS_COMBUSTIBLE.index(registro["nombre"])
                        if registro["nombre"] in TIPOS_COMBUSTIBLE else 0,
                        help=HELP_COMBUSTIBLE["nombre"],
                    )
                    unidad = st.text_input(
                        "Unidad de medida",
                        value=registro["unidad_medida"],
                        help=HELP_COMBUSTIBLE["unidad_medida"],
                    )
                    pci = st.number_input(
                        "PCI",
                        min_value=0.0,
                        value=float(registro["pci"]),
                        help=HELP_COMBUSTIBLE["pci"],
                    )
                with cols[1]:
                    pcs = st.number_input(
                        "PCS",
                        min_value=0.0,
                        value=float(registro["pcs"]),
                        help=HELP_COMBUSTIBLE["pcs"],
                    )
                    rendimiento = st.number_input(
                        "Rendimiento transformación (%)",
                        0.0,
                        100.0,
                        float(registro["rendimiento_transformacion"]),
                        help=HELP_COMBUSTIBLE["rendimiento_transformacion"],
                    )
                with cols[2]:
                    unidades_gcal = st.number_input(
                        "Unidades por Gcal",
                        min_value=0.0,
                        value=float(registro["unidades_por_gcal"]),
                        format="%.4f",
                        help=HELP_COMBUSTIBLE["unidades_por_gcal"],
                    )
                col_guardar, col_cancelar = st.columns(2)
                with col_guardar:
                    guardar = st.form_submit_button("Guardar cambios")
                with col_cancelar:
                    cancelar = st.form_submit_button("Cancelar")
                if guardar:
                    data = {
                        "nombre": nombre,
                        "unidad_medida": unidad,
                        "pci": pci,
                        "pcs": pcs,
                        "rendimiento_transformacion": rendimiento,
                        "unidades_por_gcal": unidades_gcal,
                    }
                    result, errores = CombustibleRepository.update(edit_id, data)
                    if errores:
                        st.error("\n".join(errores))
                    else:
                        st.success("Combustible actualizado.")
                        st.session_state.pop("edit_combustible_id", None)
                        st.rerun()
                if cancelar:
                    st.session_state.pop("edit_combustible_id", None)
                    st.rerun()
    else:
        st.markdown("### Agregar combustible")
        with st.form("form_nuevo_combustible"):
            cols = st.columns(3)
            with cols[0]:
                nombre = st.selectbox("Nombre", TIPOS_COMBUSTIBLE, help=HELP_COMBUSTIBLE["nombre"])
                unidad = st.text_input("Unidad de medida", "litro", help=HELP_COMBUSTIBLE["unidad_medida"])
                pci = st.number_input("PCI", min_value=0.0, value=8000.0, help=HELP_COMBUSTIBLE["pci"])
            with cols[1]:
                pcs = st.number_input("PCS", min_value=0.0, value=8500.0, help=HELP_COMBUSTIBLE["pcs"])
                rendimiento = st.number_input(
                    "Rendimiento transformación (%)",
                    0.0,
                    100.0,
                    85.0,
                    help=HELP_COMBUSTIBLE["rendimiento_transformacion"],
                )
            with cols[2]:
                unidades_gcal = st.number_input(
                    "Unidades por Gcal",
                    min_value=0.0,
                    value=0.1,
                    format="%.4f",
                    help=HELP_COMBUSTIBLE["unidades_por_gcal"],
                )
            if st.form_submit_button("Agregar Combustible"):
                data = {
                    "nombre": nombre,
                    "unidad_medida": unidad,
                    "pci": pci,
                    "pcs": pcs,
                    "rendimiento_transformacion": rendimiento,
                    "unidades_por_gcal": unidades_gcal,
                }
                result, errores = CombustibleRepository.create(data)
                if errores:
                    st.error("\n".join(errores))
                else:
                    st.success(f"Combustible {result.nombre} creado!")
                    st.rerun()

# ------------------------- PRECIOS -------------------------
with tab2:
    st.subheader("Precios de Combustibles")
    glosario("Precios", HELP_PRECIO)

    combustibles = CombustibleRepository.list()
    comb_opts = {c["nombre"]: c["id"] for c in combustibles}
    region_opts = {nombre: codigo for codigo, nombre in REGIONES_CHILE_NOMBRES.items()}

    importar_cne = st.expander("Importar precios desde CNE (masivo)", expanded=False)
    with importar_cne:
        CNE_COMBUSTIBLES_IMPORT = ["parafina", "gas_licuado"]
        st.markdown(
            "Descarga automáticamente los precios vigentes desde la API de la CNE "
            "para todas las regiones de **parafina** y **gas licuado** en una sola operación."
        )
        if st.button("Importar todos los precios desde CNE", type="primary"):
            with st.spinner("Consultando la API de la CNE..."):
                total_importados = 0
                total_omitidos = 0
                total_errores = 0
                mensajes = []
                for comb_nombre in CNE_COMBUSTIBLES_IMPORT:
                    cid = comb_opts.get(comb_nombre)
                    if not cid:
                        mensajes.append(f"Combustible '{comb_nombre}' no encontrado en el catálogo. Regístrelo primero.")
                        total_errores += 1
                        continue
                    res = fetch_all_regions(comb_nombre)
                    if res["status"] != "ok":
                        mensajes.append(f"CNE {comb_nombre}: {res['mensaje']}")
                        total_errores += 1
                        continue
                    for item in res["data"]:
                        data = {
                            "combustible_id": cid,
                            "region": item["region_cod"],
                            "precio_por_unidad": item["precio_por_unidad"],
                            "fecha_vigencia": item["fecha_vigencia"],
                            "fuente": "CNE_API",
                        }
                        result, errores = PrecioCombustibleRepository.add(data)
                        if errores:
                            total_omitidos += 1
                        else:
                            total_importados += 1
                if total_importados:
                    mensajes.append(f"{total_importados} precios importados exitosamente.")
                if total_omitidos:
                    mensajes.append(f"{total_omitidos} precios ya existían y fueron omitidos.")
                if total_errores:
                    mensajes.append(f"{total_errores} errores encontrados.")
                for msg in mensajes:
                    if "importado" in msg:
                        st.success(msg)
                    elif "omitido" in msg:
                        st.info(msg)
                    else:
                        st.warning(msg)
                st.rerun()

    st.markdown("### Precios registrados")
    precios = PrecioCombustibleRepository.list()
    if precios:
        precio_opts = {}
        for p in precios:
            label = (
                f"ID {p['id']} — {p['combustible_nombre']} | {region_nombre(p['region'])} | "
                f"${p['precio_por_unidad']:,.0f} | {p['fecha_vigencia']} | {p['fuente']}"
            )
            precio_opts[label] = p["id"]

        seleccionados_labels = st.multiselect(
            "Seleccione precios para eliminar masivamente:",
            list(precio_opts.keys()),
            help="Elija uno o más precios y luego presione el botón de abajo para eliminarlos todos a la vez.",
        )
        if seleccionados_labels:
            ids_seleccionados = [precio_opts[l] for l in seleccionados_labels]
            if st.button(f"Eliminar {len(ids_seleccionados)} precios seleccionados"):
                eliminados = 0
                for pid in ids_seleccionados:
                    ok, _ = PrecioCombustibleRepository.delete(pid)
                    if ok:
                        eliminados += 1
                st.success(f"{eliminados} precio(s) eliminados.")
                st.rerun()

        for p in precios:
            cols = st.columns([5, 1, 1])
            with cols[0]:
                st.write(
                    f"**{p['combustible_nombre']}** — {region_nombre(p['region'])} | "
                    f"${p['precio_por_unidad']:,.0f} CLP/unidad | "
                    f"Vigente {p['fecha_vigencia']} | Fuente: {p['fuente']}"
                )
            with cols[1]:
                if st.button("Editar", key=f"edit_precio_{p['id']}"):
                    st.session_state.edit_precio_id = p["id"]
            with cols[2]:
                if st.button("Eliminar", key=f"del_precio_{p['id']}"):
                    st.session_state.confirm_del_precio = p["id"]
            confirmar_eliminacion(
                "precio", p["id"], PrecioCombustibleRepository.delete, "precio"
            )
    else:
        st.info("No hay precios registrados.")

    edit_precio_id = st.session_state.get("edit_precio_id")
    if edit_precio_id:
        registro = PrecioCombustibleRepository.get_by_id(edit_precio_id)
        if not registro:
            st.error("Precio no encontrado.")
            st.session_state.pop("edit_precio_id", None)
        else:
            st.markdown("### Editar precio")
            with st.form("form_edit_precio"):
                cols = st.columns(3)
                with cols[0]:
                    comb_nombre = st.selectbox(
                        "Combustible",
                        list(comb_opts.keys()),
                        index=list(comb_opts.keys()).index(registro["combustible_nombre"])
                        if registro["combustible_nombre"] in comb_opts else 0,
                        help=HELP_PRECIO["combustible"],
                    )
                    region_nom = st.selectbox(
                        "Región",
                        list(region_opts.keys()),
                        index=list(region_opts.values()).index(registro["region"])
                        if registro["region"] in region_opts.values() else 0,
                        help=HELP_PRECIO["region"],
                    )
                with cols[1]:
                    precio = st.number_input(
                        "Precio por unidad (CLP)",
                        min_value=0.0,
                        value=float(registro["precio_por_unidad"]),
                        help=HELP_PRECIO["precio_por_unidad"],
                    )
                    fecha = st.date_input(
                        "Fecha de vigencia",
                        value=datetime.strptime(registro["fecha_vigencia"], "%Y-%m-%d").date(),
                        help=HELP_PRECIO["fecha_vigencia"],
                    )
                with cols[2]:
                    fuente = st.selectbox(
                        "Fuente",
                        FUENTES_VALIDAS,
                        index=FUENTES_VALIDAS.index(registro["fuente"])
                        if registro["fuente"] in FUENTES_VALIDAS else 0,
                        help=HELP_PRECIO["fuente"],
                    )
                col_guardar, col_cancelar = st.columns(2)
                with col_guardar:
                    guardar = st.form_submit_button("Guardar cambios")
                with col_cancelar:
                    cancelar = st.form_submit_button("Cancelar")
                if guardar:
                    if fuente == "CNE_API":
                        res = fetch_precio_cne(comb_nombre, region_opts[region_nom])
                        if res["status"] != "ok":
                            st.error(res["mensaje"])
                            st.stop()
                        precio = res["precio_por_unidad"]
                        fecha = datetime.strptime(res["fecha_vigencia"], "%Y-%m-%d").date()
                    data = {
                        "combustible_id": comb_opts[comb_nombre],
                        "region": region_opts[region_nom],
                        "precio_por_unidad": precio,
                        "fecha_vigencia": str(fecha),
                        "fuente": fuente,
                    }
                    result, errores = PrecioCombustibleRepository.update(edit_precio_id, data)
                    if errores:
                        st.error("\n".join(errores))
                    else:
                        st.success("Precio actualizado.")
                        st.session_state.pop("edit_precio_id", None)
                        st.rerun()
                if cancelar:
                    st.session_state.pop("edit_precio_id", None)
                    st.rerun()
    else:
        st.markdown("### Agregar precio")
        with st.form("form_nuevo_precio"):
            cols = st.columns(3)
            with cols[0]:
                comb_nombre = st.selectbox(
                    "Combustible", list(comb_opts.keys()), help=HELP_PRECIO["combustible"]
                )
                region_nom = st.selectbox(
                    "Región", list(region_opts.keys()), help=HELP_PRECIO["region"]
                )
            with cols[1]:
                precio = st.number_input(
                    "Precio por unidad (CLP)",
                    min_value=0.0,
                    value=1000.0,
                    help=HELP_PRECIO["precio_por_unidad"],
                )
                fecha = st.date_input("Fecha de vigencia", help=HELP_PRECIO["fecha_vigencia"])
            with cols[2]:
                fuente = st.selectbox("Fuente", FUENTES_VALIDAS, help=HELP_PRECIO["fuente"])
            if st.form_submit_button("Agregar Precio"):
                if fuente == "CNE_API":
                    res = fetch_precio_cne(comb_nombre, region_opts[region_nom])
                    if res["status"] != "ok":
                        st.error(res["mensaje"])
                        st.stop()
                    precio = res["precio_por_unidad"]
                    fecha = datetime.strptime(res["fecha_vigencia"], "%Y-%m-%d").date()
                    st.info(f"Precio CNE obtenido: ${precio:,.0f} CLP/{res['unidad']} ({res['fecha_vigencia']})")
                data = {
                    "combustible_id": comb_opts[comb_nombre],
                    "region": region_opts[region_nom],
                    "precio_por_unidad": precio,
                    "fecha_vigencia": str(fecha),
                    "fuente": fuente,
                }
                result, errores = PrecioCombustibleRepository.add(data)
                if errores:
                    st.error("\n".join(errores))
                else:
                    st.success("Precio registrado!")
                    st.rerun()

# ------------------------- EQUIPOS HVAC -------------------------
with tab3:
    st.subheader("Gestionar Equipos HVAC")
    glosario("Equipos", HELP_EQUIPO)

    equipos = EquipoHVACRepository.list()
    if equipos:
        for e in equipos:
            cols = st.columns([5, 1, 1])
            with cols[0]:
                st.write(
                    f"**{e['tecnologia_nombre']}** — {e['combustible_nombre']} | "
                    f"Modelo: {e['modelo']} | {e['potencia_nominal_kw']} kW | "
                    f"Rend. {e['rendimiento_termico_pct']}% | "
                    f"${e['costo_adquisicion_clp']:,.0f} CLP"
                )
            with cols[1]:
                if st.button("Editar", key=f"edit_eq_{e['id']}"):
                    st.session_state.edit_equipo_id = e["id"]
            with cols[2]:
                if st.button("Eliminar", key=f"del_eq_{e['id']}"):
                    st.session_state.confirm_del_equipo = e["id"]
            confirmar_eliminacion("equipo", e["id"], EquipoHVACRepository.delete, "equipo")
    else:
        st.info("No hay equipos registrados.")

    conteo = EquipoHVACRepository.count_by_tecnologia()
    if conteo:
        st.write("**Conteo por tecnología:**")
        for c in conteo:
            st.write(f"- {c['nombre']}: {c['cantidad']} equipos")

    tipos = TipoTecnologiaRepository.list()
    tipo_opts = {t["nombre"]: t["id"] for t in tipos}
    comb_opts = {c["nombre"]: c["id"] for c in CombustibleRepository.list()}

    edit_equipo_id = st.session_state.get("edit_equipo_id")
    if edit_equipo_id:
        registro = EquipoHVACRepository.get_by_id(edit_equipo_id)
        if not registro:
            st.error("Equipo no encontrado.")
            st.session_state.pop("edit_equipo_id", None)
        else:
            st.markdown("### Editar equipo")
            with st.form("form_edit_equipo"):
                cols = st.columns(3)
                with cols[0]:
                    tipo_tec = st.selectbox(
                        "Tipo tecnología",
                        list(tipo_opts.keys()),
                        index=list(tipo_opts.keys()).index(registro["tecnologia_nombre"])
                        if registro["tecnologia_nombre"] in tipo_opts else 0,
                        help=HELP_EQUIPO["tipo_tecnologia"],
                    )
                    comb = st.selectbox(
                        "Combustible",
                        list(comb_opts.keys()),
                        index=list(comb_opts.keys()).index(registro["combustible_nombre"])
                        if registro["combustible_nombre"] in comb_opts else 0,
                        help=HELP_EQUIPO["combustible"],
                    )
                    modelo = st.text_input(
                        "Modelo", value=registro["modelo"], help=HELP_EQUIPO["modelo"]
                    )
                with cols[1]:
                    potencia = st.number_input(
                        "Potencia nominal (kW)",
                        min_value=0.0,
                        value=float(registro["potencia_nominal_kw"]),
                        help=HELP_EQUIPO["potencia_nominal_kw"],
                    )
                    rendimiento = st.number_input(
                        "Rendimiento térmico (%)",
                        0.0,
                        100.0,
                        float(registro["rendimiento_termico_pct"]),
                        help=HELP_EQUIPO["rendimiento_termico_pct"],
                    )
                    costo_adq = st.number_input(
                        "Costo adquisición (CLP)",
                        min_value=0.0,
                        value=float(registro["costo_adquisicion_clp"]),
                        help=HELP_EQUIPO["costo_adquisicion_clp"],
                    )
                with cols[2]:
                    tasa_consumo = st.number_input(
                        "Tasa consumo",
                        min_value=0.0,
                        value=float(registro["tasa_consumo"]),
                        help=HELP_EQUIPO["tasa_consumo"],
                    )
                    unidad_tasa = st.text_input(
                        "Unidad tasa",
                        value=registro["unidad_tasa_consumo"],
                        help=HELP_EQUIPO["unidad_tasa_consumo"],
                    )
                    costo_inst = st.number_input(
                        "Costo instalación (CLP)",
                        min_value=0.0,
                        value=float(registro.get("costo_instalacion_clp") or 0),
                        help=HELP_EQUIPO["costo_instalacion_clp"],
                    )
                    costo_mant = st.number_input(
                        "Costo mantención anual (CLP)",
                        min_value=0.0,
                        value=float(registro.get("costo_mantencion_anual_clp") or 0),
                        help=HELP_EQUIPO["costo_mantencion_anual_clp"],
                    )
                    fuente_datos = st.selectbox(
                        "Fuente datos",
                        FUENTES_DATOS_PERMITIDAS,
                        index=FUENTES_DATOS_PERMITIDAS.index(registro["fuente_datos"])
                        if registro["fuente_datos"] in FUENTES_DATOS_PERMITIDAS else 0,
                        help=HELP_EQUIPO["fuente_datos"],
                    )
                    url_fuente = st.text_input(
                        "URL fuente",
                        value=registro.get("url_fuente") or "",
                        help=HELP_EQUIPO["url_fuente"],
                    )
                col_guardar, col_cancelar = st.columns(2)
                with col_guardar:
                    guardar = st.form_submit_button("Guardar cambios")
                with col_cancelar:
                    cancelar = st.form_submit_button("Cancelar")
                if guardar:
                    data = {
                        "tipo_tecnologia_id": tipo_opts[tipo_tec],
                        "combustible_id": comb_opts[comb],
                        "modelo": modelo,
                        "potencia_nominal_kw": potencia,
                        "rendimiento_termico_pct": rendimiento,
                        "costo_adquisicion_clp": costo_adq,
                        "tasa_consumo": tasa_consumo,
                        "unidad_tasa_consumo": unidad_tasa,
                        "costo_instalacion_clp": costo_inst,
                        "costo_mantencion_anual_clp": costo_mant,
                        "fuente_datos": fuente_datos,
                        "url_fuente": url_fuente or None,
                    }
                    result, errores = EquipoHVACRepository.update(edit_equipo_id, data)
                    if errores:
                        st.error("\n".join(errores))
                    else:
                        st.success("Equipo actualizado.")
                        st.session_state.pop("edit_equipo_id", None)
                        st.rerun()
                if cancelar:
                    st.session_state.pop("edit_equipo_id", None)
                    st.rerun()
    else:
        st.markdown("### Agregar equipo")
        with st.form("form_nuevo_equipo"):
            cols = st.columns(3)
            with cols[0]:
                tipo_tec = st.selectbox(
                    "Tipo tecnología", list(tipo_opts.keys()), help=HELP_EQUIPO["tipo_tecnologia"]
                )
                comb = st.selectbox(
                    "Combustible", list(comb_opts.keys()), help=HELP_EQUIPO["combustible"]
                )
                modelo = st.text_input("Modelo", help=HELP_EQUIPO["modelo"])
            with cols[1]:
                potencia = st.number_input(
                    "Potencia nominal (kW)",
                    min_value=0.0,
                    value=3.5,
                    help=HELP_EQUIPO["potencia_nominal_kw"],
                )
                rendimiento = st.number_input(
                    "Rendimiento térmico (%)",
                    0.0,
                    100.0,
                    90.0,
                    help=HELP_EQUIPO["rendimiento_termico_pct"],
                )
                costo_adq = st.number_input(
                    "Costo adquisición (CLP)",
                    min_value=0.0,
                    value=300000.0,
                    help=HELP_EQUIPO["costo_adquisicion_clp"],
                )
            with cols[2]:
                tasa_consumo = st.number_input(
                    "Tasa consumo", min_value=0.0, value=1.0, help=HELP_EQUIPO["tasa_consumo"]
                )
                unidad_tasa = st.text_input(
                    "Unidad tasa", "kWh/h", help=HELP_EQUIPO["unidad_tasa_consumo"]
                )
                costo_inst = st.number_input(
                    "Costo instalación (CLP)",
                    min_value=0.0,
                    value=0.0,
                    help=HELP_EQUIPO["costo_instalacion_clp"],
                )
                costo_mant = st.number_input(
                    "Costo mantención anual (CLP)",
                    min_value=0.0,
                    value=0.0,
                    help=HELP_EQUIPO["costo_mantencion_anual_clp"],
                )
                fuente_datos = st.selectbox(
                    "Fuente datos", FUENTES_DATOS_PERMITIDAS, help=HELP_EQUIPO["fuente_datos"]
                )
                url_fuente = st.text_input("URL fuente", help=HELP_EQUIPO["url_fuente"])
            if st.form_submit_button("Agregar Equipo"):
                data = {
                    "tipo_tecnologia_id": tipo_opts[tipo_tec],
                    "combustible_id": comb_opts[comb],
                    "modelo": modelo,
                    "potencia_nominal_kw": potencia,
                    "rendimiento_termico_pct": rendimiento,
                    "costo_adquisicion_clp": costo_adq,
                    "tasa_consumo": tasa_consumo,
                    "unidad_tasa_consumo": unidad_tasa,
                    "costo_instalacion_clp": costo_inst,
                    "costo_mantencion_anual_clp": costo_mant,
                    "fuente_datos": fuente_datos,
                    "url_fuente": url_fuente or None,
                }
                result, errores = EquipoHVACRepository.create(data)
                if errores:
                    st.error("\n".join(errores))
                else:
                    st.success(f"Equipo {result.modelo} creado!")
                    st.rerun()

# ------------------------- MATRIZ -------------------------
with tab4:
    st.subheader("Matriz de Eleccion Discreta")
    matrix_rows = calcular_matriz()
    if matrix_rows:
        df = pd.DataFrame(matrix_rows)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar Matriz CSV", csv, "matriz_eleccion.csv", "text/csv")
    else:
        st.info("No hay datos suficientes para calcular la matriz. Registre equipos y combustibles primero.")
