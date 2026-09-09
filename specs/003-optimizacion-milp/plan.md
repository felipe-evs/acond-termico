# Implementation Plan: Modelo de Optimizacion MILP

**Branch**: `003-optimizacion-milp` | **Date**: 2026-07-27 | **Spec**: spec.md

**Input**: Feature specification from `specs/003-optimizacion-milp/spec.md`

## Summary

Modelo de Programacion Lineal Entera Mixta (MILP) que minimiza el Costo Anual Equivalente
total para 36 escenarios (4 tipologias x 9 zonas). Lee datos desde DB SQLite compartida
(Features 001 y 002), resuelve con PuLP/CBC en paralelo, exporta resultados a CSV
para Feature 004. Interfaces CLI + GUI.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**:
- PuLP (incluye solver CBC) para modelado MILP
- sqlite3 (stdlib) para lectura de datos
- Click para CLI
- Streamlit para GUI
- pandas para export CSV
- concurrent.futures (stdlib) para ejecucion paralela

**Storage**: SQLite (solo lectura desde sim_* + hvac_*); escritura opt_* en DB compartida

**Testing**: pytest

**Target Platform**: Linux desktop (local)

**Project Type**: CLI + GUI computational module

**Performance Goals**:
- MILP individual: < 30s por escenario
- 36 escenarios en paralelo: < 3 minutos
- Visualizacion resultados: < 2s

**Constraints**: Offline-capable, monousuario, requiere > 2GB RAM para MILP paralelo

**Scale/Scope**: 36 escenarios, 70+ equipos, 6 tecnologias, 12 variables binarias tipicas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Verificacion |
|-----------|-------------|
| I. Desarrollo Modular | Modulo `src/optimizer/` independiente. Interfaz clara con Features 001/002 (lectura SQLite) y 004 (export CSV) |
| II. Rigurosidad Matematica | Modelo MILP con variables binarias, funcion objetivo documentada, restricciones explicitas |
| III. Facilidad de Uso | CLI + GUI con boton "Ejecutar optimizacion". Resultados en tabla por zona |
| IV. Alcance Acotado | Solo optimizacion. Sin modelos predictivos ni analisis posteriores (eso es Feature 004) |
| V. Entorno Academico | Export CSV de resultados. Datos de entrada desde fuentes academicas validadas (DesignBuilder, CNE) |

## Project Structure

### Documentation (this feature)

```text
specs/003-optimizacion-milp/
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
├── optimizer/
│   ├── __init__.py
│   ├── model.py         # Modelo MILP: variables, funcion objetivo, restricciones
│   ├── solver.py        # Orquestacion paralela de 36 escenarios
│   ├── reader.py        # Lectura de datos desde DB compartida (sim_*, hvac_*)
│   ├── cli.py           # Comandos Click
│   ├── gui.py           # Interfaz Streamlit
│   └── csv_export.py    # Export resultados a CSV
├── db/
│   └── schema.py        # Esquema tablas opt_*
└── shared/
    └── config.py        # Parametros globales (tasa descuento, vida util)

tests/
├── test_model.py
├── test_solver.py
├── test_reader.py
└── test_cli.py
```

**Structure Decision**: Single project con submodulo `src/optimizer/`. `src/optimizer/model.py`
contiene la formulacion matematica del MILP. `solver.py` orquesta la ejecucion paralela.
`reader.py` encapsula la lectura desde las tablas compartidas.

## Complexity Tracking

Sin violaciones constitucionales. El modelo MILP con 36 escenarios y 70+ equipos es la
complejidad necesaria para el problema. La ejecucion paralela esta justificada por SC-001.
