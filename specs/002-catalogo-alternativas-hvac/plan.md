# Implementation Plan: Catalogo de Alternativas de Climatizacion

**Branch**: `002-catalogo-alternativas-hvac` | **Date**: 2026-07-27 | **Spec**: spec.md

**Input**: Feature specification from `specs/002-catalogo-alternativas-hvac/spec.md`

## Summary

Base de datos estandarizada de alternativas de climatizacion del mercado chileno:
CRUD de combustibles (6 tipos) con precios regionales historicos, CRUD de equipos
HVAC (70+ modelos en 6 tecnologias), y calculo automatico de la Matriz de Eleccion
Discreta con costos normalizados. Interfaces CLI + GUI + CSV Import.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**:
- sqlite3 (stdlib) para persistencia
- Click para CLI
- Streamlit para GUI
- pandas para import/export CSV
- requests + beautifulsoup4 para web scraping CNE (opcional)
- lxml para parsing HTML de CNE

**Storage**: SQLite (base de datos compartida con Feature 003)

**Testing**: pytest

**Target Platform**: Linux desktop (local)

**Project Type**: CLI + GUI desktop app

**Performance Goals**:
- CRUD individual < 1s
- CSV import (70 equipos) < 10s
- Matriz de Eleccion Discreta < 5s recalculo
- CNE web scraping < 30s

**Constraints**: Offline-capable (con datos cargados), monousuario, sin autenticacion

**Scale/Scope**: 6 combustibles, 70+ equipos, 12 regiones, precios historicos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Verificacion |
|-----------|-------------|
| I. Desarrollo Modular | Feature implementada como modulo independiente `src/hvac/` con contrato via SQLite hacia 003 |
| II. Rigurosidad Matematica | Normalizacion de unidades a Gcal y CLP; validacion de rendimientos y rangos |
| III. Facilidad de Uso | Tres modalidades de entrada: GUI, CLI, CSV Import masivo. Export CSV para el investigador |
| IV. Alcance Acotado | Solo catalogo de datos comerciales. Sin modelos de optimizacion ni calculos complejos |
| V. Entorno Academico | Datos exportables a CSV, compatibles con herramientas academicas. Fuentes CNE oficiales |

## Project Structure

### Documentation (this feature)

```text
specs/002-catalogo-alternativas-hvac/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── hvac/
│   ├── __init__.py
│   ├── models.py        # Combustible, PrecioCombustible, TipoTecnologia, EquipoHVAC
│   ├── repository.py    # CRUD contra SQLite
│   ├── cli.py           # Comandos Click
│   ├── gui.py           # Interfaz Streamlit
│   ├── csv_handler.py   # Import/Export CSV
│   ├── matrix.py        # Calculo de Matriz de Eleccion Discreta
│   └── cne_fetcher.py   # Obtencion de precios CNE (API/scraping/CSV)
├── db/
│   └── schema.py        # Esquema SQLite compartido (tablas hvac_*)
└── shared/
    └── validators.py    # Validaciones transversales

tests/
├── test_models.py
├── test_repository.py
├── test_cli.py
├── test_csv_handler.py
├── test_matrix.py
└── test_cne_fetcher.py
```

**Structure Decision**: Single project con submodulo `src/hvac/` para toda la funcionalidad
de Fase 2. `src/db/schema.py` contiene las tablas `hvac_*` en la DB compartida.
`src/hvac/cne_fetcher.py` encapsula la logica multi-estrategia de obtencion de precios CNE.

## Complexity Tracking

Sin violaciones constitucionales. La estrategia hibrida de CNE esta justificada por
la naturaleza del problema (fuentes variables). El resto del diseno es CRUD estandar.
