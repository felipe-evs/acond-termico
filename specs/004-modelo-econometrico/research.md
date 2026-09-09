# Research: Modelacion Econometrica y Validacion

## OLS Implementation: statsmodels

**Decision**: statsmodels para OLS y todos los tests de diagnostico.

**Rationale**: statsmodels es la libreria estandar para econometria en Python. Incluye
OLS, Jarque-Bera, White, Durbin-Watson, VIF, F-test, t-test, R2 y ECM integrados.
Ramsey RESET requiere implementacion manual (es funcion de `statsmodels.stats.diagnostic`.

**Alternatives considered**:
- scikit-learn: No provee inferencia estadistica (p-values, tests).
- PyMC: Bayesian, sobredimensionado para OLS clasico.

## Variable Specification

Basado en la clarificacion Q3 (dejar para diseno), las variables se definen ahora:

### Variable Dependiente
- **Y_costo**: Costo Anual Equivalente total optimizado (CLP/ano) desde Feature 003.

### Variables Independientes

**X_fisica** (constructivas y climaticas):
- U_prom (W/m2K) — transmitancia termica promedio
- GDC (grados dia) — perfil climatico
- Demanda_anual_kwh (kWh/ano) — demanda termica total
- Peak_demanda_kw (kW) — pico de demanda

**X_fuel** (precios y rendimientos):
- Precio_combustible_seleccionado (CLP/unidad) — precio del combustible optimo
- PCI_combustible_seleccionado (kcal/kg) — poder calorifico del combustible optimo
- Rendimiento_combustible_pct (%) — rendimiento de transformacion

**X_atrib** (atributos de equipos):
- Potencia_nominal_kw (kW) — capacidad del equipo seleccionado
- Rendimiento_termico_pct (%) — eficiencia del equipo
- Costo_adquisicion_clp (CLP) — costo inicial del equipo

**Variables de control**:
- Zona_termica (factor, 1-9) — efecto fijo por zona
- Tipologia (factor, 4 niveles) — efecto fijo por tipo arquitectonico

## Conditional Validation Block

```
if (todos_los_tests_pasan):
    consolidar como Modelo Propuesto
    exportar resultados R2, coeficientes, tests
else:
    ejecutar ruta alternativa What-if
        - Analisis parametrico (variar 1 parametro)
        - Escenarios criticos (desabastecimiento +50%, alza +100%)
        - Sensibilidad multifactorial
    exportar resultados de escenarios
```

## Thresholds

| Test | Estadistico | Criterio |
|------|-------------|----------|
| Jarque-Bera | JB | p-value > 0.05 (normalidad) |
| White | LM | p-value > 0.05 (homocedasticidad) |
| Durbin-Watson | DW | 1.5 < DW < 2.5 (no autocorrelacion) |
| Ramsey RESET | F | p-value > 0.05 (especificacion correcta) |
| VIF | VIF | VIF < 10 para cada variable |
| F-test | F | p-value < 0.05 (significancia global) |
| t-test | t | p-value < 0.05 (significancia individual) |
