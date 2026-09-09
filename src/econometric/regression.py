import statsmodels.api as sm
import pandas as pd
import numpy as np


def estimar_ols(df):
    y_var = "costo_anual_equivalente_clp"
    if y_var not in df.columns:
        return None, "Variable dependiente no encontrada"

    exclude_cols = {y_var, "id", "escenario_id", "timestamp", "tecnologia_seleccionada", "combustible", "capacidad_kw"}
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    if not feature_cols:
        return None, "No hay variables independientes"

    X = df[feature_cols].copy()
    X = X.select_dtypes(include=[np.number]).dropna(axis=1)
    y = df[y_var]

    if len(X) < 3:
        return None, "Muy pocas observaciones"

    X = sm.add_constant(X)
    try:
        model = sm.OLS(y, X).fit()
    except Exception as e:
        return None, str(e)

    return model, None


def extraer_resultados(model):
    from src.econometric.model import ModeloEconometrico, CoeficienteRegresion
    from src.db.connection import get_connection

    n_vars = len(model.params) - 1
    formula = f"Y = {model.params.iloc[0]:.4f}"
    for i in range(1, len(model.params)):
        formula += f" + {model.params.iloc[i]:.4f}*{model.params.index[i]}"

    modelo_db = ModeloEconometrico(
        formula=formula,
        R2=model.rsquared,
        R2_ajustado=model.rsquared_adj,
        ECM=model.mse_resid,
        F_statistic=model.fvalue,
        F_pvalue=model.f_pvalue,
        n_observaciones=int(model.nobs),
    )

    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO eco_modelo (formula, R2, R2_ajustado, ECM, F_statistic, F_pvalue, n_observaciones) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (modelo_db.formula, modelo_db.R2, modelo_db.R2_ajustado, modelo_db.ECM,
         modelo_db.F_statistic, modelo_db.F_pvalue, modelo_db.n_observaciones),
    )
    modelo_id = cur.lastrowid

    coeficientes = []
    X = model.model.exog
    for i, var in enumerate(model.params.index):
        vif_val = None
        if var != "const" and X.shape[1] > 2:
            try:
                from statsmodels.stats.outliers_influence import variance_inflation_factor
                idx = list(model.params.index).index(var)
                vif_val = variance_inflation_factor(X, idx)
            except Exception:
                pass
        conn.execute(
            "INSERT INTO eco_coeficiente (modelo_id, variable_nombre, beta, error_std, t_statistic, pvalue, VIF) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (modelo_id, var, model.params[i], model.bse[i], model.tvalues[i], model.pvalues[i], vif_val),
        )
        coeficientes.append(CoeficienteRegresion(
            modelo_id=modelo_id, variable_nombre=var, beta=model.params[i],
            error_std=model.bse[i], t_statistic=model.tvalues[i],
            pvalue=model.pvalues[i], VIF=vif_val,
        ))
    conn.commit()
    conn.close()

    return modelo_id, modelo_db, coeficientes
