import pandas as pd
from src.db.connection import get_connection
from src.hvac.repository import EquipoHVACRepository
from src.hvac.constants import FUENTES_DATOS_PERMITIDAS


def importar_equipos(archivo):
    df = pd.read_csv(archivo)
    importados = 0
    errores = []
    for i, row in df.iterrows():
        conn = get_connection()
        cur_tec = conn.execute("SELECT id FROM hvac_tipo_tecnologia WHERE nombre=?", (row["tipo_tecnologia"],))
        tec = cur_tec.fetchone()
        cur_comb = conn.execute("SELECT id FROM hvac_combustible WHERE nombre=?", (row["combustible"],))
        comb = cur_comb.fetchone()
        conn.close()
        if not tec:
            errores.append({"fila": i, "error": f"Tecnologia '{row['tipo_tecnologia']}' no encontrada"})
            continue
        if not comb:
            errores.append({"fila": i, "error": f"Combustible '{row['combustible']}' no encontrado"})
            continue
        data = {
            "tipo_tecnologia_id": tec["id"],
            "combustible_id": comb["id"],
            "modelo": row.get("modelo", ""),
            "potencia_nominal_kw": float(row.get("potencia_nominal_kw", 0)),
            "rendimiento_termico_pct": float(row.get("rendimiento_termico_pct", 0)),
            "costo_adquisicion_clp": float(row.get("costo_adquisicion_clp", 0)),
            "tasa_consumo": float(row.get("tasa_consumo", 0)),
            "unidad_tasa_consumo": row.get("unidad_tasa_consumo", ""),
            "costo_instalacion_clp": float(row.get("costo_instalacion_clp", 0)),
            "costo_mantencion_anual_clp": float(row.get("costo_mantencion_anual_clp", 0)),
            "fuente_datos": row.get("fuente_datos", ""),
            "url_fuente": row.get("url_fuente"),
        }
        result, errs = EquipoHVACRepository.create(data)
        if result:
            importados += 1
        else:
            errores.append({"fila": i, "error": errs})
    return importados, errores
