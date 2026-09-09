# Database Schema Contract: Shared SQLite DB

## File Location

`data/acond-termico.db` en la raiz del proyecto.

## Schema Naming Convention

- `sim_*` — Tablas de Feature 001 (Carga Resultados Simulacion)
- `hvac_*` — Tablas de Feature 002 (Catalogo Alternativas HVAC)  
- `opt_*` — Tablas de Feature 003 (Optimizacion MILP)
- `eco_*` — Tablas de Feature 004 (Modelo Econometrico)

## Feature 001 Tables

### sim_estudio

```sql
CREATE TABLE sim_estudio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha_creacion TEXT NOT NULL DEFAULT (date('now'))
);
```

### sim_simulacion

```sql
CREATE TABLE sim_simulacion (
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
```

### sim_resultado

```sql
CREATE TABLE sim_resultado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacion_id INTEGER NOT NULL UNIQUE REFERENCES sim_simulacion(id),
    u_prom REAL NOT NULL CHECK (u_prom BETWEEN 0.5 AND 5.0),
    demanda_anual_kwh REAL NOT NULL CHECK (demanda_anual_kwh BETWEEN 500 AND 20000),
    peak_demanda_kw REAL NOT NULL CHECK (peak_demanda_kw BETWEEN 1 AND 20),
    gdc REAL NOT NULL CHECK (gdc BETWEEN 200 AND 4000)
);
```

## Consumer Contract

Feature 003 (Optimizacion MILP) se compromete a:

- Leer desde `sim_simulacion` y `sim_resultado` para obtener los 36 escenarios
- NO escribir ni modificar tablas `sim_*`
- Reportar error si las tablas estan vacias o no existen

Feature 001 (Carga Resultados) se compromete a:

- Escribir datos completos y validados en `sim_*`
- Mantener la restriccion UNIQUE(tipologia, zona_termica) por estudio
- Proveer datos antes de que Feature 003 los consuma
