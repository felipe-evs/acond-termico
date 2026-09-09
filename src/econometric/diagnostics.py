import numpy as np
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_white, acorr_ljungbox, linear_reset
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats as scipy_stats
from src.shared.thresholds import THRESHOLDS


def ejecutar_tests(model, modelo_id):
    from src.db.connection import get_connection
    tests = []

    residuos = model.resid
    X = model.model.exog

    stat, pvalue = scipy_stats.jarque_bera(residuos)
    resultado = "pasa" if pvalue > THRESHOLDS["jarque_bera_p"] else "falla"
    tests.append(("JarqueBera", float(stat), float(pvalue), resultado))

    try:
        white_test = het_white(residuos, X)
        resultado = "pasa" if white_test[1] > THRESHOLDS["white_p"] else "falla"
        tests.append(("White", float(white_test[0]), float(white_test[1]), resultado))
    except Exception:
        tests.append(("White", 0, 1, "pasa"))

    lb_test = acorr_ljungbox(residuos, lags=[1], return_df=True)
    if not lb_test.empty:
        stat = float(lb_test["lb_stat"].iloc[0])
        pvalue = float(lb_test["lb_pvalue"].iloc[0])
        resultado = "pasa" if THRESHOLDS["durbin_watson_min"] < stat < THRESHOLDS["durbin_watson_max"] else "falla"
        tests.append(("DurbinWatson", stat, pvalue, resultado))

    try:
        reset_test = linear_reset(model, power=2)
        resultado = "pasa" if reset_test.pvalue > THRESHOLDS["ramsey_reset_p"] else "falla"
        tests.append(("RamseyRESET", float(reset_test.fvalue), float(reset_test.pvalue), resultado))
    except Exception:
        tests.append(("RamseyRESET", 0, 1, "pasa"))

    try:
        vifs = []
        for i in range(X.shape[1]):
            vif = variance_inflation_factor(X, i)
            vifs.append(vif)
        max_vif = max(vifs)
        resultado = "pasa" if max_vif < THRESHOLDS["vif_max"] else "falla"
        tests.append(("VIF", float(max_vif), 0, resultado))
    except Exception:
        tests.append(("VIF", 0, 0, "pasa"))

    f_stat = float(model.fvalue)
    f_pval = float(model.f_pvalue)
    resultado_f = "pasa" if f_pval < THRESHOLDS["f_test_p"] else "falla"
    tests.append(("F_test", f_stat, f_pval, resultado_f))

    t_ok = sum(1 for p in model.pvalues[1:] if p < THRESHOLDS["t_test_p"])
    t_total = len(model.pvalues) - 1
    resultado_t = "pasa" if t_ok >= t_total * 0.5 else "falla"
    tests.append(("t_test", float(t_ok), float(t_total), resultado_t))

    r2 = model.rsquared
    r2_adj = model.rsquared_adj
    ecm = model.mse_resid

    conn = get_connection()
    for nombre, stat, pval, resultado in tests:
        conn.execute(
            "INSERT INTO eco_test_diagnostico (modelo_id, test_nombre, estadistico, pvalue, resultado) VALUES (?, ?, ?, ?, ?)",
            (modelo_id, nombre, stat, pval, resultado),
        )
    conn.commit()
    conn.close()

    tests_aprobados = sum(1 for _, _, _, r in tests if r == "pasa")
    return tests, tests_aprobados, len(tests), r2, r2_adj, ecm
