# Quickstart: Modelacion Econometrica y Validacion

## Prerequisites

- Python 3.10+
- `pip install statsmodels pandas numpy scipy click streamlit`
- Archivo CSV de resultados desde Feature 003

## Setup

```bash
# Verificar que existe el CSV de entrada
ls -la ./output/resultados_optimizacion.csv
# Expected: archivo con 36 filas
```

## Test Scenarios

### Scenario 1: Ejecutar modelo econometrico

```bash
python -m src.econometric.cli econometric run \
    --input ./output/resultados_optimizacion.csv
```
**Expected (validado)**:
```
Status: MODELO VALIDADO
R2: > 0.8
Tests: 8/8 pasan
```

### Scenario 2: Ver coeficientes

```bash
python -m src.econometric.cli econometric results
```
**Expected**: Tabla con ~10 variables, cada una con beta, t-statistic, p-value, VIF.

### Scenario 3: Ruta alternativa (si modelo no valida)

```bash
python -m src.econometric.cli econometric whatif \
    --tipo critico --parametro "Desabastecimiento gas"
```
**Expected**: Escenario procesado con Y_costo resultante.

### Scenario 4: Exportar resultados

```bash
python -m src.econometric.cli econometric export ./output/modelo_completo.csv
```
**Expected**: Archivo CSV con coeficientes y tests.

### Scenario 5: GUI

```bash
streamlit run src/econometric/gui.py
```
**Expected**: Boton "Ejecutar modelo" + resultados + opcion what-if.

## Verification

```bash
# Verificar modelo guardado en DB
sqlite3 data/acond-termico.db "SELECT COUNT(*) FROM eco_modelo;"
# Expected: 1+ (depende de cuantas veces se ejecuto)

sqlite3 data/acond-termico.db "SELECT R2, resultado_global FROM eco_modelo m JOIN eco_validacion v ON m.id=v.modelo_id;"
# Expected: R2 y resultado de validacion
```
