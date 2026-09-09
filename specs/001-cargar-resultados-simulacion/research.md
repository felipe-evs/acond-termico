# Research: Carga de Resultados de Simulacion

## Tech Stack Decisions

### GUI Framework: Streamlit vs Flask

**Decision**: Streamlit

**Rationale**: El proyecto academic no requiere una web app compleja. Streamlit permite crear una
GUI funcional con minimo codigo, ideal para formularios CRUD y visualizacion de datos tabulares.
Se integra naturalmente con pandas para CSV import/export.

**Alternatives considered**:
- Flask: Mas flexible pero requiere mas boilerplate para CRUD simple. Sobredimensionado para el alcance actual.
- Tkinter: Nativo pero interfaz menos moderna y mas complejidad para CSV handling.

### CLI Framework: Click vs argparse

**Decision**: Click

**Rationale**: Click proporciona comandos anidados, validacion de parametros y ayuda automatica.
Estandar en el ecosistema Python para CLI tools.

**Alternatives considered**:
- argparse: Nativo pero mas verboso para comandos complejos. Click es mas productivo.

### Storage: SQLite

**Decision**: SQLite via sqlite3 (stdlib)

**Rationale**: Base de datos embebida, sin servidor, cero configuracion. Suficiente para 36 registros.
Compartida entre Features 001 y 003 para flujo de datos. Archivo unico facil de respaldar.

**Alternatives considered**:
- PostgreSQL: Sobredimensionado para monousuario local.
- CSV files: Sin capacidad de consulta estructurada, joins, ni integridad referencial.
- JSON files: Sin queries ni transacciones.

### CSV Import/Export: pandas

**Decision**: pandas

**Rationale**: Estandar academico para datos tabulares. Validacion de tipos, manejo de nulos,
compatibilidad con Excel/MATLAB/R. Export directo a CSV sin transformaciones.

**Alternatives considered**:
- csv (stdlib): Suficiente pero sin validacion de tipos ni manejo de errores robusto.
- openpyxl: Solo para Excel, no cubre CSV.

### Unique Constraint: tipologia + zona_termica

**Decision**: Unique constraint compuesto en SQLite

**Rationale**: El spec indica que la combinacion tipologia-zona termica no debe duplicarse.
SQLite soporta UNIQUE(tipologia, zona_termica). Esto evita duplicados a nivel BD sin logica
adicional en la aplicacion.

## Validation Ranges

Basados en valores tipicos para viviendas de interes social en Chile (MINVU 2024):

| Parametro | Rango | Unidad | Fuente |
|-----------|-------|--------|--------|
| U_prom | 0.5 - 5.0 | W/m2K | Transmitancia termica tipica viviendas Chile |
| Demanda anual | 500 - 20000 | kWh/ano | Rango para viviendas 40-80 m2 |
| Peak demanda | 1 - 20 | kW | Potencia nominal equipos residenciales |
| GDC | 200 - 4000 | grados dia base 15C | Zonas 1-9 Chile (norte a sur) |

## Integration Pattern: Shared SQLite DB

Feature 001 escribe datos de simulacion a la DB SQLite compartida.
Feature 003 lee desde la misma DB para la optimizacion MILP.
El esquema define tablas con prefijo consistente: `sim_*` para Feature 001, `hvac_*` para 002, etc.

Formato de archivo DB: `data/acond-termico.db` en la raiz del proyecto.
