import math
from src.db.connection import get_connection

TASA_DESCUENTO_DEFAULT = 8.0
VIDA_UTIL_DEFAULT = 15
DEMANDA_ANUAL_KWH_DEFAULT = 6000.0
VALOR_UF_DEFAULT = 39000.0

# Poder Calorífico Inferior (PCI) en kWh por unidad comercial física
# Fuente: Tabla 1.1 Balance Nacional de Energía / Documento Borrador Oficial 2026
PCI_KWH_POR_UNIDAD = {
    "electricidad": 1.0,     # kWh/kWh
    "parafina": 9.93,        # kWh/Litro
    "gas_licuado": 12.66,    # kWh/kg
    "gas_natural": 9.91,     # kWh/m³
    "lena": 3.87,            # kWh/kg (25% humedad base seca)
    "pellet": 3.87,          # kWh/kg
}


def obtener_precios_energia(ciudad=None):
    """
    Obtiene los precios de combustibles por unidad física base para una ciudad
    o los promedios nacionales en caso de no especificarse.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT AVG(electricidad_clp_kwh), AVG(kerosene_clp_litro), AVG(glp_clp_kg),
               AVG(gas_natural_clp_m3), AVG(lena_clp_kg), AVG(pellet_clp_kg)
        FROM hvac_matriz_precio_zona
    """)
    avg_row = cur.fetchone()
    national_defaults = {
        "electricidad": float(avg_row[0] or 275.0),
        "parafina": float(avg_row[1] or 1100.0),
        "gas_licuado": float(avg_row[2] or 1750.0),
        "gas_natural": float(avg_row[3] or 1500.0),
        "lena": float(avg_row[4] or 180.0),
        "pellet": float(avg_row[5] or 300.0),
    }

    if not ciudad or str(ciudad).strip().lower() in ["nacional", "todas", "promedio", ""]:
        conn.close()
        return national_defaults

    cur.execute("""
        SELECT electricidad_clp_kwh, kerosene_clp_litro, glp_clp_kg,
               gas_natural_clp_m3, lena_clp_kg, pellet_clp_kg
        FROM hvac_matriz_precio_zona
        WHERE LOWER(ciudad) = LOWER(?)
    """, (str(ciudad).strip(),))
    row = cur.fetchone()
    conn.close()

    if not row:
        return national_defaults

    precios = {
        "electricidad": float(row[0]) if row[0] is not None else national_defaults["electricidad"],
        "parafina": float(row[1]) if row[1] is not None else national_defaults["parafina"],
        "gas_licuado": float(row[2]) if row[2] is not None else national_defaults["gas_licuado"],
        "gas_natural": float(row[3]) if row[3] is not None else national_defaults["gas_natural"],
        "lena": float(row[4]) if row[4] is not None else national_defaults["lena"],
        "pellet": float(row[5]) if row[5] is not None else national_defaults["pellet"],
    }
    return precios


