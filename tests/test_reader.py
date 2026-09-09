from src.db.connection import init_db, get_connection


def test_reader_escenarios_vacio():
    init_db()
    from src.optimizer.reader import leer_escenarios
    escenarios = leer_escenarios()
    assert isinstance(escenarios, list)


def test_reader_equipos_vacio():
    init_db()
    from src.optimizer.reader import leer_equipos
    equipos = leer_equipos()
    assert isinstance(equipos, list)
