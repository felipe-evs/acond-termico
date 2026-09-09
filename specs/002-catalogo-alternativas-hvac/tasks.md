---

description: "Task list for Catalogo de Alternativas de Climatizacion"

---

# Tasks: Catalogo de Alternativas de Climatizacion

**Input**: Design documents from `specs/002-catalogo-alternativas-hvac/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are included for core logic (matrix calculation, CNE fetching).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend project structure for HVAC module

- [x] T001 Create `src/hvac/` directory structure with `src/hvac/__init__.py`
- [x] T002 [P] Add hvac dependencies to `requirements.txt`: requests, beautifulsoup4, lxml
- [x] T003 [P] Create seed data fixtures in `src/hvac/seed.py` (6 combustibles, 6 tipos tecnologia)
- [x] T004 [P] Create `src/hvac/constants.py` with region list (1-16), fuente list, tipos de combustible

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create HVAC schema tables in `src/db/schema.py`: hvac_combustible, hvac_precio_combustible, hvac_tipo_tecnologia, hvac_equipo
- [x] T006 [P] Create sequence combobox registration (enables dropdown re-use across CLI/GUI)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Gestionar Combustibles (Priority: P1) MVP

**Goal**: El usuario puede administrar combustibles con sus parametros fisicos y precios regionales historicos

**Independent Test**: Crear un combustible, agregar un precio por region, verificar en listado

### Implementation for User Story 1

- [x] T007 [P] [US1] Create Combustible model in `src/hvac/models.py`
- [x] T008 [P] [US1] Create PrecioCombustible model in `src/hvac/models.py`
- [x] T009 [P] [US1] Create TipoTecnologia model in `src/hvac/models.py`
- [x] T010 [US1] Implement CombustibleRepository (CRUD + seed) in `src/hvac/repository.py`
- [x] T011 [P] [US1] Implement PrecioCombustibleRepository (append-only historico) in `src/hvac/repository.py`
- [x] T012 [US1] Implement CLI command `hvac combustible create` in `src/hvac/cli.py`
- [x] T013 [P] [US1] Implement CLI command `hvac combustible list` in `src/hvac/cli.py`
- [x] T014 [US1] Implement CLI command `hvac precio add` in `src/hvac/cli.py`
- [x] T015 [P] [US1] Implement CLI command `hvac precio list` in `src/hvac/cli.py`
- [x] T016 [US1] Implement GUI form for combustible CRUD in `src/hvac/gui.py`
- [x] T017 [US1] Implement GUI form for precio management in `src/hvac/gui.py`
- [x] T018 [US1] Implement CNE multi-estrategia fetcher in `src/hvac/cne_fetcher.py`
- [x] T019 [US1] Implement CLI command `hvac precio fetch-cne` in `src/hvac/cli.py`
- [x] T020 [US1] Implement CSV import for precios in `src/hvac/csv_handler.py`
- [x] T021 [US1] Run seed data (6 combustibles) via `src/hvac/seed.py`

**Checkpoint**: Combustibles y precios funcionales via CLI y GUI. Datos en DB compartida.

---

## Phase 4: User Story 2 - Gestionar Equipos HVAC (Priority: P1)

**Goal**: El usuario puede registrar equipos HVAC con validacion de fuentes oficiales

**Independent Test**: Registrar 3 equipos de distintos tipos via CLI y verificar en listado

### Implementation for User Story 2

- [x] T022 [P] [US2] Create EquipoHVAC model in `src/hvac/models.py`
- [x] T023 [US2] Implement EquipoHVACRepository (CRUD + contador por tecnologia) in `src/hvac/repository.py`
- [x] T024 [P] [US2] Implement fuente validation logic in `src/shared/validators.py`
- [x] T025 [US2] Implement CLI command `hvac equipo create` in `src/hvac/cli.py`
- [x] T026 [P] [US2] Implement CLI command `hvac equipo list` in `src/hvac/cli.py`
- [x] T027 [P] [US2] Implement CLI command `hvac equipo update` in `src/hvac/cli.py`
- [x] T028 [P] [US2] Implement CLI command `hvac equipo delete` in `src/hvac/cli.py`
- [x] T029 [US2] Implement GUI form for equipo CRUD in `src/hvac/gui.py`
- [x] T030 [US2] Implement CSV import for equipos in `src/hvac/csv_handler.py`
- [x] T031 [P] [US2] Implement CLI command `hvac equipo import` in `src/hvac/cli.py`

**Checkpoint**: Equipos HVAC registrados via CLI, GUI y CSV. Contador por tecnologia visible.

---

## Phase 5: User Story 3 - Visualizar Matriz de Eleccion Discreta (Priority: P2)

**Goal**: El sistema calcula y muestra la matriz con costos normalizados

**Independent Test**: Registrar equipos con distintos combustibles y verificar que la matriz calcula costos por Gcal

### Implementation for User Story 3

- [x] T032 [US3] Implement matrix calculation logic in `src/hvac/matrix.py` (formulas normalizacion)
- [x] T033 [P] [US3] Implement CLI command `hvac matrix show` in `src/hvac/cli.py`
- [x] T034 [US3] Add matrix view tab to GUI in `src/hvac/gui.py`
- [x] T035 [US3] Add auto-recalculation trigger on equipo/combustible changes in `src/hvac/matrix.py`
- [x] T036 [US3] Implement CLI command `hvac equipo export` in `src/hvac/cli.py`
- [x] T037 [US3] Add export button to GUI list view in `src/hvac/gui.py`

**Checkpoint**: Matriz de Eleccion Discreta calculada y visible. Datos exportables a CSV.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T038 [P] Add error handling for CNE fetch failures (timeout, parse error) in `src/hvac/cne_fetcher.py`
- [x] T039 [P] Add logging configuration for hvac module in `src/hvac/__init__.py`
- [x] T040 [P] Write unit tests for matrix calculation in `tests/test_matrix.py`
- [x] T041 [P] Write unit tests for CNE fetcher in `tests/test_cne_fetcher.py`
- [x] T042 [P] Write unit tests for repository in `tests/test_repository.py`
- [x] T043 [P] Write integration tests for CLI commands in `tests/test_cli.py`
- [x] T044 [P] Write integration tests for CSV import/export in `tests/test_csv_handler.py`
- [x] T045 Run quickstart.md validation scenarios and verify all outputs
- [x] T046 [P] Verify SQLite shared DB integration: data accessible from Feature 003 perspective

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - combustibles base for equipos
- **User Story 2 (Phase 4)**: Depends on US1 combustibles existir (FK)
- **User Story 3 (Phase 5)**: Depends on US1 + US2 - necesita datos para calcular matriz
- **Polish (Phase 6)**: Depends on all user stories

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (combustibles FK) - puede empezar cuando US1 tenga seed data
- **User Story 3 (P2)**: Depends on US1 + US2 completos

### Within Each User Story

- Models before services
- Services before CLI
- CLI before GUI
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- US1 precio + combustible CLI commands are independent [P]

---

## Parallel Example: User Story 1

```bash
# Launch all models together:
Task: "Create Combustible model in src/hvac/models.py"
Task: "Create PrecioCombustible model in src/hvac/models.py"
Task: "Create TipoTecnologia model in src/hvac/models.py"

# Then sequentially:
Task: "Implement CombustibleRepository (depends on models)"
Task: "Implement PrecioCombustibleRepository (depends on models)"
Task: "Implement CLI commands (depends on repositories)"
Task: "Implement GUI (depends on repositories)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (combustibles + precios + CNE + CSV import)
4. **STOP and VALIDATE**: Test creacion de combustibles y precios
5. Verificar que datos estan en DB compartida para Feature 003

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test combustibles/precios -> Demo (MVP!)
3. Add User Story 2 -> Test equipos HVAC -> Demo
4. Add User Story 3 -> Test matriz eleccion discreta -> Demo
5. Polish -> Tests y documentacion
