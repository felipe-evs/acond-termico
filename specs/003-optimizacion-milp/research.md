# Research: Modelo de Optimizacion MILP

## Solver Decision: CBC via PuLP

**Decision**: PuLP con solver CBC (incluido).

**Rationale**: PuLP es la libreria estandar de modelado MILP en Python. CBC es un solver
de codigo abierto maduro, sin licencias, incluido en la instalacion de PuLP. No requiere
instalacion externa ni configuracion.

**Alternatives considered**:
- Pyomo + GLPK: Pyomo es mas verbose, GLPK menos eficiente que CBC para problemas grandes.
- OR-Tools: Potente pero menos documentado para MILP clasico.
- SciPy optimize: No soporta variables enteras/binarias.

## MILP Formulation

### Sets
- E = {equipos HVAC disponibles} (70+)
- Z = {zonas termicas} (9)

### Parameters (por escenario: tipologia z + zona z)
- D_anual_z = demanda anual (kWh/ano) — desde Feature 001
- Peak_z = pico de demanda (kW) — desde Feature 001
- CF_e = costo fijo anualizado del equipo e (CLP/ano) — desde Feature 002
- CV_e = costo variable del equipo e (CLP/kWh util) — desde Feature 002
- P_s = perdida sistemica (%)

### Decision Variables
- x_e = 1 si el equipo e es seleccionado, 0 si no (binaria)

### Objective Function
```
Min Z = SUM_e (CF_e * x_e) + SUM_e (CV_e * D_anual_z * x_e / (1 - P_s))
```

### Constraints
1. Pico de demanda: SUM_e (Capacidad_e * x_e) >= Peak_z
2. Energia anual: SUM_e (Capacidad_e * 8760 * x_e) >= D_anual_z
3. Seleccion unica: SUM_e x_e <= N_max (opcional, limitar cantidad de equipos)

## Parallel Execution

**Decision**: `concurrent.futures.ProcessPoolExecutor` con max_workers = CPU count.

**Rationale**: Los 36 escenarios son independientes (sin restricciones entre zonas).
Cada escenario se resuelve en su propio proceso, evitando GIL de Python.

**Riesgo**: Uso de memoria. 36 procesos simultaneos pueden consumir mucha RAM.
Mitigacion: `max_workers = min(36, os.cpu_count())` y timeout por escenario.

## Data Flow

1. `reader.py` consulta tablas `sim_simulacion` + `sim_resultado` (Feature 001) y
   `hvac_equipo` + `hvac_combustible` (Feature 002) desde la DB SQLite compartida
2. `model.py` construye el MILP para cada escenario
3. `solver.py` ejecuta en paralelo
4. Resultados se escriben en tabla `opt_resultado`
5. `csv_export.py` exporta resultados a CSV para Feature 004
