from src.db.connection import get_connection
from src.hvac.models import Combustible, PrecioCombustible, TipoTecnologia, EquipoHVAC


class CombustibleRepository:

    @staticmethod
    def create(data):
        conn = get_connection()
        try:
            cur = conn.execute(
                """INSERT INTO hvac_combustible
                   (nombre, unidad_medida, pci, pcs, rendimiento_transformacion, unidades_por_gcal)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (data["nombre"], data["unidad_medida"], data["pci"], data["pcs"],
                 data["rendimiento_transformacion"], data["unidades_por_gcal"]),
            )
            conn.commit()
            return Combustible(id=cur.lastrowid, **data), []
        except Exception as e:
            conn.close()
            return None, [str(e)]
        finally:
            conn.close()

    @staticmethod
    def list():
        conn = get_connection()
        cur = conn.execute("SELECT * FROM hvac_combustible ORDER BY nombre")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_id(combustible_id):
        conn = get_connection()
        cur = conn.execute("SELECT * FROM hvac_combustible WHERE id=?", (combustible_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_nombre(nombre):
        conn = get_connection()
        cur = conn.execute("SELECT * FROM hvac_combustible WHERE nombre=?", (nombre,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update(combustible_id, data):
        conn = get_connection()
        try:
            fields = []
            vals = []
            for k in ["nombre", "unidad_medida", "pci", "pcs",
                      "rendimiento_transformacion", "unidades_por_gcal"]:
                if k in data:
                    fields.append(f"{k}=?")
                    vals.append(data[k])
            if not fields:
                return {"id": combustible_id, "updated": False}, []
            vals.append(combustible_id)
            conn.execute(f"UPDATE hvac_combustible SET {', '.join(fields)} WHERE id=?", vals)
            conn.commit()
            return {"id": combustible_id, "updated": True}, []
        except Exception as e:
            return None, [str(e)]
        finally:
            conn.close()

    @staticmethod
    def count_dependencies(combustible_id):
        conn = get_connection()
        cur_precios = conn.execute(
            "SELECT COUNT(*) as n FROM hvac_precio_combustible WHERE combustible_id=?",
            (combustible_id,),
        )
        precios = cur_precios.fetchone()["n"]
        cur_equipos = conn.execute(
            "SELECT COUNT(*) as n FROM hvac_equipo WHERE combustible_id=?",
            (combustible_id,),
        )
        equipos = cur_equipos.fetchone()["n"]
        conn.close()
        return {"precios": precios, "equipos": equipos}

    @staticmethod
    def delete(combustible_id):
        conn = get_connection()
        cur = conn.execute("SELECT id FROM hvac_combustible WHERE id=?", (combustible_id,))
        if not cur.fetchone():
            conn.close()
            return False, ["Combustible no encontrado."]
        deps = CombustibleRepository.count_dependencies(combustible_id)
        if deps["precios"] > 0 or deps["equipos"] > 0:
            conn.close()
            return False, [
                f"No se puede eliminar el combustible porque tiene "
                f"{deps['precios']} precio(s) y {deps['equipos']} equipo(s) asociados. "
                "Elimine primero las dependencias."
            ]
        conn.execute("DELETE FROM hvac_combustible WHERE id=?", (combustible_id,))
        conn.commit()
        conn.close()
        return True, []


class TipoTecnologiaRepository:

    @staticmethod
    def create(nombre):
        conn = get_connection()
        try:
            cur = conn.execute("INSERT INTO hvac_tipo_tecnologia (nombre) VALUES (?)", (nombre,))
            conn.commit()
            return TipoTecnologia(id=cur.lastrowid, nombre=nombre)
        except Exception:
            return None
        finally:
            conn.close()

    @staticmethod
    def list():
        conn = get_connection()
        cur = conn.execute("SELECT * FROM hvac_tipo_tecnologia ORDER BY nombre")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_id(tipo_id):
        conn = get_connection()
        cur = conn.execute("SELECT * FROM hvac_tipo_tecnologia WHERE id=?", (tipo_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_nombre(nombre):
        conn = get_connection()
        cur = conn.execute("SELECT * FROM hvac_tipo_tecnologia WHERE nombre=?", (nombre,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None


class PrecioCombustibleRepository:

    @staticmethod
    def add(data):
        conn = get_connection()
        try:
            cur = conn.execute(
                """INSERT INTO hvac_precio_combustible
                   (combustible_id, region, precio_por_unidad, fecha_vigencia, fuente)
                   VALUES (?, ?, ?, ?, ?)""",
                (data["combustible_id"], data["region"], data["precio_por_unidad"],
                 data["fecha_vigencia"], data.get("fuente", "MANUAL")),
            )
            conn.commit()
            return PrecioCombustible(id=cur.lastrowid, **data), []
        except Exception as e:
            return None, [str(e)]
        finally:
            conn.close()

    @staticmethod
    def list(combustible_id=None, region=None):
        conn = get_connection()
        query = "SELECT p.*, c.nombre as combustible_nombre FROM hvac_precio_combustible p JOIN hvac_combustible c ON p.combustible_id=c.id WHERE 1=1"
        params = []
        if combustible_id:
            query += " AND p.combustible_id=?"
            params.append(combustible_id)
        if region:
            query += " AND p.region=?"
            params.append(region)
        query += " ORDER BY p.fecha_vigencia DESC"
        cur = conn.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_id(precio_id):
        conn = get_connection()
        cur = conn.execute(
            """SELECT p.*, c.nombre as combustible_nombre
               FROM hvac_precio_combustible p
               JOIN hvac_combustible c ON p.combustible_id=c.id
               WHERE p.id=?""",
            (precio_id,),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update(precio_id, data):
        conn = get_connection()
        try:
            fields = []
            vals = []
            for k in ["combustible_id", "region", "precio_por_unidad",
                      "fecha_vigencia", "fuente"]:
                if k in data:
                    fields.append(f"{k}=?")
                    vals.append(data[k])
            if not fields:
                return {"id": precio_id, "updated": False}, []
            vals.append(precio_id)
            conn.execute(f"UPDATE hvac_precio_combustible SET {', '.join(fields)} WHERE id=?", vals)
            conn.commit()
            return {"id": precio_id, "updated": True}, []
        except Exception as e:
            return None, [str(e)]
        finally:
            conn.close()

    @staticmethod
    def delete(precio_id):
        conn = get_connection()
        cur = conn.execute("SELECT id FROM hvac_precio_combustible WHERE id=?", (precio_id,))
        if not cur.fetchone():
            conn.close()
            return False, ["Precio no encontrado."]
        conn.execute("DELETE FROM hvac_precio_combustible WHERE id=?", (precio_id,))
        conn.commit()
        conn.close()
        return True, []


class EquipoHVACRepository:

    @staticmethod
    def create(data):
        conn = get_connection()
        try:
            cur = conn.execute(
                """INSERT INTO hvac_equipo
                   (tipo_tecnologia_id, combustible_id, modelo, potencia_nominal_kw,
                    rendimiento_termico_pct, costo_adquisicion_clp, tasa_consumo,
                    unidad_tasa_consumo, costo_instalacion_clp, costo_mantencion_anual_clp,
                    fuente_datos, url_fuente)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data["tipo_tecnologia_id"], data["combustible_id"], data["modelo"],
                 data["potencia_nominal_kw"], data["rendimiento_termico_pct"],
                 data["costo_adquisicion_clp"], data["tasa_consumo"],
                 data["unidad_tasa_consumo"], data.get("costo_instalacion_clp", 0),
                 data.get("costo_mantencion_anual_clp", 0),
                 data["fuente_datos"], data.get("url_fuente")),
            )
            conn.commit()
            return EquipoHVAC(id=cur.lastrowid, **data), []
        except Exception as e:
            return None, [str(e)]
        finally:
            conn.close()

    @staticmethod
    def list(tipo_tecnologia_id=None):
        conn = get_connection()
        query = """SELECT e.*, t.nombre as tecnologia_nombre, c.nombre as combustible_nombre
                   FROM hvac_equipo e
                   JOIN hvac_tipo_tecnologia t ON e.tipo_tecnologia_id=t.id
                   JOIN hvac_combustible c ON e.combustible_id=c.id
                   WHERE 1=1"""
        params = []
        if tipo_tecnologia_id:
            query += " AND e.tipo_tecnologia_id=?"
            params.append(tipo_tecnologia_id)
        query += " ORDER BY t.nombre, e.modelo"
        cur = conn.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_id(equipo_id):
        conn = get_connection()
        cur = conn.execute(
            """SELECT e.*, t.nombre as tecnologia_nombre, c.nombre as combustible_nombre
               FROM hvac_equipo e
               JOIN hvac_tipo_tecnologia t ON e.tipo_tecnologia_id=t.id
               JOIN hvac_combustible c ON e.combustible_id=c.id
               WHERE e.id=?""",
            (equipo_id,),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update(equipo_id, data):
        conn = get_connection()
        try:
            fields = []
            vals = []
            for k in ["tipo_tecnologia_id", "combustible_id", "modelo", "potencia_nominal_kw",
                       "rendimiento_termico_pct", "costo_adquisicion_clp", "tasa_consumo",
                       "unidad_tasa_consumo", "costo_instalacion_clp", "costo_mantencion_anual_clp",
                       "fuente_datos", "url_fuente"]:
                if k in data:
                    fields.append(f"{k}=?")
                    vals.append(data[k])
            if not fields:
                return {"id": equipo_id, "updated": False}, []
            vals.append(equipo_id)
            conn.execute(f"UPDATE hvac_equipo SET {', '.join(fields)} WHERE id=?", vals)
            conn.commit()
            return {"id": equipo_id, "updated": True}, []
        except Exception as e:
            return None, [str(e)]
        finally:
            conn.close()

    @staticmethod
    def delete(equipo_id):
        conn = get_connection()
        cur = conn.execute("SELECT id FROM hvac_equipo WHERE id=?", (equipo_id,))
        if not cur.fetchone():
            conn.close()
            return False
        conn.execute("DELETE FROM hvac_equipo WHERE id=?", (equipo_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def count_by_tecnologia():
        conn = get_connection()
        cur = conn.execute(
            """SELECT t.nombre, COUNT(e.id) as cantidad
               FROM hvac_tipo_tecnologia t
               LEFT JOIN hvac_equipo e ON t.id=e.tipo_tecnologia_id
               GROUP BY t.id, t.nombre
               ORDER BY t.nombre"""
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
