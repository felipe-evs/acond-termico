def construir_milp(escenario, equipos, parametros):
    try:
        import pulp
    except ImportError:
        return None, "pulp no instalado. Ejecute: pip install pulp"

    prob = pulp.LpProblem(f"Optimizacion_Zona{escenario['zona_termica']}_{escenario['tipologia']}",
                          pulp.LpMinimize)

    x = {}
    for eq in equipos:
        x[eq["equipo_id"]] = pulp.LpVariable(f"x_{eq['equipo_id']}", cat="Binary")

    tasa = parametros.get("tasa_descuento_pct", 8.0) / 100
    vida = parametros.get("vida_util_anos", 15)
    perdida = parametros.get("perdida_sistemica_pct", 5.0) / 100

    prob += pulp.lpSum([
        (
            (eq["costo_adquisicion_clp"] + eq.get("costo_instalacion_clp", 0)) *
            (tasa * (1 + tasa) ** vida) / ((1 + tasa) ** vida - 1) +
            eq.get("costo_mantencion_anual_clp", 0) +
            (eq["tasa_consumo"] * escenario["demanda_anual_kwh"] / (eq["potencia_nominal_kw"] * (1 - perdida))) *
            eq.get("unidades_por_gcal", 1)
        ) * x[eq["equipo_id"]]
        for eq in equipos
    ])

    prob += pulp.lpSum([eq["potencia_nominal_kw"] * x[eq["equipo_id"]] for eq in equipos]) >= escenario["peak_demanda_kw"]

    prob += pulp.lpSum([eq["potencia_nominal_kw"] * 8760 * x[eq["equipo_id"]] for eq in equipos]) >= escenario["demanda_anual_kwh"]

    prob += pulp.lpSum([x[eq["equipo_id"]] for eq in equipos]) >= 1

    return prob, x


def resolver_escenario(escenario, equipos, parametros):
    prob, variables = construir_milp(escenario, equipos, parametros)
    if prob is None:
        return None, variables

    try:
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
    except Exception as e:
        return None, str(e)

    import pulp
    if pulp.LpStatus[prob.status] == "Optimal":
        seleccionados = []
        for eq in equipos:
            if pulp.value(variables[eq["equipo_id"]]) == 1:
                seleccionados.append(eq)
        costo_total = pulp.value(prob.objective)
        return {
            "escenario_id": escenario["escenario_id"],
            "zona_termica": escenario["zona_termica"],
            "tipologia": escenario["tipologia"],
            "costo_anual_equivalente_clp": round(costo_total, 0) if costo_total else 0,
            "seleccionados": [
                {
                    "equipo_hvac_id": eq["equipo_id"],
                    "tecnologia_nombre": eq["tecnologia_nombre"],
                    "combustible_nombre": eq["combustible_nombre"],
                    "capacidad_asignada_kw": eq["potencia_nominal_kw"],
                    "es_seleccionado": 1,
                }
                for eq in seleccionados
            ],
        }, None
    return None, f"No factible para escenario {escenario['escenario_id']}"
