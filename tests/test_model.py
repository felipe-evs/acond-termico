from src.optimizer.reader import leer_parametros


def test_parametros_default():
    params = leer_parametros()
    assert "tasa_descuento_pct" in params
    assert params["tasa_descuento_pct"] > 0
