#!/usr/bin/env python3
"""
Populate Energy & Fuel Prices Database (Investigation 2026)
===========================================================
Populates data/acond-termico.db with the researched energy prices across 9 reference
cities / thermal zones (Antofagasta, Calama, Valparaiso, Santiago, Concepcion,
Temuco, Puerto Montt, Los Andes, Punta Arenas).
"""

import csv
import logging
import os
import shutil
import sqlite3
import sys
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("populate_energy_costs")

DB_PATH = "data/acond-termico.db"

RAW_RESEARCH_DATA = """
Ciudad	Energia	Unidad	Precio_Min	Precio_Max	Precio_Prom
Antofagasta	Electricidad	kWh	260	285	270
Antofagasta	Kerosene	Litro	781	1248	1086
Antofagasta	GLP	Cilindro 15kg	24500	28500	26500
Calama	Electricidad	kWh	270	295	282
Calama	Kerosene	Litro	900	1250	1050
Calama	GLP	Cilindro 15kg	25500	29500	27500
Valparaiso	Electricidad	kWh	220	292	270
Valparaiso	Kerosene	Litro	850	1310	975
Valparaiso	GLP	Cilindro 15kg	23500	28000	25500
Valparaiso	Gas Natural	m3	1876	2033	1954
Santiago	Electricidad	kWh	228	310	237
Santiago	Kerosene	Litro	816	1281	1060
Santiago	GLP	Cilindro 15kg	23000	30600	24500
Santiago	Gas Natural	m3	884	2121	1161
Concepcion	Electricidad	kWh	255	305	292
Concepcion	Kerosene	Litro	880	1554	1054
Concepcion	GLP	Cilindro 15kg	23500	26500	25000
Concepcion	Gas Natural	m3	926	2100	1950
Concepcion	Leña	Saco	2500	8000	3200
Concepcion	Pellet	Bolsa 15kg	3500	4900	4100
Temuco	Electricidad	kWh	272	300	284
Temuco	Kerosene	Litro	1050	1325	1180
Temuco	GLP	Cilindro 15kg	24000	28000	26500
Temuco	Gas Natural	m3	1800	2200	1980
Temuco	Leña	Saco	2500	4500	3500
Temuco	Pellet	Bolsa 15kg	3300	5500	3800
Puerto Montt	Electricidad	kWh	240	340	300
Puerto Montt	Kerosene	Litro	1097	1450	1250
Puerto Montt	GLP	Cilindro 15kg	26000	31000	28500
Puerto Montt	Leña	Saco	5000	9000	7000
Puerto Montt	Pellet	Bolsa 15kg	4800	6250	5300
Los Andes	Electricidad	kWh	275	295	282
Los Andes	Kerosene	Litro	900	1200	1050
Los Andes	GLP	Cilindro 15kg	24000	27500	26000
Los Andes	Gas Natural	m3	1876	2033	1954
Los Andes	Leña	Saco	3500	5500	4200
Los Andes	Pellet	Bolsa 15kg	4200	5600	4900
Punta Arenas	Electricidad	kWh	246	285	265
Punta Arenas	Kerosene	Litro	1200	1500	1350
Punta Arenas	GLP	Cilindro 15kg	28000	32000	30000
Punta Arenas	Gas Natural	m3	117	150	125
"""

CITY_METADATA = {
    "Antofagasta": {"zona": "A", "region": 2},
    "Calama": {"zona": "B", "region": 2},
    "Valparaiso": {"zona": "C", "region": 5},
    "Santiago": {"zona": "D", "region": 13},
    "Concepcion": {"zona": "E", "region": 8},
    "Temuco": {"zona": "F", "region": 9},
    "Puerto Montt": {"zona": "G", "region": 10},
    "Los Andes": {"zona": "H", "region": 5},
    "Punta Arenas": {"zona": "I", "region": 12},
}

FUEL_MAP = {
    "Electricidad": {"id": 6, "nombre": "electricidad", "base_unit": "kWh", "divisor": 1.0},
    "Kerosene": {"id": 1, "nombre": "parafina", "base_unit": "litro", "divisor": 1.0},
    "GLP": {"id": 2, "nombre": "gas_licuado", "base_unit": "kg", "divisor": 15.0},
    "Gas Natural": {"id": 3, "nombre": "gas_natural", "base_unit": "m3", "divisor": 1.0},
    "Leña": {"id": 5, "nombre": "lena", "base_unit": "kg", "divisor": 25.0}, # Saco 25kg leña seca estándar
    "Pellet": {"id": 4, "nombre": "pellet", "base_unit": "kg", "divisor": 15.0}, # Bolsa 15kg
}


