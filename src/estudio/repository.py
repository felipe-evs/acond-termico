from src.db.connection import get_connection
from src.estudio.models import Estudio, Simulacion, ResultadoSimulacion
from src.shared.validators import validar_simulacion


class EstudioRepository:

    @staticmethod
    def init(nombre="Modelo Optimizacion Termico Chile", descripcion=None):
        conn = get_connection()
        cur = conn.execute("SELECT id FROM sim_estudio LIMIT 1")
        existing = cur.fetchone()
        if existing:
            conn.close()
            return existing["id"]
        cur = conn.execute(
            "INSERT INTO sim_estudio (nombre, descripcion) VALUES (?, ?)",
            (nombre, descripcion),
        )
        conn.commit()
        estudio_id = cur.lastrowid
        conn.close()
        return estudio_id

    @staticmethod
    def get():
        conn = get_connection()
        cur = conn.execute("SELECT * FROM sim_estudio LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if row:
            return Estudio(**dict(row))
        return None


class SimulacionRepository:

    @staticmethod
    def create(data):
        errores = validar_simulacion(data)
        if errores:
            return None, errores
        conn = get_connection()
        estudio = EstudioRepository.get()
        if not estudio:
            estudio_id = EstudioRepository.init()
        else:
            estudio_id = estudio.id
        try:
            cur = conn.execute(
                """INSERT INTO sim_simulacion
                   (estudio_id, tipologia, zona_termica, descripcion, archivo_modelo)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    estudio_id,
                    data["tipologia"],
                    data["zona_termica"],
                    data.get("descripcion"),
                    data.get("archivo_modelo"),
                ),
            )
            sim_id = cur.lastrowid
            conn.execute(
                """INSERT INTO sim_resultado
                   (simulacion_id, u_prom, demanda_anual_kwh, peak_demanda_kw, gdc)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    sim_id,
                    data["u_prom"],
                    data["demanda_anual_kwh"],
                    data["peak_demanda_kw"],
                    data["gdc"],
                ),
            )
            conn.commit()
            conn.close()
            return Simulacion(id=sim_id, **{k: data[k] for k in
                                             ["tipologia", "zona_termica", "descripcion", "archivo_modelo"]}), errores
        except Exception as e:
            conn.close()
            return None, [str(e)]

    @staticmethod
    def list():
        conn = get_connection()
        cur = conn.execute("""
            SELECT s.*, r.u_prom, r.demanda_anual_kwh, r.peak_demanda_kw, r.gdc
            FROM sim_simulacion s
            JOIN sim_resultado r ON s.id = r.simulacion_id
            ORDER BY s.zona_termica, s.tipologia
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_id(sim_id):
        conn = get_connection()
        cur = conn.execute(
            """SELECT s.*, r.u_prom, r.demanda_anual_kwh, r.peak_demanda_kw, r.gdc
               FROM sim_simulacion s
               JOIN sim_resultado r ON s.id = r.simulacion_id
               WHERE s.id = ?""",
            (sim_id,),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update(sim_id, data):
        errores = []
        if any(k in data for k in ["u_prom", "demanda_anual_kwh", "peak_demanda_kw", "gdc"]):
            for campo in ["u_prom", "demanda_anual_kwh", "peak_demanda_kw", "gdc"]:
                if campo in data:
                    from src.shared.validators import validar_parametro
                    valido, msg = validar_parametro(campo, data[campo])
                    if not valido:
                        errores.append(msg)
            if errores:
                return None, errores
        conn = get_connection()
        try:
            if any(k in data for k in ["tipologia", "zona_termica", "descripcion", "archivo_modelo"]):
                fields = []
                vals = []
                for k in ["tipologia", "zona_termica", "descripcion", "archivo_modelo"]:
                    if k in data:
                        fields.append(f"{k}=?")
                        vals.append(data[k])
                vals.append(sim_id)
                conn.execute(f"UPDATE sim_simulacion SET {', '.join(fields)} WHERE id=?", vals)
            if any(k in data for k in ["u_prom", "demanda_anual_kwh", "peak_demanda_kw", "gdc"]):
                fields = []
                vals = []
                for k in ["u_prom", "demanda_anual_kwh", "peak_demanda_kw", "gdc"]:
                    if k in data:
                        fields.append(f"{k}=?")
                        vals.append(data[k])
                vals.append(sim_id)
                conn.execute(f"UPDATE sim_resultado SET {', '.join(fields)} WHERE simulacion_id=?", vals)
            conn.commit()
            conn.close()
            return {"id": sim_id, "updated": True}, errores
        except Exception as e:
            conn.close()
            return None, [str(e)]

    @staticmethod
    def delete(sim_id):
        conn = get_connection()
        cur = conn.execute("SELECT id FROM sim_simulacion WHERE id=?", (sim_id,))
        if not cur.fetchone():
            conn.close()
            return False
        conn.execute("DELETE FROM sim_resultado WHERE simulacion_id=?", (sim_id,))
        conn.execute("DELETE FROM sim_simulacion WHERE id=?", (sim_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def bulk_create(simulaciones):
        importados = 0
        errores = []
        for i, data in enumerate(simulaciones):
            result, errs = SimulacionRepository.create(data)
            if result:
                importados += 1
            else:
                errores.append({"fila": i, "errores": errs})
        return importados, errores
