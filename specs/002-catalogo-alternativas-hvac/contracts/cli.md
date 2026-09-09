# CLI Contract: Catalogo de Alternativas de Climatizacion

## Command: `hvac combustible create`

```bash
hvac combustible create \
    --nombre parafina \
    --unidad litro \
    --pci 8200 \
    --pcs 8800 \
    --rendimiento 85 \
    --unidades-por-gcal 0.12
```
**Output**: `{"id": 1, "nombre": "parafina", ...}`

## Command: `hvac combustible list`

```bash
hvac combustible list
```
**Output**: Tabla con todos los combustibles registrados.

## Command: `hvac precio add`

```bash
hvac precio add \
    --combustible-id 1 \
    --region 13 \
    --precio 1200 \
    --fecha-vigencia 2026-07-01 \
    --fuente MANUAL
```
**Output**: `{"id": 1, "combustible_id": 1, "region": 13, ...}`

## Command: `hvac precio list`

```bash
hvac precio list --combustible-id 1 --region 13
```
**Output**: Tabla historica de precios para ese combustible y region.

## Command: `hvac equipo create`

```bash
hvac equipo create \
    --tipo-tecnologia split_inverter \
    --combustible electricidad \
    --modelo "Midea Xtreme 12000" \
    --potencia 3.5 \
    --rendimiento 320 \
    --costo-adquisicion 450000 \
    --tasa-consumo 1.2 \
    --unidad-tasa kWh/h \
    --fuente-datos "Sodimac"
```
**Output**: `{"id": 1, "modelo": "Midea Xtreme 12000", ...}`

## Command: `hvac equipo list`

```bash
hvac equipo list --tipo split_inverter
```
**Output**: Tabla filtrada por tipo de tecnologia.

## Command: `hvac equipo import`

```bash
hvac equipo import ./datos/equipos.csv
```
**Output**: `{"imported": 70, "errors": 0, "failed_rows": []}`

## Command: `hvac matrix show`

```bash
hvac matrix show --output csv
```
**Output**: Matriz de Eleccion Discreta completa con costos normalizados.
