#!/usr/bin/env python3
"""
Populate HVAC Database with Scraped & Normalized 2026 Catalog
============================================================
Discards outdated database records and populates data/acond-termico.db
with the complete universe of updated heating and air conditioning models
scraped from SoloTodo.cl (using the highest store price c/IVA).
"""

import json
import logging
import os
import re
import shutil
import sqlite3
import sys

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("populate_db")

DB_PATH = "data/acond-termico.db"
SCRAPED_JSON = "data/solotodo_scraped_products.json"


def backup_database():
    if os.path.exists(DB_PATH):
        backup_path = f"{DB_PATH}.bak_populate"
        shutil.copyfile(DB_PATH, backup_path)
        logger.info(f"Database backed up to {backup_path}")


def add_columns_if_missing(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(hvac_equipo)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    columns_to_add = [
        ("marca", "TEXT"),
        ("cop_calor", "REAL"),
        ("poder_calorifico_bruto", "TEXT"),
        ("rango_calefaccion", "TEXT"),
        ("tienda", "TEXT"),
        ("url_tienda", "TEXT"),
        ("otros", "TEXT"),
        ("id_solotodo", "INTEGER"),
    ]

    for col_name, col_type in columns_to_add:
        if col_name not in existing_cols:
            logger.info(f"Adding column '{col_name} {col_type}' to hvac_equipo...")
            cursor.execute(f"ALTER TABLE hvac_equipo ADD COLUMN {col_name} {col_type}")
    conn.commit()


def main():
    backup_database()

    if not os.path.exists(SCRAPED_JSON):
        logger.error(f"File not found: {SCRAPED_JSON}")
        sys.exit(1)

    with open(SCRAPED_JSON, "r", encoding="utf-8") as f:
        products = json.load(f)

    logger.info(f"Loaded {len(products)} scraped products from {SCRAPED_JSON}")

    # Sort descending by price to ensure highest price is kept upon deduplication
    products.sort(key=lambda x: x["precio_max_c_iva_clp"], reverse=True)

    seen_keys = set()
    records_to_insert = []

    for p in products:
        brand = p["marca"].strip()
        model = p["modelo"].strip()
        full_model = f"{brand} {model}".strip() if not model.startswith(brand) else model

        tipo = p["tipo"].lower()
        cat = p["categoria_solotodo"].lower()
        comb = p["combustible"].lower()

        # Map to hvac_tipo_tecnologia:
        # 1: split_inverter
        # 2: estufa_lena
        # 3: estufa_pellet
        # 4: estufa_parafina
        # 5: estufa_gas
        # 6: estufa_electrica
        if "split" in tipo or "split" in cat:
            tec_id = 1
            tec_name = "split_inverter"
        elif "leña" in tipo or "leña" in comb:
            tec_id = 2
            tec_name = "estufa_lena"
        elif "pellet" in tipo or "pellet" in comb:
            tec_id = 3
            tec_name = "estufa_pellet"
        elif "parafina" in tipo or "kerosene" in comb or "parafina" in comb:
            tec_id = 4
            tec_name = "estufa_parafina"
        elif "gas" in tipo or "gas" in comb:
            tec_id = 5
            tec_name = "estufa_gas"
        else:
            tec_id = 6
            tec_name = "estufa_electrica"

        # Deduplicate strictly on (full_model.lower(), tec_id)
        dedup_key = (full_model.lower(), tec_id)
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        # Map to hvac_combustible:
        # 1: parafina
        # 2: gas_licuado
        # 3: gas_natural
        # 4: pellet
        # 5: lena
        # 6: electricidad
        if "parafina" in comb or "kerosene" in comb:
            comb_id = 1
            comb_name = "parafina"
        elif "gas natural" in comb or "gn" in comb:
            comb_id = 3
            comb_name = "gas_natural"
        elif "gas" in comb or "glp" in comb:
            comb_id = 2
            comb_name = "gas_licuado"
        elif "pellet" in comb:
            comb_id = 4
            comb_name = "pellet"
        elif "leña" in comb:
            comb_id = 5
            comb_name = "lena"
        else:
            comb_id = 6
            comb_name = "electricidad"

        # Determine Nominal Power (kW)
        kw = 0.0
        raw_pwr = p["poder_calorifico_bruto"]
        m_w = re.search(r"(\d+(?:\.\d+)?)\s*W", raw_pwr)
        if m_w:
            kw = float(m_w.group(1)) / 1000.0
        m_kcal = re.search(r"(\d+(?:\.\d+)?)\s*Kcal", raw_pwr, re.I)
        if not kw and m_kcal:
            kw = float(m_kcal.group(1)) * 0.001163
        m_btu = re.search(r"(\d+(?:\.\d+)?)\s*BTU", raw_pwr, re.I)
        if not kw and m_btu:
            kw = float(m_btu.group(1)) * 0.000293071
        m_kw = re.search(r"(\d+(?:\.\d+)?)\s*kW", raw_pwr, re.I)
        if not kw and m_kw:
            kw = float(m_kw.group(1))

        # Infer from name if missing
        if not kw:
            m_name_btu = re.search(r"(\d{4,5})\s*btu", p["nombre_completo"], re.I)
            if m_name_btu:
                kw = float(m_name_btu.group(1)) * 0.000293071
            m_name_w = re.search(r"(\d{3,4})\s*w\b", p["nombre_completo"], re.I)
            if not kw and m_name_w:
                kw = float(m_name_w.group(1)) / 1000.0

        # Standard technical fallback if completely missing
        if not kw or kw <= 0:
            if tec_name == "estufa_lena":
                kw = 8.5
            elif tec_name == "estufa_pellet":
                kw = 7.0
            elif tec_name == "estufa_parafina":
                kw = 3.0
            elif tec_name == "estufa_gas":
                kw = 4.2 if ("patio" not in tipo and "terraza" not in tipo) else 11.5
            elif tec_name == "split_inverter":
                kw = 3.52  # 12000 BTU
            else:
                kw = 1.5  # 1500 W convector

        # Guard against raw Watts parsed without unit conversion
        if kw >= 100.0:
            kw = kw / 1000.0

        kw = round(max(kw, 0.4), 2)

        # Determine COP (Heating Mode only)
        cop = None
        if tec_name == "split_inverter":
            raw_cop = p.get("cop_calor", "")
            m_cop = re.search(r"(\d+(?:\.\d+)?)", raw_cop)
            cop = float(m_cop.group(1)) if m_cop else 3.20
        elif "portátil" in tipo or "portatil" in cat:
            cop = 2.60 if "calor" in p["nombre_completo"].lower() else None

        # Determine Rendimiento Térmico (%)
        # Check constraint: BETWEEN 0 AND 100
        if comb_name == "electricidad":
            rend = 100.0
        elif comb_name == "pellet":
            rend = 85.0
        elif comb_name == "lena":
            rend = 65.0
        elif "tiro forzado" in tipo or "tiro balanceado" in tipo:
            rend = 92.7
        else:
            rend = 80.0

        # Determine Tasa de Consumo & Unidad
        if comb_name == "electricidad":
            c_cop = cop if (cop and cop > 1.0) else 1.0
            tasa = round(kw / c_cop, 3)
            unit = "kWh/h"
        elif comb_name == "parafina":
            tasa = round(kw / (9.8 * (rend / 100.0)), 3)
            unit = "litro/h"
        elif comb_name == "gas_licuado":
            tasa = round(kw / (12.8 * (rend / 100.0)), 3)
            unit = "kg/h"
        elif comb_name == "gas_natural":
            tasa = round(kw / (10.8 * (rend / 100.0)), 3)
            unit = "m3/h"
        elif comb_name == "pellet":
            tasa = round(kw / (4.8 * (rend / 100.0)), 3)
            unit = "kg/h"
        elif comb_name == "lena":
            tasa = round(kw / (3.8 * (rend / 100.0)), 3)
            unit = "kg/h"
        else:
            tasa = kw
            unit = "unidad/h"

        tasa = max(tasa, 0.01)

        # Installation & Maintenance Costs (CLP)
        p_max = float(p["precio_max_c_iva_clp"])

        if tec_name == "split_inverter":
            c_inst = 100000.0
            c_mant = 40000.0
        elif tec_name in ["estufa_pellet", "estufa_lena"]:
            c_inst = 120000.0
            c_mant = 45000.0 if tec_name == "estufa_pellet" else 30000.0
        elif "tiro forzado" in tipo or "tiro balanceado" in tipo:
            c_inst = 75000.0
            c_mant = 35000.0
        elif tec_name == "estufa_parafina":
            c_inst = 0.0
            c_mant = 35000.0 if ("laser" in tipo or "láser" in tipo) else 12500.0
        elif tec_name == "estufa_gas":
            c_inst = 0.0
            c_mant = 10000.0
        elif "portátil" in tipo or "portatil" in cat:
            c_inst = 0.0
            c_mant = 25000.0
        else:
            c_inst = 0.0
            c_mant = 0.0

        fuente_datos = p["tienda_precio_max"].split(" (")[0].strip() or "SoloTodo"
        url_fuente = p["url_tienda_precio_max"] or p["url_solotodo"]

        records_to_insert.append(
            (
                tec_id,
                comb_id,
                full_model,
                kw,
                rend,
                p_max,
                tasa,
                unit,
                c_inst,
                c_mant,
                fuente_datos,
                url_fuente,
                brand,
                cop,
                raw_pwr,
                p["rango_calefaccion"],
                p["tienda_precio_max"],
                p["url_tienda_precio_max"],
                p["otros"],
                p["id_solotodo"],
            )
        )

    logger.info(f"Prepared {len(records_to_insert)} distinct equipment records for insertion.")

    conn = sqlite3.connect(DB_PATH)
    add_columns_if_missing(conn)

    cursor = conn.cursor()

    # Discard outdated equipment rows
    cursor.execute("SELECT COUNT(*) FROM hvac_equipo")
    old_count = cursor.fetchone()[0]
    logger.info(f"Discarding {old_count} old/outdated rows from hvac_equipo...")
    cursor.execute("DELETE FROM hvac_equipo")

    # Insert updated 2026 catalog
    insert_sql = """
        INSERT INTO hvac_equipo (
            tipo_tecnologia_id, combustible_id, modelo, potencia_nominal_kw,
            rendimiento_termico_pct, costo_adquisicion_clp, tasa_consumo,
            unidad_tasa_consumo, costo_instalacion_clp, costo_mantencion_anual_clp,
            fuente_datos, url_fuente, marca, cop_calor, poder_calorifico_bruto,
            rango_calefaccion, tienda, url_tienda, otros, id_solotodo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cursor.executemany(insert_sql, records_to_insert)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM hvac_equipo")
    new_count = cursor.fetchone()[0]
    logger.info(f"Successfully populated hvac_equipo with {new_count} updated records.")

    # Summary by Technology
    logger.info("\n=== POBLACIÓN POR TECNOLOGÍA EN BD ===")
    cursor.execute("""
        SELECT t.nombre, COUNT(e.id), MIN(e.costo_adquisicion_clp),
               AVG(e.costo_adquisicion_clp), MAX(e.costo_adquisicion_clp)
        FROM hvac_equipo e
        JOIN hvac_tipo_tecnologia t ON e.tipo_tecnologia_id = t.id
        GROUP BY t.nombre
        ORDER BY COUNT(e.id) DESC
    """)
    for row in cursor.fetchall():
        logger.info(f"  • {row[0]}: {row[1]} equipos | Rango CLP: ${row[2]:,.0f} - ${row[4]:,.0f} | Promedio: ${row[3]:,.0f}")

    # Summary by Fuel
    logger.info("\n=== POBLACIÓN POR COMBUSTIBLE EN BD ===")
    cursor.execute("""
        SELECT c.nombre, COUNT(e.id), MIN(e.costo_adquisicion_clp),
               AVG(e.costo_adquisicion_clp), MAX(e.costo_adquisicion_clp)
        FROM hvac_equipo e
        JOIN hvac_combustible c ON e.combustible_id = c.id
        GROUP BY c.nombre
        ORDER BY COUNT(e.id) DESC
    """)
    for row in cursor.fetchall():
        logger.info(f"  • {row[0]}: {row[1]} equipos | Rango CLP: ${row[2]:,.0f} - ${row[4]:,.0f} | Promedio: ${row[3]:,.0f}")

    conn.close()
    logger.info("\nDatabase population completed successfully!")


if __name__ == "__main__":
    main()
