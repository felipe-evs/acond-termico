# Quickstart: Modelo de Optimizacion MILP

## Prerequisites

- Python 3.10+
- `pip install pulp click streamlit pandas`
- Datos cargados en DB compartida desde Features 001 y 002

## Setup

```bash
# Verificar datos disponibles
sqlite3 data/acond-termico.db "SELECT COUNT(*) FROM sim_simulacion;"
# Expected: 36

sqlite3 data/acond-termico.db "SELECT COUNT(*) FROM hvac_equipo;"
# Expected: 70+
```

## Test Scenarios

### Scenario 1: Configurar parametros

```bash
python -m src.optimizer.cli optimize config \
    --tasa-descuento 8 --vida-util 15 --perdida-sistemica 5
```
**Expected**: Parametros guardados en `opt_parametro`.

### Scenario 2: Ejecutar optimizacion

```bash
python -m src.optimizer.cli optimize run
```
**Expected**: `{"status": "completed", "escenarios_resueltos": 36}`
**Tiempo esperado**: < 3 minutos.

### Scenario 3: Ver resultados

```bash
python -m src.optimizer.cli optimize results --zona 5
```
**Expected**: Tabla con tecnologia optima para cada tipologia en zona 5.

### Scenario 4: Exportar resultados

```bash
python -m src.optimizer.cli optimize export ./output/resultados.csv
```
**Expected**: Archivo CSV con 36 filas listo para Feature 004.

### Scenario 5: GUI

```bash
streamlit run src/optimizer/gui.py
```
**Expected**: Boton "Ejecutar optimizacion" + tabla de resultados.

## Verification

```bash
# Verificar resultados en DB
sqlite3 data/acond-termico.db "SELECT COUNT(*) FROM opt_resultado;"
# Expected: 36

sqlite3 data/acond-termico.db "SELECT zona_termica, MIN(costo_anual_equivalente_clp) FROM opt_resultado GROUP BY zona_termica;"
# Expected: costo optimo por zona
```
