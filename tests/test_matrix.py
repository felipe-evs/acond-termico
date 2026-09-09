from src.hvac.matrix import calcular_matriz


def test_calcular_matriz_sin_datos():
    rows = calcular_matriz()
    assert isinstance(rows, list)
