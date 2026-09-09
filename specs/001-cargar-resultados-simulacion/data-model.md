# Data Model: Carga de Resultados de Simulacion

## Entities

### Estudio

Contenedor unico del proyecto academico. Agrupa las 36 simulaciones.

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|---------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Identificador unico |
| nombre | TEXT | NOT NULL | Nombre del estudio |
| descripcion | TEXT | | Descripcion cualitativa |
| fecha_creacion | TEXT | NOT NULL, DEFAULT CURRENT_DATE | Fecha ISO 8601 |

**Relationships**: 1 Estudio -> N Simulaciones

### Simulacion

Representa una ejecucion de DesignBuilder para una combinacion tipologia + zona termica.

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|---------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Identificador unico |
| estudio_id | INTEGER | FK -> Estudio.id, NOT NULL | Estudio al que pertenece |
| tipologia | TEXT | NOT NULL, CHECK IN ('aislada_1piso', 'aislada_2pisos', 'pareada_1piso', 'pareada_2pisos') | Tipologia arquitectonica |
| zona_termica | INTEGER | NOT NULL, CHECK (1-9) | Zona termica segun normativa chilena |
| descripcion | TEXT | | Caracterizacion cualitativa del caso |
| archivo_modelo | TEXT | | Ruta al archivo .idf/.eso adjunto (opcional) |
| fecha_carga | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Momento de carga |

**Unique Constraint**: UNIQUE(estudio_id, tipologia, zona_termica) — no duplicar combinaciones.

**Relationships**: 1 Simulacion -> 1 ResultadoSimulacion

### ResultadoSimulacion

Valores numericos de salida de la simulacion. Datos obligatorios para las etapas siguientes.

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|---------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Identificador unico |
| simulacion_id | INTEGER | FK -> Simulacion.id, NOT NULL, UNIQUE | One-to-one con Simulacion |
| u_prom | REAL | NOT NULL, CHECK (0.5-5.0) | Transmitancia termica promedio ponderada (W/m2K) |
| demanda_anual_kwh | REAL | NOT NULL, CHECK (500-20000) | Demanda de energia anual (kWh/ano) |
| peak_demanda_kw | REAL | NOT NULL, CHECK (1-20) | Pico de demanda termica (kW) |
| gdc | REAL | NOT NULL, CHECK (200-4000) | Grados Dia de Calefaccion |

**Relationships**: 1 ResultadoSimulacion -> 1 Simulacion (one-to-one via FK unico)

## SQL Schema

```sql
CREATE TABLE estudio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha_creacion TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE simulacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudio_id INTEGER NOT NULL REFERENCES estudio(id),
    tipologia TEXT NOT NULL CHECK (tipologia IN (
        'aislada_1piso', 'aislada_2pisos', 'pareada_1piso', 'pareada_2pisos'
    )),
    zona_termica INTEGER NOT NULL CHECK (zona_termica BETWEEN 1 AND 9),
    descripcion TEXT,
    archivo_modelo TEXT,
    fecha_carga TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(estudio_id, tipologia, zona_termica)
);

CREATE TABLE resultado_simulacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacion_id INTEGER NOT NULL UNIQUE REFERENCES simulacion(id),
    u_prom REAL NOT NULL CHECK (u_prom BETWEEN 0.5 AND 5.0),
    demanda_anual_kwh REAL NOT NULL CHECK (demanda_anual_kwh BETWEEN 500 AND 20000),
    peak_demanda_kw REAL NOT NULL CHECK (peak_demanda_kw BETWEEN 1 AND 20),
    gdc REAL NOT NULL CHECK (gdc BETWEEN 200 AND 4000)
);
```

## State Transitions

- **Estudio**: Se crea automaticamente al iniciar el sistema por primera vez. No se elimina.
- **Simulacion**: Se crea (carga manual o CSV import), se puede editar (UPDATE), se puede eliminar (DELETE). No hay otros estados.
- **ResultadoSimulacion**: Se crea junto con Simulacion (misma transaccion). Se edita en conjunto. Se elimina en cascada con Simulacion.

## Data Volume

- 1 Estudio
- 36 Simulaciones (4 tipologias x 9 zonas)
- 36 ResultadosSimulacion (one-to-one)
- ~100 KB total sin archivos adjuntos
- Archivos adjuntos opcionales: ~1-50 MB cada uno (archivos .idf/.eso)