def calcular_matriz(
    tasa_descuento=None,
    vida_util=None,
    ciudad=None,
    demanda_anual_kwh=None,
    potencia_peak_kw=None,
    valor_uf=VALOR_UF_DEFAULT,
    q_especifica_w_m2=60.0,
    equipos_df=None,
):
    if tasa_descuento is None:
        tasa_descuento = TASA_DESCUENTO_DEFAULT
    if vida_util is None:
        vida_util = VIDA_UTIL_DEFAULT
    if demanda_anual_kwh is None or demanda_anual_kwh <= 0:
        demanda_anual_kwh = DEMANDA_ANUAL_KWH_DEFAULT

    precios_comb = obtener_precios_energia(ciudad)

    r = float(tasa_descuento) / 100.0
    N = int(vida_util)
    if r > 0 and N > 0:
        frc = (r * ((1.0 + r) ** N)) / (((1.0 + r) ** N) - 1.0)
    elif N > 0:
        frc = 1.0 / float(N)
    else:
        frc = 0.0

    if equipos_df is not None and not equipos_df.empty:
        records = []
        for _, r_val in equipos_df.iterrows():
            records.append({
                "equipo_id": r_val.get("id") if "id" in r_val else r_val.get("equipo_id"),
                "modelo": r_val["modelo"],
                "marca": r_val.get("marca", "") or "",
                "potencia_nominal_kw": r_val.get("potencia_nominal_kw"),
                "rendimiento_termico_pct": r_val.get("rendimiento_termico_pct"),
                "cop_calor": r_val.get("cop_calor"),
                "costo_adquisicion_clp": r_val.get("costo_adquisicion_clp"),
                "tasa_consumo": r_val.get("tasa_consumo"),
                "unidad_tasa_consumo": r_val.get("unidad_tasa_consumo", ""),
                "costo_instalacion_clp": r_val.get("costo_instalacion_clp", 0),
                "costo_mantencion_anual_clp": r_val.get("costo_mantencion_anual_clp", 0),
                "tecnologia": r_val.get("tecnologia"),
                "combustible": r_val.get("combustible"),
            })
    else:
        conn = get_connection()
        cur = conn.execute("""
            SELECT e.id as equipo_id, e.modelo, e.marca, e.potencia_nominal_kw,
                   e.rendimiento_termico_pct, e.cop_calor, e.costo_adquisicion_clp,
                   e.tasa_consumo, e.unidad_tasa_consumo, e.costo_instalacion_clp,
                   e.costo_mantencion_anual_clp, t.nombre as tecnologia, c.nombre as combustible
            FROM hvac_equipo e
            JOIN hvac_tipo_tecnologia t ON e.tipo_tecnologia_id = t.id
            JOIN hvac_combustible c ON e.combustible_id = c.id
        """)
        records = [dict(r_item) for r_item in cur.fetchall()]
        conn.close()

    rows = []
    for row in records:
        p_nom = float(row["potencia_nominal_kw"] or 1.0)

        # Incorporación de Potencia: Número de equipos requeridos para suplir la carga peak
        if potencia_peak_kw and potencia_peak_kw > 0 and p_nom > 0:
            n_equipos = max(1, math.ceil(float(potencia_peak_kw) / p_nom))
        else:
            n_equipos = 1

        c_adq = float(row["costo_adquisicion_clp"] or 0.0)
        c_inst = float(row["costo_instalacion_clp"] or 0.0)
        c_mant = float(row["costo_mantencion_anual_clp"] or 0.0)

        inversion_total = (c_adq + c_inst) * n_equipos
        costo_fijo_anualizado = (inversion_total * frc) + (c_mant * n_equipos)

        comb = row["combustible"]
        if comb == "electricidad":
            cop = float(row["cop_calor"]) if row["cop_calor"] and row["cop_calor"] > 1.0 else 1.0
            eficiencia_factor = cop
        else:
            rend = float(row["rendimiento_termico_pct"]) if row["rendimiento_termico_pct"] else 80.0
            eficiencia_factor = max(0.1, rend / 100.0)

        p_fuel = precios_comb.get(comb, 200.0)
        pci = PCI_KWH_POR_UNIDAD.get(comb, 1.0)

        costo_variable_por_kwh = p_fuel / (pci * eficiencia_factor)
        costo_variable_por_gcal = costo_variable_por_kwh * 1162.79

        tasa = float(row["tasa_consumo"] or 0.0)
        costo_hora_nominal = tasa * p_fuel * n_equipos

        costo_anual_total = costo_fijo_anualizado + (costo_variable_por_kwh * demanda_anual_kwh)

        lcoh_clp_kwh = costo_anual_total / demanda_anual_kwh
        lcoh_uf_kwh = lcoh_clp_kwh / float(valor_uf) if valor_uf > 0 else 0.0

        superficie_estimada_m2 = (p_nom * 1000.0) / float(q_especifica_w_m2) if q_especifica_w_m2 > 0 else 0.0

        rows.append({
            "equipo_id": row["equipo_id"],
            "tecnologia": row["tecnologia"],
            "combustible": comb,
            "modelo": row["modelo"],
            "marca": row["marca"] or "",
            "potencia_nominal_kw": p_nom,
            "equipos_requeridos": n_equipos,
            "costo_fijo_anualizado_clp": round(costo_fijo_anualizado, 0),
            "costo_variable_por_kwh": round(costo_variable_por_kwh, 2),
            "costo_variable_por_gcal": round(costo_variable_por_gcal, 2),
            "costo_hora_nominal_clp": round(costo_hora_nominal, 1),
            "costo_anual_total_clp": round(costo_anual_total, 0),
            "lcoh_clp_kwh": round(lcoh_clp_kwh, 2),
            "lcoh_uf_kwh": round(lcoh_uf_kwh, 6),
            "superficie_estimada_m2": round(superficie_estimada_m2, 1),
        })

    return rows
