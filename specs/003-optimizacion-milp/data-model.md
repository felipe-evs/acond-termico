# Data Model: Modelo de Optimizacion MILP

## Entities

### EscenarioOptimizacion (vista virtual desde Feature 001)

No es tabla fisica. Se construye desde `sim_simulacion` + `sim_resultado` (Feature 001).

| Campo | Fuente | Descripcion |
|-------|--------|-------------|
| id | simulacion.id | Escenario unico |
| zona_termica | simulacion.zona_termica | 1-9 |
| tipologia | simulacion.tipologia | Tipo arquitectonico |
| demanda_anual_kwh | resultado.demanda_anual_kwh | Demanda anual |
| peak_demanda_kw | resultado.peak_demanda_kw | Pico de demanda |
| u_prom | resultado.u_prom | Transmitancia termica |
| gdc | resultado.gdc | Grados dia calefaccion |

### ParametroOptimizacion

Configuracion global del modelo economico.

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|---------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Identificador |
| tasa_descuento_pct | REAL | NOT NULL, > 0 | Tasa de descuento (%) |
| vida_util_anos | INTEGER | NOT NULL, > 0 | Vida util de equipos (anos) |
| perdida_sistemica_pct | REAL | NOT NULL, 0-100 | Perdida sistemica (%) |
| fecha_actualizacion | TEXT | DEFAULT CURRENT_TIMESTAMP | Momento de configuracion |

### ResultadoOptimizacion

Resultados del modelo MILP para cada escenario.

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|---------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Identificador |
| escenario_id | INTEGER | NOT NULL | Corresponde a simulacion.id de Feature 001 |
| zona_termica | INTEGER | NOT NULL | Zona termica |
| tipologia | TEXT | NOT NULL | Tipologia arquitectonica |
| costo_anual_equivalente_clp | REAL | NOT NULL | Valor optimo de la funcion objetivo |
| timestamp | TEXT | DEFAULT CURRENT_TIMESTAMP | Momento de ejecucion |

## SQL Schema

```sql
CREATE TABLE opt_parametro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tasa_descuento_pct REAL NOT NULL CHECK (tasa_descuento_pct > 0),
    vida_util_anos INTEGER NOT NULL CHECK (vida_util_anos > 0),
    perdida_sistemica_pct REAL NOT NULL CHECK (perdida_sistemica_pct BETWEEN 0 AND 100),
    fecha_actualizacion TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE opt_resultado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    escenario_id INTEGER NOT NULL,
    zona_termica INTEGER NOT NULL CHECK (zona_termica BETWEEN 1 AND 9),
    tipologia TEXT NOT NULL,
    costo_anual_equivalente_clp REAL NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE opt_seleccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resultado_id INTEGER NOT NULL REFERENCES opt_resultado(id),
    equipo_hvac_id INTEGER NOT NULL,
    tecnologia_nombre TEXT NOT NULL,
    combustible_nombre TEXT NOT NULL,
    capacidad_asignada_kw REAL NOT NULL CHECK (capacidad_asignada_kw > 0),
    es_seleccionado INTEGER NOT NULL CHECK (es_seleccionado IN (0, 1))
);
```

## State Transitions

- **ParametroOptimizacion**: Solo existe un registro activo (configuracion global).
  Se actualiza (UPDATE) cuando el usuario modifica parametros.
- **ResultadoOptimizacion**: Se INSERT al ejecutar la optimizacion.
  Se mantiene historico de ejecuciones (cada ejecucion es append).
- **opt_seleccion**: Detalle de la solucion. Se INSERT junto con el resultado.
