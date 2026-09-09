# Database Schema Contract: Shared SQLite DB

## Feature 002 Tables (prefijo `hvac_`)

Misma base de datos SQLite compartida (`data/acond-termico.db`).

### Tablas:

| Tabla | Proposito | Escritura | Lectura |
|-------|-----------|-----------|---------|
| hvac_combustible | Catalogo de combustibles | 002 | 002, 003 |
| hvac_precio_combustible | Precios historicos por region | 002 | 002, 003 |
| hvac_tipo_tecnologia | Tipos de tecnologia HVAC | 002 (seed) | 002, 003 |
| hvac_equipo | Equipos HVAC del mercado | 002 | 002, 003 |

Feature 003 (Optimizacion MILP) se compromete a:
- Leer desde `hvac_equipo` y `hvac_combustible` para parametros de optimizacion
- NO escribir ni modificar tablas `hvac_*`
