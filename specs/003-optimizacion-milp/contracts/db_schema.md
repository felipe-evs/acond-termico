# Database Schema Contract: Shared SQLite DB

## Feature 003 Tables (prefijo `opt_`)

### Lectura desde Features 001 y 002

Feature 003 LEE las siguientes tablas (solo lectura):

| Tabla | Feature | Proposito |
|-------|---------|-----------|
| sim_simulacion | 001 | Escenarios: tipologia, zona_termica |
| sim_resultado | 001 | Demandas: U_prom, demanda_anual, peak, GDC |
| hvac_equipo | 002 | Equipos: potencia, rendimiento, costos |
| hvac_combustible | 002 | Combustibles: PCI, PCS, costos |

### Escritura por Feature 003

Feature 003 ESCRIBE en las siguientes tablas:

| Tabla | Proposito |
|-------|-----------|
| opt_parametro | Configuracion global del modelo |
| opt_resultado | Resultados por escenario |
| opt_seleccion | Detalle de seleccion de equipos |

Feature 004 (Modelo Econometrico) leera desde `opt_resultado` para la regresion.
