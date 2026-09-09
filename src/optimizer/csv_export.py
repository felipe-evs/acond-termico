import pandas as pd
from src.optimizer.solver import ResultadoRepository


def exportar_resultados(archivo):
    rows = ResultadoRepository.list()
    if not rows:
        return False
    for r in rows:
        selecciones = ResultadoRepository.get_selecciones(r["id"])
        r["tecnologia_seleccionada"] = selecciones[0]["tecnologia_nombre"] if selecciones else ""
        r["combustible"] = selecciones[0]["combustible_nombre"] if selecciones else ""
        r["capacidad_kw"] = selecciones[0]["capacidad_asignada_kw"] if selecciones else 0
    df = pd.DataFrame(rows)
    df.to_csv(archivo, index=False, columns=[
        "zona_termica", "tipologia", "costo_anual_equivalente_clp",
        "tecnologia_seleccionada", "combustible", "capacidad_kw",
    ])
    return True
