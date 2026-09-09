---

description: "Task list for Carga de Resultados de Simulacion"

---

# Tasks: Carga de Resultados de Simulacion

**Input**: Design documents from `specs/001-cargar-resultados-simulacion/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are included for core validation (rangos fisicos, CLI commands). Tests are OPTIONAL features for the CRUD operations.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure with directories `src/estudio/`, `src/db/`, `src/shared/`, `tests/`, `data/`, `output/`
- [x] T002 [P] Create `src/__init__.py` and `src/estudio/__init__.py`, `src/db/__init__.py`, `src/shared/__init__.py`
- [x] T003 [P] Create `requirements.txt` with click, streamlit, pandas
- [x] T004 Create `data/.gitkeep` and add `data/`, `output/` to `.gitignore`
- [x] T005 [P] Configure pytest with `tests/conftest.py` and `pytest.ini`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create shared SQLite database connection module in `src/db/connection.py`
- [x] T007 Create database schema initialization in `src/db/schema.py` with tables: sim_estudio, sim_simulacion, sim_resultado
- [x] T008 Create physical range validators in `src/shared/validators.py` for U_prom, demanda anual, peak demanda, GDC
- [x] T009 [P] Create CSV format validator in `src/shared/csv_validator.py` (headers, types, ranges)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cargar Resultados de Simulacion (Priority: P1) MVP

**Goal**: El usuario puede cargar una simulacion con sus 4 parametros de salida via CLI, GUI o CSV import

**Independent Test**: Crear una simulacion via CLI y verificar que aparece en la DB SQLite

### Implementation for User Story 1

- [x] T010 [P] [US1] Create Estudio model in `src/estudio/models.py`
- [x] T011 [P] [US1] Create Simulacion model in `src/estudio/models.py`
- [x] T012 [P] [US1] Create ResultadoSimulacion model in `src/estudio/models.py`
- [x] T013 [US1] Implement EstudioRepository (init, get) in `src/estudio/repository.py`
- [x] T014 [US1] Implement SimulacionRepository (create with validacion) in `src/estudio/repository.py`
- [x] T015 [US1] Implement CLI command `simulacion create` with all flags in `src/estudio/cli.py`
- [x] T016 [US1] Implement CLI command `estudio init` in `src/estudio/cli.py`
- [x] T017 [US1] Implement GUI form for carga individual in `src/estudio/gui.py`
- [x] T018 [US1] Implement CSV import in `src/estudio/csv_handler.py` with validacion previa
- [x] T019 [US1] Implement CLI command `simulacion import` in `src/estudio/cli.py`

**Checkpoint**: At this point, el usuario puede cargar simulaciones por CLI, GUI y CSV. Feature 003 puede leer los datos desde la DB compartida.

---

## Phase 4: User Story 2 - Adjuntar Archivo del Modelo (Priority: P2)

**Goal**: El usuario puede adjuntar opcionalmente archivos .idf/.eso a cada simulacion

**Independent Test**: Crear una simulacion con archivo adjunto y verificar que el archivo se almacena

### Implementation for User Story 2

- [x] T020 [P] [US2] Add file attachment field handling in `src/estudio/repository.py`
- [x] T021 [P] [US2] Implement file storage logic (copy to `data/attachments/`) in `src/estudio/services.py`
- [x] T022 [P] [US2] Add `--archivo-modelo` flag to CLI `simulacion create` in `src/estudio/cli.py`
- [x] T023 [US2] Add file upload widget to GUI form in `src/estudio/gui.py`
- [x] T024 [US2] Add file path column to CSV import/export in `src/estudio/csv_handler.py`

**Checkpoint**: Los archivos adjuntos se almacenan y asocian correctamente a cada simulacion.

---

## Phase 5: User Story 3 - Revisar y Gestionar Registros (Priority: P3)

**Goal**: El usuario puede listar, editar y eliminar simulaciones

**Independent Test**: Listar simulaciones, editar un campo, eliminar otra, verificar persistencia

### Implementation for User Story 3

- [x] T025 [P] [US3] Implement SimulacionRepository.list() with filters in `src/estudio/repository.py`
- [x] T026 [P] [US3] Implement SimulacionRepository.update() in `src/estudio/repository.py`
- [x] T027 [P] [US3] Implement SimulacionRepository.delete() with confirmacion in `src/estudio/repository.py`
- [x] T028 [US3] Implement CLI command `simulacion list` in `src/estudio/cli.py`
- [x] T029 [P] [US3] Implement CLI command `simulacion update` in `src/estudio/cli.py`
- [x] T030 [P] [US3] Implement CLI command `simulacion delete` in `src/estudio/cli.py`
- [x] T031 [US3] Add list view to GUI in `src/estudio/gui.py`
- [x] T032 [P] [US3] Add edit form to GUI in `src/estudio/gui.py`
- [x] T033 [P] [US3] Add delete button with confirmation to GUI in `src/estudio/gui.py`
- [x] T034 [US3] Implement CLI command `simulacion export` in `src/estudio/cli.py`
- [x] T035 [US3] Add export button to GUI list view in `src/estudio/gui.py`

**Checkpoint**: CRUD completo de simulaciones via CLI y GUI. Datos exportables a CSV.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T036 [P] Add database migration support (schema version tracking) in `src/db/schema.py`
- [x] T037 [P] Add error handling middleware for CLI (try/except en comandos) in `src/estudio/cli.py`
- [x] T038 [P] Add logging configuration in `src/shared/logging_config.py`
- [x] T039 [P] Write unit tests for validators in `tests/test_validators.py`
- [x] T040 [P] Write unit tests for models in `tests/test_models.py`
- [x] T041 [P] Write unit tests for repository in `tests/test_repository.py`
- [x] T042 [P] Write integration tests for CLI commands in `tests/test_cli.py`
- [x] T043 [P] Write integration tests for CSV import/export in `tests/test_csv_handler.py`
- [x] T044 Run quickstart.md validation scenarios and verify all outputs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - models must exist before services
- **User Story 2 (Phase 4)**: Depends on US1 repository - file attachment extends create/update
- **User Story 3 (Phase 5)**: Depends on US1 repository - list/edit/delete on existing data
- **Polish (Phase 6)**: Depends on all user stories

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 repository but independently testable (crear con archivo)
- **User Story 3 (P3)**: Depends on US1 data operations but independently testable (CRUD sobre datos existentes)

### Within Each User Story

- Models before services
- Services before CLI
- CLI before GUI
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- CLI commands for different stories marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all models together:
Task: "Create Estudio model in src/estudio/models.py"
Task: "Create Simulacion model in src/estudio/models.py"
Task: "Create ResultadoSimulacion model in src/estudio/models.py"

# Then sequentially:
Task: "Implement repository (depends on models)"
Task: "Implement CLI command simulacion create (depends on repository)"
Task: "Implement GUI form (depends on repository)"
Task: "Implement CSV import (depends on repository)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (CLI create + CSV import)
4. **STOP and VALIDATE**: Test carga individual y masiva de simulaciones
5. Verificar que Feature 003 puede leer datos desde DB compartida

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test carga CLI/GUI/CSV -> Demo (MVP!)
3. Add User Story 2 -> Test archivos adjuntos -> Demo
4. Add User Story 3 -> Test CRUD completo + export -> Demo
5. Polish -> Tests y documentacion
