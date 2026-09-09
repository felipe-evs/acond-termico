# CLI Contract: Modelo de Optimizacion MILP

## Command: `optimize run`

Ejecuta la optimizacion para los 36 escenarios.

```bash
optimize run
```

**Output**: `{"status": "completed", "escenarios_resueltos": 36, "tiempo_total_seg": 120.5, "output_csv": "..."}`

**Output (infactible)**: `{"status": "infeasible", "escenario_id": 5, "razon": "restriccion peak demanda no satisface"}`

## Command: `optimize config`

Muestra o actualiza los parametros economicos.

```bash
optimize config --tasa-descuento 8 --vida-util 15 --perdida-sistemica 5
```

**Output**: `{"tasa_descuento_pct": 8, "vida_util_anos": 15, "perdida_sistemica_pct": 5}`

## Command: `optimize results`

Muestra los resultados de la ultima ejecucion.

```bash
optimize results --zona 5
```

**Output**: Tabla con zona, tipologia, tecnologia, combustible, capacidad, costo anual equivalente.

Opciones: `--zona N` para filtrar, `--format json` para output JSON.

## Command: `optimize export`

Exporta resultados a CSV.

```bash
optimize export ./output/resultados_optimizacion.csv
```

**Output**: Archivo CSV con todos los resultados por escenario.
