REQUIRED_COLUMNS = [
    "tipologia",
    "zona_termica",
    "u_prom",
    "demanda_anual_kwh",
    "peak_demanda_kw",
    "gdc",
]


def validar_csv_headers(headers):
    faltantes = [c for c in REQUIRED_COLUMNS if c not in headers]
    if faltantes:
        return False, f"Columnas faltantes: {', '.join(faltantes)}"
    return True, None