def backup_database():
    if os.path.exists(DB_PATH):
        bak = f"{DB_PATH}.bak_pre_precios"
        shutil.copyfile(DB_PATH, bak)
        logger.info(f"Database backed up to {bak}")


def migrate_and_populate():
    backup_database()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # 1. Parse raw data
    lines = [line.split("\t") for line in RAW_RESEARCH_DATA.strip().split("\n")[1:]]
    parsed_records = []
    
    for row in lines:
        ciudad, energia, unidad, p_min_str, p_max_str, p_prom_str = row
        meta = CITY_METADATA.get(ciudad)
        finfo = FUEL_MAP.get(energia)
        if not meta or not finfo:
            logger.warning(f"Skipping unknown entry: {row}")
            continue
            
        p_min = float(p_min_str)
        p_max = float(p_max_str)
        p_prom = float(p_prom_str)
        divisor = finfo["divisor"]
        
        # Unit price normalized to base physical unit (kWh, litro, kg, m3)
        unit_prom = round(p_prom / divisor, 2)
        unit_min = round(p_min / divisor, 2)
        unit_max = round(p_max / divisor, 2)
        
        parsed_records.append({
            "ciudad": ciudad,
            "zona_termica": meta["zona"],
            "region": meta["region"],
            "combustible_id": finfo["id"],
            "combustible_nombre": finfo["nombre"],
            "energia_label": energia,
            "unidad_comercial": unidad,
            "precio_min_comercial": p_min,
            "precio_max_comercial": p_max,
            "precio_prom_comercial": p_prom,
            "divisor_conversion": divisor,
            "unidad_base": finfo["base_unit"],
            "precio_min_unidad": unit_min,
            "precio_max_unidad": unit_max,
            "precio_prom_unidad": unit_prom,
            "fecha_vigencia": "2026-09-01",
            "fuente": "MANUAL",
        })

    logger.info(f"Parsed {len(parsed_records)} price records.")

    # 2. Recreate / Upgrade hvac_precio_combustible table
    logger.info("Upgrading hvac_precio_combustible schema...")
    
    # Check if table has old data to backup
    cursor.execute("SELECT COUNT(*) FROM hvac_precio_combustible")
    old_count = cursor.fetchone()[0]
    logger.info(f"Found {old_count} old price rows in hvac_precio_combustible. Discarding old records...")

    # Drop and recreate with enhanced schema
    cursor.execute("DROP TABLE IF EXISTS hvac_precio_combustible")
    cursor.execute("""
        CREATE TABLE hvac_precio_combustible (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            combustible_id INTEGER NOT NULL REFERENCES hvac_combustible(id),
            region INTEGER NOT NULL CHECK (region BETWEEN 1 AND 16),
            ciudad TEXT,
            zona_termica TEXT,
            unidad_comercial TEXT,
            precio_min_comercial REAL,
            precio_max_comercial REAL,
            precio_prom_comercial REAL,
            divisor_conversion REAL DEFAULT 1.0,
            precio_por_unidad REAL NOT NULL CHECK (precio_por_unidad > 0),
            fecha_vigencia TEXT NOT NULL,
            fuente TEXT NOT NULL CHECK (fuente IN ('MANUAL', 'CNE_API')),
            fecha_registro TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(combustible_id, region, ciudad, fecha_vigencia)
        )
    """)

    # Insert the 41 researched rows
    insert_sql = """
        INSERT INTO hvac_precio_combustible (
            combustible_id, region, ciudad, zona_termica, unidad_comercial,
            precio_min_comercial, precio_max_comercial, precio_prom_comercial,
            divisor_conversion, precio_por_unidad, fecha_vigencia, fuente
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for r in parsed_records:
        cursor.execute(insert_sql, (
            r["combustible_id"],
            r["region"],
            r["ciudad"],
            r["zona_termica"],
            r["unidad_comercial"],
            r["precio_min_comercial"],
            r["precio_max_comercial"],
            r["precio_prom_comercial"],
            r["divisor_conversion"],
            r["precio_prom_unidad"], # Canonical price per unit
            r["fecha_vigencia"],
            r["fuente"],
        ))

    conn.commit()
    logger.info(f"Successfully inserted {len(parsed_records)} energy price records into hvac_precio_combustible.")

    # 3. Create dedicated matrix table hvac_matriz_precio_zona (Table 2 of report)
    cursor.execute("DROP TABLE IF EXISTS hvac_matriz_precio_zona")
    cursor.execute("""
        CREATE TABLE hvac_matriz_precio_zona (
            zona_termica TEXT PRIMARY KEY,
            ciudad TEXT NOT NULL,
            region INTEGER NOT NULL,
            electricidad_clp_kwh REAL,
            kerosene_clp_litro REAL,
            glp_clp_kg REAL,
            glp_clp_cilindro15kg REAL,
            gas_natural_clp_m3 REAL,
            lena_clp_kg REAL,
            lena_clp_saco25kg REAL,
            pellet_clp_kg REAL,
            pellet_clp_bolsa15kg REAL,
            fecha_actualizacion TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Build matrix by city
    matrix_rows = []
    for ciudad, meta in CITY_METADATA.items():
        zona = meta["zona"]
        reg = meta["region"]
        city_records = {r["energia_label"]: r for r in parsed_records if r["ciudad"] == ciudad}
        
        elec = city_records.get("Electricidad")
        kero = city_records.get("Kerosene")
        glp = city_records.get("GLP")
        gn = city_records.get("Gas Natural")
        lena = city_records.get("Leña")
        pellet = city_records.get("Pellet")

        matrix_rows.append((
            zona,
            ciudad,
            reg,
            elec["precio_prom_unidad"] if elec else None,
            kero["precio_prom_unidad"] if kero else None,
            glp["precio_prom_unidad"] if glp else None,
            glp["precio_prom_comercial"] if glp else None,
            gn["precio_prom_unidad"] if gn else None,
            lena["precio_prom_unidad"] if lena else None,
            lena["precio_prom_comercial"] if lena else None,
            pellet["precio_prom_unidad"] if pellet else None,
            pellet["precio_prom_comercial"] if pellet else None,
        ))

    cursor.executemany("""
        INSERT INTO hvac_matriz_precio_zona (
            zona_termica, ciudad, region,
            electricidad_clp_kwh, kerosene_clp_litro,
            glp_clp_kg, glp_clp_cilindro15kg,
            gas_natural_clp_m3,
            lena_clp_kg, lena_clp_saco25kg,
            pellet_clp_kg, pellet_clp_bolsa15kg
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, matrix_rows)

    conn.commit()
    conn.close()
    logger.info("Successfully created and populated hvac_matriz_precio_zona table.")

    # 4. Export CSV datasets
    df_records = pd.DataFrame(parsed_records)
    csv_costs_path = "data/costos_energia_investigacion_2026.csv"
    df_records.to_csv(csv_costs_path, index=False)
    logger.info(f"Exported detailed research costs to {csv_costs_path}")

    # Export Table 2 matrix format
    df_matrix = pd.DataFrame(matrix_rows, columns=[
        "Zona_Termica", "Ciudad", "Region",
        "Electricidad_CLP_kWh", "Kerosene_CLP_Litro",
        "GLP_CLP_kg", "GLP_CLP_Cilindro15kg",
        "Gas_Natural_CLP_m3",
        "Lena_CLP_kg", "Lena_CLP_Saco25kg",
        "Pellet_CLP_kg", "Pellet_CLP_Bolsa15kg"
    ])
    csv_matrix_path = "data/matriz_precios_zonas_termicas.csv"
    df_matrix.to_csv(csv_matrix_path, index=False)
    logger.info(f"Exported Table 2 matrix to {csv_matrix_path}")

    # Print summary
    print("\n" + "=" * 90)
    print("TABLA 2. MATRIZ DE PRECIOS BASE POR ZONA TÉRMICA Y CIUDAD DE REFERENCIA")
    print("=" * 90)
    display_df = df_matrix[[
        "Zona_Termica", "Ciudad", "Electricidad_CLP_kWh", "Kerosene_CLP_Litro",
        "GLP_CLP_kg", "Gas_Natural_CLP_m3", "Lena_CLP_kg", "Pellet_CLP_kg"
    ]].copy()
    display_df = display_df.fillna("-")
    print(display_df.to_string(index=False))
    print("=" * 90)


if __name__ == "__main__":
    migrate_and_populate()
