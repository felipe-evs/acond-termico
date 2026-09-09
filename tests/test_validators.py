from src.shared.validators import (
    validar_parametro,
    validar_tipologia,
    validar_zona_termica,
    validar_simulacion,
)


def test_validar_parametro_u_prom_valido():
    valido, msg = validar_parametro("u_prom", 2.5)
    assert valido
    assert msg is None


def test_validar_parametro_u_prom_invalido():
    valido, msg = validar_parametro("u_prom", -1)
    assert not valido
    assert "debe estar entre" in msg


def test_validar_tipologia_valida():
    valido, msg = validar_tipologia("aislada_1piso")
    assert valido


def test_validar_tipologia_invalida():
    valido, msg = validar_tipologia("invalida")
    assert not valido


def test_validar_zona_termica_valida():
    valido, msg = validar_zona_termica(5)
    assert valido


def test_validar_zona_termica_invalida():
    valido, msg = validar_zona_termica(10)
    assert not valido


def test_validar_simulacion_completa():
    data = {
        "tipologia": "aislada_1piso",
        "zona_termica": 5,
        "u_prom": 2.5,
        "demanda_anual_kwh": 8500,
        "peak_demanda_kw": 4.5,
        "gdc": 1500,
    }
    errores = validar_simulacion(data)
    assert errores == []


def test_validar_simulacion_errores():
    data = {
        "tipologia": "invalida",
        "zona_termica": 10,
        "u_prom": -1,
        "demanda_anual_kwh": 100,
        "peak_demanda_kw": 0.5,
        "gdc": 100,
    }
    errores = validar_simulacion(data)
    assert len(errores) >= 4
