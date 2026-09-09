# CLI Contract: Modelacion Econometrica y Validacion

## Command: `econometric run`

Estima el modelo OLS, ejecuta tests de diagnostico y aplica bloque condicional.

```bash
econometric run --input ./output/resultados_optimizacion.csv
```

**Output** (validado):
```
Status: MODELO VALIDADO
Formula: Y_costo = 125000 + 2.3*U_prom + 45*GDC + 0.8*Demanda + ...
R2: 0.89 | R2 ajustado: 0.85 | ECM: 12500
Tests: 8/8 pasan
```

**Output** (no validado):
```
Status: MODELO NO VALIDADO
Razon: Test White falla (p=0.01)
Activando ruta alternativa: Analisis What-if...
```

## Command: `econometric results`

Muestra los resultados de la ultima estimacion.

```bash
econometric results
```

**Output**: Tabla de coeficientes con beta, error std, t, p-value, VIF.

## Command: `econometric whatif`

Ejecuta analisis por escenarios (si el modelo no fue validado).

```bash
econometric whatif --tipo parametrico --parametro "Precio gas" --variacion 0.5
```

**Output**: `{"parametro": "Precio gas", "variacion": 0.5, "Y_costo_resultante": 325000}`

## Command: `econometric export`

Exporta resultados a CSV.

```bash
econometric export ./output/modelo_econometrico.csv
```

**Output**: Archivo CSV con coeficientes y tests.
