import tempfile
import os
import pandas as pd
from src.econometric.model import leer_csv_resultados, preparar_datos


def test_leer_csv_resultados():
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        f.write("zona_termica,tipologia,costo_anual_equivalente_clp,u_prom,gdc\n")
        f.write("5,aislada_1piso,285000,2.3,1500\n")
        f.write("8,pareada_2pisos,320000,1.8,2500\n")
        ruta = f.name
    df = leer_csv_resultados(ruta)
    os.unlink(ruta)
    assert len(df) == 2
    assert "costo_anual_equivalente_clp" in df.columns


def test_preparar_datos():
    df = pd.DataFrame({
        "zona_termica": [5, 8, 3],
        "tipologia": ["aislada_1piso", "pareada_2pisos", "aislada_2pisos"],
        "costo_anual_equivalente_clp": [285000, 320000, 310000],
        "u_prom": [2.3, 1.8, 2.0],
        "gdc": [1500, 2500, 1200],
    })
    df_prep = preparar_datos(df)
    assert "costo_anual_equivalente_clp" in df_prep.columns
    assert "zona_termica" not in df_prep.columns
    assert "tipologia" not in df_prep.columns
