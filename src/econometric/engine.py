from src.econometric.model import leer_csv_resultados, preparar_datos
from src.econometric.regression import estimar_ols, extraer_resultados
from src.econometric.diagnostics import ejecutar_tests
from src.econometric.validation import validar_modelo
from src.econometric.whatif import analisis_parametrico, escenario_critico, analisis_multifactorial, guardar_whatif


def ejecutar_modelo(archivo_csv):
    df = leer_csv_resultados(archivo_csv)
    if df.empty:
        return {"status": "error", "mensaje": "Archivo CSV vacio"}
    n_obs = len(df)
    df_prep = preparar_datos(df)
    model, error = estimar_ols(df_prep)
    if error:
        return {"status": "error", "mensaje": f"Error en estimacion OLS: {error}"}
    modelo_id, modelo_db, coeficientes = extraer_resultados(model)
    tests, tests_aprobados, total_tests, r2, r2_adj, ecm = ejecutar_tests(model, modelo_id)
    resultado_val, razon = validar_modelo(modelo_id, tests_aprobados, total_tests)

    response = {
        "status": "completed" if resultado_val == "validado" else "no_validado",
        "modelo_id": modelo_id,
        "formula": modelo_db.formula,
        "R2": round(r2, 4),
        "R2_ajustado": round(r2_adj, 4),
        "ECM": round(ecm, 2),
        "n_observaciones": n_obs,
        "tests": {t[0]: {"estadistico": t[1], "pvalue": t[2], "resultado": t[3]} for t in tests},
        "tests_aprobados": tests_aprobados,
        "total_tests": total_tests,
        "validacion": resultado_val,
    }

    if resultado_val == "no_validado":
        response["razon_rechazo"] = razon
        response["whatif"] = ejecutar_whatif(df)

    return response


def ejecutar_whatif(df):
    resultados = []
    for col in df.select_dtypes(include=["float64", "int64"]).columns[:3]:
        if col != "costo_anual_equivalente_clp":
            r = analisis_parametrico(df, col, 10)
            resultados.append(r)
    criticos = escenario_critico(df, "alza_tarifaria")
    resultados.extend(criticos)
    multi = analisis_multifactorial(df, [
        {c: 10 for c in list(df.select_dtypes(include=["float64", "int64"]).columns[:2])},
    ])
    resultados.extend(multi)
    guardar_whatif(resultados)
    return resultados
