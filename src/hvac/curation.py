"""
Módulo de Curación de Datos, Detección de Anomalías y Estratificación Arquetípica HVAC
======================================================================================
Fundamentación Académica:
- Detección de Outliers: Rango Intercuartílico (IQR / Tukey, 1977) y Consistencia de Primera Ley.
- Estratificación y Clustering: Método K-Medoids / Partitioning Around Medoids (Kaufman & Rousseeuw, 1990).
- Normalización Energética: ASHRAE Guideline 14, IEA EBC Annex 67, balances SEC / CNE Chile 2026.
"""

import json
import os
import numpy as np
import pandas as pd
from src.db.connection import get_connection

# Poder Calorífico Inferior (PCI) oficial en kWh/unidad (Tabla 1.1 Balance Nacional de Energía)
PCI_KWH_MAP = {
    "electricidad": 1.0,     # kWh/kWh
    "parafina": 9.93,        # kWh/L
    "gas_licuado": 12.66,    # kWh/kg
    "gas_natural": 9.91,     # kWh/m³
    "lena": 3.87,            # kWh/kg
    "pellet": 3.87,          # kWh/kg
}

# Límites físicos normativos según SEC y literatura técnica HVAC
LIMITES_FISICOS_SEC = {
    "split_inverter": {"cop_min": 2.2, "cop_max": 5.2},
    "estufa_electrica": {"rend_min": 99.0, "rend_max": 100.0},
    "estufa_pellet": {"rend_min": 70.0, "rend_max": 96.0},
    "estufa_lena": {"rend_min": 50.0, "rend_max": 80.0},
    "estufa_parafina": {"rend_min": 70.0, "rend_max": 98.0},
    "estufa_gas": {"rend_min": 70.0, "rend_max": 98.0},
}


