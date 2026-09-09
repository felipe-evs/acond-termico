---

description: "Task list for Modelo de Optimizacion MILP"

---

# Tasks: Modelo de Optimizacion MILP

**Input**: Design documents from `specs/003-optimizacion-milp/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are included for core logic (MILP model, solver).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend project structure for optimizer module

- [x] T001 Create `src/optimizer/` directory structure with `src/optimizer/__init__.py`
- [x] T002 [P] Add optimize dependencies to `requirements.txt`: pulp
- [x] T003 Create `src/shared/config.py` with global optimizer config defaults (tasa descuento 8%, vida util 15 anos, perdida sistemica 5%)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create optimizer DB tables in `src/db/schema.py`: opt_parametro, opt_resultado, opt_seleccion
- [x] T005 Implement data reader from shared DB in `src/optimizer/reader.py` (reads sim_* + hvac_* tables)
- [x] T006 [P] Create unit test for reader in `tests/test_reader.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ejecutar Optimizacion MILP (Priority: P1) MVP

**Goal**: El sistema ejecuta el modelo MILP que selecciona las tecnologias optimas para cada escenario

**Independent Test**: Ejecutar optimizacion y verificar que retorna solucion factible con asignaciones discretas

### Implementation for User Story 1

- [x] T007 [P] [US1] Create ParametroOptimizacion model in `src/optimizer/model.py`
- [x] T008 [P] [US1] Create EscenarioOptimizacion (virtual, desde reader) in `src/optimizer/model.py`
- [x] T009 [P] [US1] Create ResultadoOptimizacion model in `src/optimizer/model.py`
- [x] T010 [US1] Implement MILP model formulation in `src/optimizer/model.py` (variables binarias, funcion objetivo, restricciones)
- [x] T011 [US1] Implement single-scenario solver function in `src/optimizer/solver.py`
- [x] T012 [US1] Implement parallel execution with concurrent.futures in `src/optimizer/solver.py`
- [x] T013 [US1] Implement ResultadoOptimizacionRepository (write to opt_resultado) in `src/optimizer/solver.py`
- [x] T014 [US1] Implement CLI command `optimize run` in `src/optimizer/cli.py`
- [x] T015 [P] [US1] Create unit tests for MILP model in `tests/test_model.py`
- [x] T016 [P] [US1] Create unit tests for solver in `tests/test_solver.py`

**Checkpoint**: Optimizacion MILP funcional via CLI. 36 escenarios resueltos en < 3 min.

---

## Phase 4: User Story 2 - Configurar Parametros de Optimizacion (Priority: P2)

**Goal**: El usuario puede configurar los parametros economicos del modelo

**Independent Test**: Modificar tasa descuento y verificar que el resultado cambia consistentemente

### Implementation for User Story 2

- [x] T017 [US2] Implement ParametroOptimizacionRepository (CRUD) in `src/optimizer/solver.py`
- [x] T018 [P] [US2] Implement CLI command `optimize config` in `src/optimizer/cli.py`
- [x] T019 [US2] Add config section to GUI in `src/optimizer/gui.py`
- [x] T020 [P] [US2] Add config validation (tasa > 0, vida util > 0, perdida 0-100) in `src/shared/config.py`
- [x] T021 [US2] Wire config into solver so it uses current params on each run in `src/optimizer/solver.py`

**Checkpoint**: Parametros configurables y aplicados en la optimizacion.

---

## Phase 5: User Story 3 - Visualizar Resultados de Optimizacion (Priority: P3)

**Goal**: El usuario puede ver y exportar los resultados de la optimizacion

**Independent Test**: Verificar que los resultados se muestran agrupados por zona con tecnologia seleccionada

### Implementation for User Story 3

- [x] T022 [P] [US3] Implement ResultadoOptimizacionRepository.list() with filters (zona, tipologia) in `src/optimizer/solver.py`
- [x] T023 [P] [US3] Implement CLI command `optimize results` in `src/optimizer/cli.py`
- [x] T024 [P] [US3] Implement CLI command `optimize export` in `src/optimizer/cli.py`
- [x] T025 [US3] Implement CSV export in `src/optimizer/csv_export.py`
- [x] T026 [US3] Add results table view to GUI in `src/optimizer/gui.py`
- [x] T027 [US3] Add export button to GUI in `src/optimizer/gui.py`
- [x] T028 [P] [US3] Create integration tests for CLI commands in `tests/test_cli.py`

**Checkpoint**: Resultados visibles y exportables a CSV para Feature 004.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T029 [P] Add timeout handling for solver (default: 60s por escenario) in `src/optimizer/solver.py`
- [x] T030 [P] Add infeasibility detection and reporting in `src/optimizer/solver.py`
- [x] T031 [P] Add logging for solver progress in `src/optimizer/solver.py`
- [x] T032 [P] Add memory limit warning for parallel execution in `src/optimizer/solver.py`
- [x] T033 Run quickstart.md validation scenarios and verify all outputs
- [x] T034 Verify CSV output contract: Feature 004 puede leer el archivo generado

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - BLOCKS US3
- **User Story 2 (Phase 4)**: Can run in parallel with US1 - no depende de la ejecucion MILP
- **User Story 3 (Phase 5)**: Depends on US1 - necesita resultados para mostrar
- **Polish (Phase 6)**: Depends on all user stories

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Independent of US1 - puede implementarse en paralelo
- **User Story 3 (P3)**: Depends on US1 completado - sin resultados no hay visualizacion

### Within Each User Story

- Models before services
- Services before CLI
- CLI before GUI
- Story complete before moving to next priority

### Parallel Opportunities

- US1 (MILP model) and US2 (config) can be built in parallel
- Different CLI commands for different stories are independent [P]

---

## Parallel Example: User Story 1

```bash
# Launch all models together:
Task: "Create ParametroOptimizacion model in src/optimizer/model.py"
Task: "Create EscenarioOptimizacion model in src/optimizer/model.py"  
Task: "Create ResultadoOptimizacion model in src/optimizer/model.py"

# Then sequentially:
Task: "Implement MILP model formulation (depends on models)"
Task: "Implement single-scenario solver (depends on model)"
Task: "Implement parallel execution (depends on single solver)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (MILP solver + CLI)
4. **STOP and VALIDATE**: Test optimizacion de 36 escenarios
5. Verificar CSV output para Feature 004

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test MILP solver -> Demo (MVP!)
3. Add User Story 2 -> Test configuracion parametros -> Demo
4. Add User Story 3 -> Test visualizacion/export -> Demo
5. Polish -> Timeouts, logging, integracion
