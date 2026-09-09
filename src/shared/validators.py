VALIDATION_RANGES = {
    "u_prom": {"min": 0.5, "max": 5.0, "unit": "W/m2K"},
    "demanda_anual_kwh": {"min": 500, "max": 20000, "unit": "kWh/ano"},
    "peak_demanda_kw": {"min": 1, "max": 20, "unit": "kW"},
    "gdc": {"min": 200, "max": 4000, "unit": "grados dia base 15C"},
}

TIPOLOGIAS_VALIDAS = [
    "aislada_1piso",
    "aislada_2pisos",
    "pareada_1piso",
    "pareada_2pisos",
]

ZONAS_TERMICAS = list(range(1, 10))


def validar_parametro(nombre, valor):
    rango = VALIDATION_RANGES.get(nombre)
    if rango is None:
        return True, None
    if not (rango["min"] <= valor <= rango["max"]):
        msg = f"{nombre} debe estar entre {rango['min']} y {rango['max']} {rango['unit']}, valor ingresado: {valor}"
        return False, msg
    return True, None


def validar_tipologia(tipologia):
    if tipologia not in TIPOLOGIAS_VALIDAS:
        return False, f"Tipologia invalida: {tipologia}. Validas: {', '.join(TIPOLOGIAS_VALIDAS)}"
    return True, None


def validar_zona_termica(zona):
    if zona not in ZONAS_TERMICAS:
        return False, f"Zona termica invalida: {zona}. Debe ser 1-9"
    return True, None


FUENTES_DATOS_PERMITIDAS = [
    "Sodimac", "Easy", "MTS", "Distribuidor oficial",
    "Tienda especializada", "Casa Matriz",
]


def validar_fuente_datos(fuente):
    if fuente not in FUENTES_DATOS_PERMITIDAS:
        return False, f"Fuente de datos no permitida: {fuente}. Permitidas: {', '.join(FUENTES_DATOS_PERMITIDAS)}"
    return True, None


def validar_simulacion(data):
    errores = []
    for campo in ["u_prom", "demanda_anual_kwh", "peak_demanda_kw", "gdc"]:
        valido, msg = validar_parametro(campo, data.get(campo))
        if not valido:
            errores.append(msg)
    valido, msg = validar_tipologia(data.get("tipologia", ""))
    if not valido:
        errores.append(msg)
    valido, msg = validar_zona_termica(data.get("zona_termica"))
    if not valido:
        errores.append(msg)
    return errores
