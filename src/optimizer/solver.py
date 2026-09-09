import concurrent.futures
import logging
from src.db.connection import get_connection
from src.optimizer.reader import leer_escenarios, leer_equipos, leer_parametros
from src.optimizer.model import resolver_escenario

logger = logging.getLogger(__name__)


def ejecutar_optimizacion():
    escenarios = leer_escenarios()
    equipos = leer_equipos()
    parametros = leer_parametros()

    if not escenarios:
        return {"status": "error", "mensaje": "No hay escenarios cargados (Fase 1)"}
    if not equipos:
        return {"status": "error", "mensaje": "No hay equipos registrados (Fase 2)"}

    logger.info(f"Ejecutando optimizacion para {len(escenarios)} escenarios con {len(equipos)} equipos")

    resultados = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(len(escenarios), 8)) as executor:
        futuros = {executor.submit(resolver_escenario, e, equipos, parametros): e for e in escenarios}
        for futuro in concurrent.futures.as_completed(futuros):
            esc = futuros[futuro]
            try:
                resultado, error = futuro.result()
                if error:
                    logger.warning(f"Error en escenario {esc['escenario_id']}: {error}")
                else:
                    resultados.append(resultado)
            except Exception as e:
                logger.error(f"Excepcion en escenario {esc['escenario_id']}: {e}")

    conn = get_connection()
    for r in resultados:
        cur = conn.execute(
            "INSERT INTO opt_resultado (escenario_id, zona_termica, tipologia, costo_anual_equivalente_clp) VALUES (?, ?, ?, ?)",
            (r["escenario_id"], r["zona_termica"], r["tipologia"], r["costo_anual_equivalente_clp"]),
        )
        resultado_id = cur.lastrowid
        for sel in r["seleccionados"]:
            conn.execute(
                "INSERT INTO opt_seleccion (resultado_id, equipo_hvac_id, tecnologia_nombre, combustible_nombre, capacidad_asignada_kw, es_seleccionado) VALUES (?, ?, ?, ?, ?, ?)",
                (resultado_id, sel["equipo_hvac_id"], sel["tecnologia_nombre"],
                 sel["combustible_nombre"], sel["capacidad_asignada_kw"], sel["es_seleccionado"]),
            )
    conn.commit()
    conn.close()

    return {
        "status": "completed",
        "escenarios_resueltos": len(resultados),
        "total_escenarios": len(escenarios),
    }


class ParametroRepository:

    @staticmethod
    def get():
        from src.optimizer.reader import leer_parametros
        return leer_parametros()

    @staticmethod
    def update(tasa, vida, perdida):
        conn = get_connection()
        conn.execute("DELETE FROM opt_parametro")
        conn.execute(
            "INSERT INTO opt_parametro (tasa_descuento_pct, vida_util_anos, perdida_sistemica_pct) VALUES (?, ?, ?)",
            (tasa, vida, perdida),
        )
        conn.commit()
        conn.close()
        return {"tasa_descuento_pct": tasa, "vida_util_anos": vida, "perdida_sistemica_pct": perdida}


class ResultadoRepository:

    @staticmethod
    def list(zona_termica=None):
        conn = get_connection()
        query = "SELECT * FROM opt_resultado WHERE 1=1"
        params = []
        if zona_termica:
            query += " AND zona_termica=?"
            params.append(zona_termica)
        query += " ORDER BY zona_termica, tipologia"
        cur = conn.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_selecciones(resultado_id):
        conn = get_connection()
        cur = conn.execute("SELECT * FROM opt_seleccion WHERE resultado_id=?", (resultado_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
