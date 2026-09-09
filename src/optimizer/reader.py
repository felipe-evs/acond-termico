from src.db.connection import get_connection


def leer_escenarios():
    conn = get_connection()
    cur = conn.execute("""
        SELECT s.id as escenario_id, s.tipologia, s.zona_termica,
               r.u_prom, r.demanda_anual_kwh, r.peak_demanda_kw, r.gdc
        FROM sim_simulacion s
        JOIN sim_resultado r ON s.id = r.simulacion_id
        ORDER BY s.zona_termica, s.tipologia
    """)
    escenarios = [dict(row) for row in cur.fetchall()]
    conn.close()
    return escenarios


def leer_equipos():
    conn = get_connection()
    cur = conn.execute("""
        SELECT e.id as equipo_id, e.modelo, e.tipo_tecnologia_id, e.combustible_id,
               e.potencia_nominal_kw, e.rendimiento_termico_pct,
               e.costo_adquisicion_clp, e.costo_instalacion_clp,
               e.costo_mantencion_anual_clp, e.tasa_consumo, e.unidad_tasa_consumo,
               t.nombre as tecnologia_nombre, c.nombre as combustible_nombre,
               c.unidades_por_gcal
        FROM hvac_equipo e
        JOIN hvac_tipo_tecnologia t ON e.tipo_tecnologia_id = t.id
        JOIN hvac_combustible c ON e.combustible_id = c.id
        ORDER BY e.id
    """)
    equipos = [dict(row) for row in cur.fetchall()]
    conn.close()
    return equipos


def leer_parametros():
    conn = get_connection()
    cur = conn.execute("SELECT * FROM opt_parametro ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"tasa_descuento_pct": 8.0, "vida_util_anos": 15, "perdida_sistemica_pct": 5.0}
