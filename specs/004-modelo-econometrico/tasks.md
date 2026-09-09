---

description: "Task list for Modelacion Econometrica y Validacion"

---

# Tasks: Modelacion Econometrica y Validacion

**Input**: Design documents from `specs/004-modelo-econometrico/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are included for core logic (OLS estimation, diagnostics, what-if).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend project structure for econometric module

- [x] T001 Create `src/econometric/` directory structure with `src/econometric/__init__.py`
- [x] T002 [P] Add econometric dependencies to `requirements.txt`: statsmodels, scipy
- [x] T003 Create `src/shared/thresholds.py` with validation thresholds (JB_p=0.05, White_p=0.05, DW_min=1.5, DW_max=2.5, RESET_p=0.05, VIF_max=10, F_p=0.05, t_p=0.05)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create econometric DB tables in `src/db/schema.py`: eco_modelo, eco_coeficiente, eco_test_diagnostico, eco_escenario_whatif, eco_validacion
- [x] T005 Implement CSV reader from Feature 003 in `src/econometric/model.py` (import resultados_optimizacion.csv)
- [x] T006 [P] Create unit test for CSV reader in `tests/test_model.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Estimar Modelo de Regresion (Priority: P1) MVP

**Goal**: El sistema estima un modelo OLS con Y_costo como variable dependiente

**Independent Test**: Ejecutar la regresion con 36 observaciones y verificar que se generan coeficientes beta

### Implementation for User Story 1

- [x] T007 [P] [US1] Create ModeloEconometrico model in `src/econometric/model.py`
- [x] T008 [P] [US1] Create CoeficienteRegresion model in `src/econometric/model.py`
- [x] T009 [US1] Implement data preparation (X_fisica, X_fuel, X_atrib) from CSV + DB enrichment in `src/econometric/model.py`
- [x] T010 [US1] Implement OLS estimation with statsmodels in `src/econometric/model.py`
- [x] T011 [US1] Implement ModeloEconometricoRepository (write to eco_modelo, eco_coeficiente) in `src/econometric/model.py`
- [x] T012 [US1] Implement CLI command `econometric run` in `src/econometric/cli.py`
- [x] T013 [P] [US1] Create unit tests for OLS estimation in `tests/test_model.py`

**Checkpoint**: Modelo OLS funcional via CLI. Coeficientes y estadisticos basicos disponibles.

---

## Phase 4: User Story 2 - Validacion Estadistica del Modelo (Priority: P1)

**Goal**: El sistema ejecuta la bateria completa de tests de diagnostico

**Independent Test**: Ejecutar los 8 tests y verificar que cada uno produce p-value y decision

### Implementation for User Story 2

- [x] T014 [P] [US2] Create TestDiagnostico model in `src/econometric/model.py`
- [x] T015 [P] [US2] Create ValidacionModelo model in `src/econometric/model.py`
- [x] T016 [US2] Implement Jarque-Bera test in `src/econometric/diagnostics.py`
- [x] T017 [P] [US2] Implement White test in `src/econometric/diagnostics.py`
- [x] T018 [P] [US2] Implement Durbin-Watson test in `src/econometric/diagnostics.py`
- [x] T019 [P] [US2] Implement Ramsey RESET test in `src/econometric/diagnostics.py`
- [x] T020 [P] [US2] Implement VIF calculation in `src/econometric/diagnostics.py`
- [x] T021 [P] [US2] Implement F-test and t-test extraction in `src/econometric/diagnostics.py`
- [x] T022 [P] [US2] Implement R2, R2 ajustado and ECM calculation in `src/econometric/diagnostics.py`
- [x] T023 [US2] Implement conditional validation block in `src/econometric/validation.py`
- [x] T024 [P] [US2] Create unit tests for diagnostics in `tests/test_diagnostics.py`
- [x] T025 [P] [US2] Create unit tests for validation block in `tests/test_validation.py`

**Checkpoint**: Bateria completa de tests y bloque condicional funcional.

---

## Phase 5: User Story 3 - Analisis por Escenarios (Ruta Alternativa) (Priority: P2)

