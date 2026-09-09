import pandas as pd
from src.db.connection import get_connection


def exportar_resultados(archivo):
    conn = get_connection()
    cur = conn.execute("SELECT * FROM eco_modelo ORDER BY id DESC LIMIT 1")
    modelo = cur.fetchone()
    if not modelo:
        conn.close()
        return False
    modelo_id = modelo["id"]
    cur = conn.execute("SELECT * FROM eco_coeficiente WHERE modelo_id=?", (modelo_id,))
    coefs = [dict(r) for r in cur.fetchall()]
    cur = conn.execute("SELECT * FROM eco_test_diagnostico WHERE modelo_id=?", (modelo_id,))
    tests = [dict(r) for r in cur.fetchall()]
    cur = conn.execute("SELECT * FROM eco_validacion WHERE modelo_id=?", (modelo_id,))
    val = cur.fetchone()
    conn.close()

    with pd.ExcelWriter(archivo, engine="openpyxl") as writer:
        pd.DataFrame([dict(modelo)]).to_csv(archivo.replace(".xlsx", "_modelo.csv"), index=False)
        pd.DataFrame(coefs).to_csv(archivo.replace(".xlsx", "_coeficientes.csv"), index=False)
        pd.DataFrame(tests).to_csv(archivo.replace(".xlsx", "_tests.csv"), index=False)
        if val:
            pd.DataFrame([dict(val)]).to_csv(archivo.replace(".xlsx", "_validacion.csv"), index=False)
    return True
