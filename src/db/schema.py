SCHEMA_VERSION = 3


def get_schema_version(conn):
    cur = conn.execute("PRAGMA user_version")
    return cur.fetchone()[0]


def set_schema_version(conn, version):
    conn.execute(f"PRAGMA user_version = {version}")


SCHEMA_SQL = """
-- Feature 001: Carga de Resultados de Simulacion
CREATE TABLE IF NOT EXISTS sim_estudio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha_creacion TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS sim_simulacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudio_id INTEGER NOT NULL REFERENCES sim_estudio(id),
    tipologia TEXT NOT NULL CHECK (tipologia IN (
        'aislada_1piso', 'aislada_2pisos', 'pareada_1piso', 'pareada_2pisos'
    )),
    zona_termica INTEGER NOT NULL CHECK (zona_termica BETWEEN 1 AND 9),
    descripcion TEXT,
    archivo_modelo TEXT,
    fecha_carga TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(estudio_id, tipologia, zona_termica)
);

CREATE TABLE IF NOT EXISTS sim_resultado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacion_id INTEGER NOT NULL UNIQUE REFERENCES sim_simulacion(id),
    u_prom REAL NOT NULL CHECK (u_prom BETWEEN 0.5 AND 5.0),
    demanda_anual_kwh REAL NOT NULL CHECK (demanda_anual_kwh BETWEEN 500 AND 20000),
    peak_demanda_kw REAL NOT NULL CHECK (peak_demanda_kw BETWEEN 1 AND 20),
    gdc REAL NOT NULL CHECK (gdc BETWEEN 200 AND 4000)
);

-- Feature 002: Catalogo Alternativas HVAC
CREATE TABLE IF NOT EXISTS hvac_combustible (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    unidad_medida TEXT NOT NULL,
    pci REAL NOT NULL CHECK (pci > 0),
    pcs REAL NOT NULL CHECK (pcs > 0),
    rendimiento_transformacion REAL NOT NULL CHECK (rendimiento_transformacion BETWEEN 0 AND 100),
    unidades_por_gcal REAL NOT NULL CHECK (unidades_por_gcal > 0)
);

CREATE TABLE IF NOT EXISTS hvac_tipo_tecnologia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS hvac_precio_combustible (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    combustible_id INTEGER NOT NULL REFERENCES hvac_combustible(id),
    region INTEGER NOT NULL CHECK (region BETWEEN 1 AND 16),
    precio_por_unidad REAL NOT NULL CHECK (precio_por_unidad > 0),
    fecha_vigencia TEXT NOT NULL,
    fuente TEXT NOT NULL CHECK (fuente IN ('MANUAL', 'CNE_API')),
    fecha_registro TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(combustible_id, region, fecha_vigencia)
);

CREATE TABLE IF NOT EXISTS hvac_equipo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_tecnologia_id INTEGER NOT NULL REFERENCES hvac_tipo_tecnologia(id),
    combustible_id INTEGER NOT NULL REFERENCES hvac_combustible(id),
    modelo TEXT NOT NULL,
    potencia_nominal_kw REAL NOT NULL CHECK (potencia_nominal_kw > 0),
    rendimiento_termico_pct REAL NOT NULL CHECK (rendimiento_termico_pct BETWEEN 0 AND 100),
    costo_adquisicion_clp REAL NOT NULL CHECK (costo_adquisicion_clp > 0),
    tasa_consumo REAL NOT NULL CHECK (tasa_consumo > 0),
    unidad_tasa_consumo TEXT NOT NULL,
    costo_instalacion_clp REAL DEFAULT 0 CHECK (costo_instalacion_clp >= 0),
    costo_mantencion_anual_clp REAL DEFAULT 0 CHECK (costo_mantencion_anual_clp >= 0),
    fuente_datos TEXT NOT NULL,
    url_fuente TEXT,
    fecha_registro TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(modelo, tipo_tecnologia_id)
);

-- Feature 003: Optimizacion MILP
CREATE TABLE IF NOT EXISTS opt_parametro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tasa_descuento_pct REAL NOT NULL CHECK (tasa_descuento_pct > 0),
    vida_util_anos INTEGER NOT NULL CHECK (vida_util_anos > 0),
    perdida_sistemica_pct REAL NOT NULL CHECK (perdida_sistemica_pct BETWEEN 0 AND 100),
    fecha_actualizacion TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS opt_resultado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    escenario_id INTEGER NOT NULL,
    zona_termica INTEGER NOT NULL CHECK (zona_termica BETWEEN 1 AND 9),
    tipologia TEXT NOT NULL,
    costo_anual_equivalente_clp REAL NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS opt_seleccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resultado_id INTEGER NOT NULL REFERENCES opt_resultado(id),
    equipo_hvac_id INTEGER NOT NULL,
    tecnologia_nombre TEXT NOT NULL,
    combustible_nombre TEXT NOT NULL,
    capacidad_asignada_kw REAL NOT NULL CHECK (capacidad_asignada_kw > 0),
    es_seleccionado INTEGER NOT NULL CHECK (es_seleccionado IN (0, 1))
);

-- Feature 004: Modelo Econometrico
CREATE TABLE IF NOT EXISTS eco_modelo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula TEXT NOT NULL,
    R2 REAL,
    R2_ajustado REAL,
    ECM REAL,
    F_statistic REAL,
    F_pvalue REAL,
    n_observaciones INTEGER NOT NULL DEFAULT 36,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS eco_coeficiente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL REFERENCES eco_modelo(id),
    variable_nombre TEXT NOT NULL,
    beta REAL NOT NULL,
    error_std REAL,
    t_statistic REAL,
    pvalue REAL,
    VIF REAL
);

CREATE TABLE IF NOT EXISTS eco_test_diagnostico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL REFERENCES eco_modelo(id),
    test_nombre TEXT NOT NULL,
    estadistico REAL,
    pvalue REAL,
    resultado TEXT NOT NULL CHECK (resultado IN ('pasa', 'falla'))
);

CREATE TABLE IF NOT EXISTS eco_escenario_whatif (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK (tipo IN ('parametrico', 'critico', 'multifactorial')),
    parametros_variados TEXT,
    valores TEXT,
    resultado_Y_costo REAL
);

CREATE TABLE IF NOT EXISTS eco_validacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL REFERENCES eco_modelo(id),
    resultado_global TEXT NOT NULL CHECK (resultado_global IN ('validado', 'no_validado')),
    razon_rechazo TEXT
);
"""
