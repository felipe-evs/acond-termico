import pandas as pd
from src.shared.csv_validator import validar_csv_headers, REQUIRED_COLUMNS
from src.estudio.repository import SimulacionRepository


def importar_simulaciones(archivo):
    df = pd.read_csv(archivo)
    valido, msg = validar_csv_headers(list(df.columns))
    if not valido:
        return 0, [{"error": msg}]
    simulaciones = df.to_dict("records")
    importados, errores = SimulacionRepository.bulk_create(simulaciones)
    return importados, errores


def exportar_simulaciones(archivo):
    rows = SimulacionRepository.list()
    if not rows:
        return False
    df = pd.DataFrame(rows)
    df.to_csv(archivo, index=False)
    return True
