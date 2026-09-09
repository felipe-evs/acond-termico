from src.db.connection import init_db, get_connection


def test_schema_has_hvac_tables():
    init_db()
    conn = get_connection()
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r["name"] for r in cur.fetchall()]
    conn.close()
    assert "hvac_combustible" in tables
    assert "hvac_tipo_tecnologia" in tables
    assert "hvac_precio_combustible" in tables
    assert "hvac_equipo" in tables
