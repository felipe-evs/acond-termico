import tempfile
import os
import pytest


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def sample_simulacion_data():
    return {
        "tipologia": "aislada_1piso",
        "zona_termica": 5,
        "u_prom": 2.3,
        "demanda_anual_kwh": 8500,
        "peak_demanda_kw": 4.5,
        "gdc": 1500,
        "descripcion": "Caso zona central",
    }
