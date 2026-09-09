# Quickstart: Catalogo de Alternativas de Climatizacion

## Prerequisites

- Python 3.10+
- `pip install click streamlit pandas requests beautifulsoup4`

## Setup

```bash
# Inicializar catalogo de combustibles base
python -m src.hvac.cli hvac combustible create --nombre parafina --unidad litro --pci 8200 --pcs 8800 --rendimiento 85 --unidades-por-gcal 0.12
python -m src.hvac.cli hvac combustible create --nombre electricidad --unidad kWh --pci 1 --pcs 1 --rendimiento 100 --unidades-por-gcal 1163
```

## Test Scenarios

### Scenario 1: Agregar precio manual

```bash
python -m src.hvac.cli hvac precio add \
    --combustible-id 1 --region 13 --precio 1200 \
    --fecha-vigencia 2026-07-01 --fuente MANUAL
```
**Expected**: Precio registrado con trazabilidad.

### Scenario 2: Cargar equipos via CSV

```bash
python -m src.hvac.cli hvac equipo import tests/fixtures/equipos_muestra.csv
```
**Expected**: `{"imported": 70, "errors": 0}`

### Scenario 3: Ver matriz de eleccion discreta

```bash
python -m src.hvac.cli hvac matrix show
```
**Expected**: Tabla con equipos, costos fijos anualizados y costos variables por Gcal.

### Scenario 4: Verificar contador por tecnologia

```bash
python -m src.hvac.cli hvac equipo list --tipo split_inverter
```
**Expected**: Al menos 10 equipos listados.

### Scenario 5: GUI

```bash
streamlit run src/hvac/gui.py
```
**Expected**: Navegador abre formularios CRUD para combustibles, precios y equipos.

## Verification

```bash
# Verificar datos en DB compartida
sqlite3 data/acond-termico.db "SELECT COUNT(*) FROM hvac_equipo;"
# Expected: 70+

sqlite3 data/acond-termico.db "SELECT tipo_tecnologia_id, COUNT(*) FROM hvac_equipo GROUP BY tipo_tecnologia_id;"
# Expected: Cada tecnologia con >= 10 equipos
```