**Goal**: Si el modelo no valida, el sistema ejecuta analisis What-if

**Independent Test**: Forzar validacion fallida y verificar que la ruta alternativa se activa

### Implementation for User Story 3

- [x] T026 [P] [US3] Create EscenarioWhatIf model in `src/econometric/model.py`
- [x] T027 [US3] Implement parametric analysis (variar 1 parametro) in `src/econometric/whatif.py`
- [x] T028 [US3] Implement critical scenario builder (desabastecimiento +50%, alza tarifaria +100%) in `src/econometric/whatif.py`
- [x] T029 [US3] Implement multi-factorial sensitivity analysis in `src/econometric/whatif.py`
- [x] T030 [P] [US3] Create unit tests for what-if analysis in `tests/test_whatif.py`

**Checkpoint**: Ruta alternativa completa con 3 tipos de escenarios.

---

## Phase 6: Integration & GUI

**Purpose**: Unir todo en interfaces CLI/GUI funcionales

- [x] T031 [P] Wire CLI command `econometric run` (estima + valida + decide ruta) in `src/econometric/cli.py`
- [x] T032 [P] Implement CLI command `econometric results` (coeficientes + tests) in `src/econometric/cli.py`
- [x] T033 [P] Implement CLI command `econometric whatif` in `src/econometric/cli.py`
- [x] T034 [P] Implement CLI command `econometric export` in `src/econometric/cli.py`
- [x] T035 Implement CSV export in `src/econometric/csv_export.py`
- [x] T036 Add main GUI with "Ejecutar modelo" button in `src/econometric/gui.py`
- [x] T037 Add results view (coeficientes + tests) to GUI in `src/econometric/gui.py`
- [x] T038 Add what-if panel to GUI in `src/econometric/gui.py`
- [x] T039 [P] Create integration tests for CLI commands in `tests/test_cli.py`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T040 [P] Add partial data handling (menos de 36 observaciones) in `src/econometric/model.py`
- [x] T041 [P] Add perfect multicollinearity detection in `src/econometric/diagnostics.py`
- [x] T042 [P] Add logging for estimation and validation steps in `src/econometric/__init__.py`
- [x] T043 [P] Add error handling for non-invertible matrix (OLS falla) in `src/econometric/model.py`
- [x] T044 Run quickstart.md validation scenarios and verify all outputs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - BLOCKS US2
- **User Story 2 (Phase 4)**: Depends on US1 - necesita modelo estimado para diagnosticos
- **User Story 3 (Phase 5)**: Depends on US2 - necesita validacion para decidir si activa
- **Integration (Phase 6)**: Depends on all user stories
- **Polish (Phase 7)**: Depends on Integration

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational
- **User Story 2 (P1)**: Depends on US1 - necesita modelo estimado
- **User Story 3 (P2)**: Depends on US2 validacion - se activa condicionalmente

### Within Each User Story

- Models before services
- Services before CLI
- CLI before GUI
- Story complete before moving to next priority

### Parallel Opportunities

- Diagnostic tests (T016-T022) are all independent [P] - can be built in parallel
- What-if modules (T027-T029) are independent [P]

---

## Parallel Example: User Story 2

```bash
# Launch all diagnostic tests in parallel:
Task: "Implement Jarque-Bera test in src/econometric/diagnostics.py"
Task: "Implement White test in src/econometric/diagnostics.py"
Task: "Implement Durbin-Watson test in src/econometric/diagnostics.py"
Task: "Implement Ramsey RESET test in src/econometric/diagnostics.py"
Task: "Implement VIF calculation in src/econometric/diagnostics.py"

# Then sequentially:
Task: "Implement conditional validation block (depends on all tests)"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (OLS estimation)
4. Complete Phase 4: User Story 2 (validation + conditional block)
5. **STOP and VALIDATE**: Test modelo econometrico completo (estimar + validar)

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add US1 + US2 -> Test OLS + validacion -> Demo (MVP!)
3. Add US3 -> Test what-if scenarios -> Demo
4. Add Integration/GUI -> Test interfaces completas -> Demo
5. Polish -> Edge cases, logging, tests
