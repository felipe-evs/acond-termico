import pandas as pd
from src.db.connection import get_connection


def analisis_parametrico(df, parametro, variacion_pct):
    df = df.copy()
    if parametro not in df.columns:
        return {"error": f"Parametro '{parametro}' no encontrado"}
    col_numeric = df[parametro].dtype in ["float64", "int64"]
    if not col_numeric:
        return {"error": f"Parametro '{parametro}' no es numerico"}
    original = df[parametro].mean()
    df_mod = df.copy()
    df_mod[parametro] = df_mod[parametro] * (1 + variacion_pct / 100)
    delta_prom = df_mod[parametro].mean() - original
    return {
        "parametro": parametro,
        "variacion_pct": variacion_pct,
        "valor_original_promedio": round(original, 2),
        "valor_modificado_promedio": round(df_mod[parametro].mean(), 2),
        "delta_promedio": round(delta_prom, 2),
    }


def escenario_critico(df, tipo):
    resultados = []
    if tipo == "desabastecimiento":
        for combustible in df.get("combustible", df.get("combustible_nombre", [])).unique():
            resultados.append({
                "tipo": "critico",
                "escenario": f"Desabastecimiento de {combustible}",
                "descripcion": "Alternativa no disponible",
            })
    elif tipo == "alza_tarifaria":
        df_mod = df.copy()
        cost_col = "costo_anual_equivalente_clp"
        if cost_col in df_mod.columns:
            df_mod[cost_col] = df_mod[cost_col] * 2
            resultados.append({
                "tipo": "critico",
                "escenario": "Alza tarifaria +100%",
                "costo_promedio_original": round(df[cost_col].mean(), 0),
                "costo_promedio_duplicado": round(df_mod[cost_col].mean(), 0),
            })
    return resultados


def analisis_multifactorial(df, variaciones):
    resultados = []
    for vars_dict in variaciones:
        df_mod = df.copy()
        desc = []
        for var, pct in vars_dict.items():
            if var in df_mod.columns:
                df_mod[var] = df_mod[var] * (1 + pct / 100)
                desc.append(f"{var} {pct:+.0f}%")
        cost_col = "costo_anual_equivalente_clp"
        if cost_col in df_mod.columns:
            delta = df_mod[cost_col].mean() - df[cost_col].mean()
            resultados.append({
                "tipo": "multifactorial",
                "variaciones": ", ".join(desc),
                "delta_costo_promedio": round(delta, 0),
            })
    return resultados


def guardar_whatif(resultados):
    conn = get_connection()
    for r in resultados:
        conn.execute(
            "INSERT INTO eco_escenario_whatif (tipo, parametros_variados, valores, resultado_Y_costo) VALUES (?, ?, ?, ?)",
            (r.get("tipo", ""), str(r.get("parametro", r.get("escenario", ""))),
             str(r.get("variacion_pct", r.get("descripcion", ""))),
             r.get("delta_promedio", r.get("costo_promedio_duplicado", r.get("delta_costo_promedio", 0)))),
        )
    conn.commit()
    conn.close()
