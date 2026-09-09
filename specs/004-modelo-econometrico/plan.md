# Implementation Plan: Modelacion Econometrica y Validacion

**Branch**: `004-modelo-econometrico` | **Date**: 2026-07-27 | **Spec**: spec.md

**Input**: Feature specification from `specs/004-modelo-econometrico/spec.md`

## Summary

Modelo de regresion lineal multiple (OLS) que explica el costo total optimizado en funcion
de variables fisicas, de combustible y de atributos tecnologicos. Incluye bloque condicional
de validacion estadistica (8 pruebas de diagnostico) y ruta alternativa de analisis What-if
por escenarios. Interfaces CLI + GUI.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**:
- statsmodels para OLS y tests de diagnostico
- pandas para manipulacion de datos
- numpy para calculos numericos
- scipy.stats para soporte estadistico adicional
- Click para CLI
- Streamlit para GUI

**Storage**: No requiere persistencia interna (lee CSV desde Feature 003)

**Testing**: pytest

**Target Platform**: Linux desktop (local)

**Project Type**: CLI + GUI computational module

**Performance Goals**:
- OLS estimation: < 10s (36 observaciones)
- Tests de diagnostico: < 30s
- Analisis What-if: < 2 min

**Constraints**: Requiere output CSV de Feature 003. 36 observaciones minimas.

**Scale/Scope**: 36 observaciones, ~10 variables independientes, ~8 tests de diagnostico

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Verificacion |
|-----------|-------------|
| I. Desarrollo Modular | Modulo `src/econometric/` independiente. Datos via CSV desde Feature 003 |
| II. Rigurosidad Matematica | Bateria completa de tests de diagnostico (Jarque-Bera, White, Durbin-Watson, Ramsey, VIF, F, t, R2) |
| III. Facilidad de Uso | CLI + GUI con boton "Ejecutar modelo econometrico". Ruta alternativa automatica |
| IV. Alcance Acotado | Solo modelo econometrico y validacion. Sin despliegue ni visualizacion avanzada |
| V. Entorno Academico | Tests estadisticos estandar academicos. Export CSV de coeficientes y resultados |

## Project Structure

### Documentation (this feature)

```text
specs/004-modelo-econometrico/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── econometric/
│   ├── __init__.py
│   ├── model.py         # OLS estimation, specification de variables
│   ├── diagnostics.py   # Bateria de tests de diagnostico
│   ├── whatif.py        # Ruta alternativa: analisis por escenarios
│   ├── validation.py    # Bloque condicional (validacion OK -> propuesto / falla -> whatif)
│   ├── cli.py           # Comandos Click
│   ├── gui.py           # Interfaz Streamlit
│   └── csv_export.py    # Export resultados a CSV
└── shared/
    └── thresholds.py    # Umbrales de validacion

tests/
├── test_model.py
├── test_diagnostics.py
├── test_whatif.py
├── test_validation.py
└── test_cli.py
```

**Structure Decision**: Single project con submodulo `src/econometric/`.
`model.py` define la especificacion OLS. `diagnostics.py` implementa los 8 tests.
`validation.py` orquesta el bloque condicional. `whatif.py` implementa la ruta
alternativa con analisis parametrico, escenarios criticos y sensibilidad multifactorial.

## Complexity Tracking

Sin violaciones constitucionales. La bateria de tests de diagnostico (8 pruebas) es
la complejidad academica requerida para validar el modelo segun metodologia Wooldridge.
