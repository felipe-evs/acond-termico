import pytest

from src.db.connection import init_db, get_connection
from src.hvac.repository import (
    CombustibleRepository,
    PrecioCombustibleRepository,
    TipoTecnologiaRepository,
)


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    import src.db.connection as conn_mod
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(conn_mod, "DB_PATH", str(db_file))
    init_db()
    yield str(db_file)


def _crear_combustible(nombre="parafina"):
    data = {
        "nombre": nombre,
        "unidad_medida": "litro",
        "pci": 8200,
        "pcs": 8800,
        "rendimiento_transformacion": 85,
        "unidades_por_gcal": 0.12,
    }
    result, errores = CombustibleRepository.create(data)
    assert errores == []
    return result


def test_combustible_update(temp_db):
    comb = _crear_combustible()
    result, errores = CombustibleRepository.update(comb.id, {"pci": 9000})
    assert errores == []
    assert result["updated"] is True
    actualizado = CombustibleRepository.get_by_id(comb.id)
    assert actualizado["pci"] == 9000


def test_combustible_delete_sin_dependencias(temp_db):
    comb = _crear_combustible()
    ok, errores = CombustibleRepository.delete(comb.id)
    assert ok is True
    assert errores == []
    assert CombustibleRepository.get_by_id(comb.id) is None


def test_combustible_delete_con_precio_bloqueado(temp_db):
    comb = _crear_combustible()
    PrecioCombustibleRepository.add({
        "combustible_id": comb.id,
        "region": 13,
        "precio_por_unidad": 1000,
        "fecha_vigencia": "2026-01-01",
        "fuente": "MANUAL",
    })
    ok, errores = CombustibleRepository.delete(comb.id)
    assert ok is False
    assert "precio(s)" in errores[0]
    assert CombustibleRepository.get_by_id(comb.id) is not None


def test_precio_update_y_delete(temp_db):
    comb = _crear_combustible()
    precio, errores = PrecioCombustibleRepository.add({
        "combustible_id": comb.id,
        "region": 13,
        "precio_por_unidad": 1000,
        "fecha_vigencia": "2026-01-01",
        "fuente": "MANUAL",
    })
    assert errores == []
    result, errores = PrecioCombustibleRepository.update(precio.id, {"precio_por_unidad": 1500})
    assert errores == []
    actualizado = PrecioCombustibleRepository.get_by_id(precio.id)
    assert actualizado["precio_por_unidad"] == 1500
    ok, errores = PrecioCombustibleRepository.delete(precio.id)
    assert ok is True
    assert PrecioCombustibleRepository.get_by_id(precio.id) is None