def cargar_catalogo_completo():
    """Carga los 653 equipos desde SQLite con sus relaciones de tecnología y combustible."""
    conn = get_connection()
    query = """
        SELECT e.id, e.modelo, e.marca, t.nombre as tecnologia, c.nombre as combustible,
               e.potencia_nominal_kw, e.rendimiento_termico_pct, e.cop_calor,
               e.costo_adquisicion_clp, e.tasa_consumo, e.unidad_tasa_consumo,
               e.costo_instalacion_clp, e.costo_mantencion_anual_clp, e.tienda,
               e.url_tienda, e.otros
        FROM hvac_equipo e
        JOIN hvac_tipo_tecnologia t ON e.tipo_tecnologia_id = t.id
        JOIN hvac_combustible c ON e.combustible_id = c.id
        ORDER BY e.tipo_tecnologia_id, e.potencia_nominal_kw, e.costo_adquisicion_clp
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def identificar_equipos_terraza(df):
    """
    Identifica equipos de uso exclusivo exterior/terraza (ej. estufas hongo o pirámide a gas).
    No excluye equipos interiores de tiro forzado con ducto pasamuros exterior.
    """
    patio_keywords = ["patio", "terraza", "hongo", "piramide", "pirámide"]
    scraped_patio_models = set()
    
    # Cruce con JSON crudo si existe
    json_path = "data/solotodo_scraped_products.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                scraped = json.load(f)
            for p in scraped:
                t = p.get("tipo", "").lower()
                if "patio" in t or "terraza" in t:
                    scraped_patio_models.add(p.get("modelo", "").strip().lower())
                    scraped_patio_models.add(p.get("nombre_completo", "").strip().lower())
        except Exception:
            pass

    def es_patio(row):
        m_lower = str(row["modelo"]).strip().lower()
        if m_lower in scraped_patio_models:
            return True
        otros_lower = str(row.get("otros", "")).lower()
        # Verificar palabras clave explícitas en modelo u otros (excluyendo ductos pasamuros)
        if any(k in m_lower for k in patio_keywords):
            return True
        if ("hongo" in otros_lower or "piramide" in otros_lower or "pirámide" in otros_lower) and row["potencia_nominal_kw"] >= 10.0:
            return True
        return False

    return df.apply(es_patio, axis=1)


def auditar_anomalias_catalogo(df, iqr_multiplier=1.5, tol_termodinamica=0.25):
    """
    Aplica las reglas de auditoría y detección de anomalías a todo el DataFrame.
    Retorna el DataFrame con banderas y motivos detallados.
    """
    df_audit = df.copy()

    # R1: Terraza / Patio
    df_audit["es_terraza"] = identificar_equipos_terraza(df_audit)

    # R2: Inconsistencia Termodinámica (Tasa Consumo vs Potencia / (PCI * Rend))
    def test_thermo(r):
        comb = r["combustible"]
        pci = PCI_KWH_MAP.get(comb, 1.0)
        p_nom = float(r["potencia_nominal_kw"] or 0)
        tasa = float(r["tasa_consumo"] or 0)
        if p_nom <= 0 or tasa <= 0:
            return False, 0.0
        if comb == "electricidad":
            cop = float(r["cop_calor"]) if pd.notna(r["cop_calor"]) and float(r["cop_calor"]) > 1.0 else 1.0
            expected = p_nom / cop
        else:
            rend = (float(r["rendimiento_termico_pct"]) / 100.0) if pd.notna(r["rendimiento_termico_pct"]) else 0.8
            expected = p_nom / (pci * max(0.1, rend))
        diff_rel = abs(tasa - expected) / expected if expected > 0 else 0.0
        return diff_rel > tol_termodinamica, diff_rel

    thermo_res = df_audit.apply(test_thermo, axis=1)
    df_audit["anomalia_termodinamica"] = [x[0] for x in thermo_res]
    df_audit["discrepancia_termo_pct"] = [round(x[1] * 100, 1) for x in thermo_res]

    # R3: Límites Físicos SEC
    def test_sec(r):
        tec = r["tecnologia"]
        lim = LIMITES_FISICOS_SEC.get(tec)
        if not lim:
            return False
        if tec == "split_inverter":
            cop = float(r["cop_calor"]) if pd.notna(r["cop_calor"]) else 3.2
            return cop < lim["cop_min"] or cop > lim["cop_max"]
        else:
            rend = float(r["rendimiento_termico_pct"]) if pd.notna(r["rendimiento_termico_pct"]) else 80.0
            return rend < lim["rend_min"] or rend > lim["rend_max"]

    df_audit["anomalia_sec"] = df_audit.apply(test_sec, axis=1)

    # R4: Outlier Estadístico de Precio por Tecnología (Tukey IQR)
    def calc_iqr_outlier(group):
        q1 = group["costo_adquisicion_clp"].quantile(0.25)
        q3 = group["costo_adquisicion_clp"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr
        return (group["costo_adquisicion_clp"] < lower) | (group["costo_adquisicion_clp"] > upper)

    df_audit["outlier_precio_iqr"] = df_audit.groupby("tecnologia", group_keys=False).apply(calc_iqr_outlier)

    # R5: Ratio Precio / Potencia (CLP/kW)
    df_audit["ratio_clp_kw"] = df_audit["costo_adquisicion_clp"] / df_audit["potencia_nominal_kw"].replace(0, 0.1)

    def calc_ratio_outlier(group):
        q1 = group["ratio_clp_kw"].quantile(0.25)
        q3 = group["ratio_clp_kw"].quantile(0.75)
        iqr = q3 - q1
        upper = q3 + (iqr_multiplier * 1.5) * iqr
        lower = max(0, q1 - (iqr_multiplier * 1.5) * iqr)
        return (group["ratio_clp_kw"] < lower) | (group["ratio_clp_kw"] > upper)

    df_audit["outlier_ratio_kw"] = df_audit.groupby("tecnologia", group_keys=False).apply(calc_ratio_outlier)

    # Consolidar estado y motivos
    def build_audit_tag(r):
        reasons = []
        if r["es_terraza"]:
            reasons.append("Estufa Patio/Terraza")
        if r["anomalia_termodinamica"]:
            reasons.append(f"Inconsistencia Tasa Consumo (+{r['discrepancia_termo_pct']}%)")
        if r["anomalia_sec"]:
            reasons.append("Límite Físico SEC fuera de rango")
        if r["outlier_precio_iqr"]:
            reasons.append("Precio Atípico (Tukey IQR)")
        if r["outlier_ratio_kw"]:
            reasons.append("Ratio CLP/kW Dispar")
        if not reasons:
            return "Normal", "Verificado", "OK"
        severidad = "ALTA" if (r["anomalia_termodinamica"] or r["anomalia_sec"]) else "MEDIA"
        return "Alerta", " | ".join(reasons), severidad

    tag_data = df_audit.apply(build_audit_tag, axis=1)
    df_audit["estado_auditoria"] = [x[0] for x in tag_data]
    df_audit["motivo_alerta"] = [x[1] for x in tag_data]
    df_audit["severidad_alerta"] = [x[2] for x in tag_data]

    return df_audit


def generar_muestra_representativa(
    df,
    metodo="medoid",
    granularidad="estandar",
    excluir_terraza=False,
    excluir_outliers_precio=False,
    excluir_anomalias_termo=True,
    iqr_multiplier=1.5,
    target_custom_bins=None,
):
    """
    Genera la muestra representativa arquetípica (~70 equipos en granularidad estándar).
    
    Parámetros:
    - metodo: 'medoid' (Equipo Real Más Representativo) o 'centroide' (Equipo Tipo Sintético)
    - granularidad: 'compacto' (~35), 'estandar' (~70) o 'detallado' (~105)
    - excluir_terraza: si True, remueve equipos de patio/terraza
    - excluir_outliers_precio: si True, remueve equipos fuera de Tukey IQR
    - excluir_anomalias_termo: si True, remueve inconsistencias de primera ley
    - iqr_multiplier: factor de Tukey IQR (default 1.5)
    """
    # 1. Auditar y filtrar según reglas activas a voluntad
    df_audit = auditar_anomalias_catalogo(df, iqr_multiplier=iqr_multiplier)
    mask = pd.Series(True, index=df_audit.index)

    if excluir_terraza:
        mask = mask & (~df_audit["es_terraza"])
    if excluir_outliers_precio:
        mask = mask & (~df_audit["outlier_precio_iqr"])
    if excluir_anomalias_termo:
        mask = mask & (~df_audit["anomalia_termodinamica"])

    df_filtered = df_audit[mask].copy()

    # 2. Configurar estratos según granularidad deseada
    if granularidad == "compacto":
        # ~35 arquetipos
        power_cuts = {
            "split_inverter": [0, 3.5, 6.0, 100.0],       # 3 tramos
            "estufa_electrica": [0, 1.5, 2.2, 100.0],     # 3 tramos
            "estufa_lena": [0, 10.0, 18.0, 100.0],        # 3 tramos
            "estufa_pellet": [0, 8.5, 100.0],             # 2 tramos
            "estufa_parafina": [0, 3.5, 100.0],           # 2 tramos
            "estufa_gas": [0, 4.5, 100.0],               # 2 tramos
        }
        max_tiers = 2
    elif granularidad == "detallado":
        # ~105 arquetipos
        power_cuts = {
            "split_inverter": [0, 2.8, 3.8, 5.5, 7.5, 10.0, 100.0],
            "estufa_electrica": [0, 0.8, 1.2, 1.6, 2.0, 2.5, 100.0],
            "estufa_lena": [0, 7.0, 10.0, 14.0, 18.0, 100.0],
            "estufa_pellet": [0, 6.5, 8.5, 10.5, 13.0, 100.0],
            "estufa_parafina": [0, 2.5, 3.2, 4.2, 5.5, 100.0],
            "estufa_gas": [0, 2.5, 3.5, 4.5, 7.0, 100.0],
        }
        max_tiers = 3
    else:
        # 'estandar' -> Conduce naturalmente al rango óptimo de ~70 arquetipos (67-70)
        power_cuts = {
            "split_inverter": [0, 3.0, 4.5, 6.0, 8.5, 100.0],  # 9k, 12k, 18k, 24k, comercial
            "estufa_electrica": [0, 1.0, 1.5, 2.0, 2.5, 100.0], # 5 tramos
            "estufa_lena": [0, 8.0, 12.0, 16.0, 100.0],        # 4 tramos
            "estufa_pellet": [0, 7.5, 9.5, 12.0, 100.0],       # 4 tramos
            "estufa_parafina": [0, 2.8, 3.8, 5.0, 100.0],      # 4 tramos
            "estufa_gas": [0, 3.0, 4.5, 8.0, 100.0],          # 4 tramos
        }
        max_tiers = 3

    archetypes = []

    for tec, grp in df_filtered.groupby("tecnologia"):
        cuts = power_cuts.get(tec, [0, 3.0, 6.0, 100.0])
        p_labels = [f"P{i+1}" for i in range(len(cuts) - 1)]
        grp = grp.copy()
        grp["p_bin"] = pd.cut(grp["potencia_nominal_kw"], bins=cuts, labels=p_labels, include_lowest=True)

        for p_label, p_grp in grp.groupby("p_bin", observed=False):
            if p_grp.empty:
                continue

            n_items = len(p_grp)
            if n_items >= 6 and max_tiers >= 3:
                n_tiers = 3
            elif n_items >= 2 and max_tiers >= 2:
                n_tiers = 2
            else:
                n_tiers = 1

            if n_tiers > 1:
                p_grp = p_grp.copy()
                p_grp["tier"] = pd.qcut(
                    p_grp["costo_adquisicion_clp"],
                    q=n_tiers,
                    labels=[f"T{j+1}" for j in range(n_tiers)],
                    duplicates="drop"
                )
            else:
                p_grp = p_grp.copy()
                p_grp["tier"] = "T1"

            for t_label, t_grp in p_grp.groupby("tier", observed=False):
                if t_grp.empty:
                    continue

                cluster_id = f"{tec}_{p_label}_{t_label}"
                n_rep = len(t_grp)
                precio_min = float(t_grp["costo_adquisicion_clp"].min())
                precio_max = float(t_grp["costo_adquisicion_clp"].max())
                precio_prom = float(t_grp["costo_adquisicion_clp"].mean())
                p_min = float(t_grp["potencia_nominal_kw"].min())
                p_max = float(t_grp["potencia_nominal_kw"].max())

                tier_names = {"T1": "Económico", "T2": "Estándar", "T3": "Alta Gama"}
                tier_desc = tier_names.get(str(t_label), "Estándar")

                if metodo == "centroide":
                    # Generar Equipo Tipo Sintético
                    p_med = round(float(t_grp["potencia_nominal_kw"].median()), 2)
                    rend_med = round(float(t_grp["rendimiento_termico_pct"].median()), 1)
                    cop_med = round(float(t_grp["cop_calor"].median()), 2) if tec == "split_inverter" else None
                    costo_med = round(float(t_grp["costo_adquisicion_clp"].median()), 0)
                    tasa_med = round(float(t_grp["tasa_consumo"].median()), 3)
                    c_inst_med = round(float(t_grp["costo_instalacion_clp"].median()), 0)
                    c_mant_med = round(float(t_grp["costo_mantencion_anual_clp"].median()), 0)
                    unit_tasa = t_grp["unidad_tasa_consumo"].iloc[0]
                    comb_name = t_grp["combustible"].iloc[0]

                    tec_tit = tec.replace("_", " ").title()
                    archetypes.append({
                        "id": f"TIPO_{cluster_id}",
                        "modelo": f"[Equipo Tipo] {tec_tit} ({p_med:.1f} kW, {tier_desc})",
                        "marca": "Arquetipo Sintético",
                        "tecnologia": tec,
                        "combustible": comb_name,
                        "potencia_nominal_kw": p_med,
                        "rendimiento_termico_pct": rend_med,
                        "cop_calor": cop_med,
                        "costo_adquisicion_clp": costo_med,
                        "tasa_consumo": tasa_med,
                        "unidad_tasa_consumo": unit_tasa,
                        "costo_instalacion_clp": c_inst_med,
                        "costo_mantencion_anual_clp": c_mant_med,
                        "tienda": "Muestra Promedio Representativa",
                        "url_tienda": "",
                        "otros": f"Arquetipo sintético representativo de {n_rep} modelos. Rango de precios real: ${precio_min:,.0f} - ${precio_max:,.0f}.",
                        "cluster_id": cluster_id,
                        "n_representados": n_rep,
                        "precio_min_cluster": precio_min,
                        "precio_max_cluster": precio_max,
                        "precio_prom_cluster": precio_prom,
                        "potencia_min_cluster": p_min,
                        "potencia_max_cluster": p_max,
                        "es_sintetico": True,
                    })

                else:
                    # Método Medoid: Seleccionar el equipo real más cercano al centroide multidimensional
                    feat = t_grp[["potencia_nominal_kw", "costo_adquisicion_clp"]].copy()
                    if tec == "split_inverter":
                        feat["ef"] = t_grp["cop_calor"].fillna(3.2)
                    else:
                        feat["ef"] = t_grp["rendimiento_termico_pct"].fillna(80.0)

                    means = feat.mean()
                    stds = feat.std().replace(0, 1.0).fillna(1.0)
                    norm_f = (feat - means) / stds
                    centroid = norm_f.median()

                    dists = ((norm_f - centroid) ** 2).sum(axis=1)
                    medoid_idx = dists.idxmin()
                    medoid = t_grp.loc[medoid_idx]

                    archetypes.append({
                        "id": medoid["id"],
                        "modelo": medoid["modelo"],
                        "marca": medoid["marca"],
                        "tecnologia": medoid["tecnologia"],
                        "combustible": medoid["combustible"],
                        "potencia_nominal_kw": float(medoid["potencia_nominal_kw"]),
                        "rendimiento_termico_pct": float(medoid["rendimiento_termico_pct"]) if pd.notna(medoid["rendimiento_termico_pct"]) else 80.0,
                        "cop_calor": float(medoid["cop_calor"]) if pd.notna(medoid["cop_calor"]) else None,
                        "costo_adquisicion_clp": float(medoid["costo_adquisicion_clp"]),
                        "tasa_consumo": float(medoid["tasa_consumo"]),
                        "unidad_tasa_consumo": medoid["unidad_tasa_consumo"],
                        "costo_instalacion_clp": float(medoid["costo_instalacion_clp"] or 0),
                        "costo_mantencion_anual_clp": float(medoid["costo_mantencion_anual_clp"] or 0),
                        "tienda": medoid["tienda"],
                        "url_tienda": medoid["url_tienda"],
                        "otros": f"Medoid Real representativo de {n_rep} equipos. Rango cluster: ${precio_min:,.0f} - ${precio_max:,.0f}.",
                        "cluster_id": cluster_id,
                        "n_representados": n_rep,
                        "precio_min_cluster": precio_min,
                        "precio_max_cluster": precio_max,
                        "precio_prom_cluster": precio_prom,
                        "potencia_min_cluster": p_min,
                        "potencia_max_cluster": p_max,
                        "es_sintetico": False,
                    })

    df_arch = pd.DataFrame(archetypes)
    return df_arch, df_audit
