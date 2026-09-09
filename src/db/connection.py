import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "acond-termico.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate_precio_fuente(conn):
    """Recrea hvac_precio_combustible si su CHECK de fuente aún incluye fuentes antiguas."""
    cur = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='hvac_precio_combustible'"
    )
    row = cur.fetchone()
    if not row or "CNE_SCRAPING" not in (row["sql"] or ""):
        return
    conn.execute("BEGIN")
    try:
        conn.execute("""
            CREATE TABLE hvac_precio_combustible_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                combustible_id INTEGER NOT NULL REFERENCES hvac_combustible(id),
                region INTEGER NOT NULL CHECK (region BETWEEN 1 AND 16),
                precio_por_unidad REAL NOT NULL CHECK (precio_por_unidad > 0),
                fecha_vigencia TEXT NOT NULL,
                fuente TEXT NOT NULL CHECK (fuente IN ('MANUAL', 'CNE_API')),
                fecha_registro TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(combustible_id, region, fecha_vigencia)
            )
        """)
        conn.execute("""
            INSERT INTO hvac_precio_combustible_new
                (id, combustible_id, region, precio_por_unidad, fecha_vigencia, fuente, fecha_registro)
            SELECT id, combustible_id, region, precio_por_unidad, fecha_vigencia,
                   CASE WHEN fuente IN ('CNE_SCRAPING', 'CNE_CSV') THEN 'MANUAL' ELSE fuente END,
                   fecha_registro
            FROM hvac_precio_combustible
        """)
        conn.execute("DROP TABLE hvac_precio_combustible")
        conn.execute("ALTER TABLE hvac_precio_combustible_new RENAME TO hvac_precio_combustible")
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db():
    from src.db.schema import SCHEMA_SQL, get_schema_version, set_schema_version, SCHEMA_VERSION
    conn = get_connection()
    current_version = get_schema_version(conn)
    if current_version < SCHEMA_VERSION:
        conn.executescript(SCHEMA_SQL)
        set_schema_version(conn, SCHEMA_VERSION)
        conn.commit()
    _migrate_precio_fuente(conn)
    conn.close()
