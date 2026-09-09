# Feature Specification: Carga de Resultados de Simulacion

**Feature Directory**: `specs/001-cargar-resultados-simulacion`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Cargar los resultados de la Fase 1 (simulacion termica dinamica en DesignBuilder/EnergyPlus) al sistema mediante un formulario mantenedor."

## Clarifications

### Session 2026-07-27

- Q: Como entrega 001 los datos a Features 002/003? -> A: DB SQLite compartida + CSV export (001 escribe, 003 lee)
- Q: Como interactua el usuario con la carga de simulaciones? -> A: CLI + GUI + CSV Import (carga masiva)
- Q: Se definen los rangos de validacion fisica ahora? -> A: Si, definirlos en el spec

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cargar Resultados de Simulacion (Priority: P1)

El usuario investigador ingresa los resultados de una simulacion de DesignBuilder al sistema. Debe seleccionar la tipologia de vivienda y zona termica, ingresar los 4 parametros de salida (U_prom, demanda anual, peak de demanda, GDC) y opcionalmente adjuntar el archivo del modelo. El sistema ofrece tres modalidades de entrada: GUI (formulario individual), CLI (comandos para CRUD) y CSV Import (carga masiva de simulaciones desde archivo).

**Why this priority**: Sin los datos de simulacion cargados no es posible avanzar a las etapas posteriores de modelamiento estadistico y optimizacion. Es la puerta de entrada del proyecto.

**Independent Test**: Puede probarse creando un registro de simulacion con valores numericos validos y verificando que aparece en el listado de simulaciones.

**Acceptance Scenarios**:

1. **Given** que el usuario esta en la pantalla de carga de simulacion, **When** completa tipologia, zona termica, los 4 parametros de salida y una descripcion, **Then** el sistema guarda el registro y lo muestra en el listado de simulaciones
2. **Given** que el usuario ingresa un valor no numerico en uno de los 4 parametros, **When** intenta guardar, **Then** el sistema muestra un error de validacion y no guarda el registro
3. **Given** que el usuario ingresa un valor fuera del rango fisicamente plausible (ej. U_prom negativo), **When** intenta guardar, **Then** el sistema muestra una advertencia de rango invalido

---

### User Story 2 - Adjuntar Archivo del Modelo (Priority: P2)

El usuario puede adjuntar opcionalmente el archivo del modelo DesignBuilder/EnergyPlus (.idf, .eso, etc.) como respaldo del registro de simulacion.

**Why this priority**: El archivo del modelo no es critico para las etapas siguientes pero sirve como documentacion y trazabilidad academica.

**Independent Test**: Crear un registro con archivo adjunto y verificar que el archivo se asocia correctamente al registro.

**Acceptance Scenarios**:

1. **Given** que el usuario esta creando o editando una simulacion, **When** selecciona un archivo valido y lo adjunta, **Then** el sistema guarda el archivo y muestra el nombre en el registro
2. **Given** que el usuario no adjunta ningun archivo, **When** guarda la simulacion, **Then** el sistema crea el registro correctamente sin archivo asociado

---

### User Story 3 - Revisar y Gestionar Registros (Priority: P3)

El usuario puede listar todas las simulaciones cargadas, editarlas y eliminarlas segun sea necesario.

**Why this priority**: La gestion de datos es necesaria para corregir errores de carga y mantener la calidad de los datos.

**Independent Test**: Listar simulaciones, editar un campo de una existente, y eliminar otra, verificando que los cambios persisten.

**Acceptance Scenarios**:

1. **Given** que existen simulaciones cargadas, **When** el usuario accede al listado, **Then** ve todas las simulaciones con sus datos principales
2. **Given** un registro de simulacion existente, **When** el usuario edita un campo y guarda, **Then** los cambios se reflejan en el listado
3. **Given** un registro de simulacion existente, **When** el usuario confirma la eliminacion, **Then** el registro desaparece del listado

---

### Edge Cases

- Que ocurre cuando el usuario intenta cargar un archivo de modelo con formato no soportado?
- Que ocurre cuando se interrumpe la carga de un archivo grande?
- Que ocurre si el usuario intenta duplicar una combinacion tipologia-zona termica ya existente?
- Como maneja el sistema valores extremos pero fisicamente posibles (ej. GDC muy alto para zonas frias)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to crear un registro de simulacion seleccionando tipologia de vivienda y zona termica
- **FR-002**: System MUST aceptar los 4 parametros de salida como valores numericos: U_prom (W/m2K), demanda anual (kWh/ano), peak de demanda (kW), GDC (grados dia)
- **FR-003**: System MUST validar que los valores numericos esten en rangos fisicamente plausibles: U_prom (0.5-5.0 W/m2K), demanda anual (500-20000 kWh/ano), peak de demanda (1-20 kW), GDC (200-4000 grados dia base 15C)
- **FR-004**: Users MUST be able to agregar una descripcion o caracterizacion cualitativa del caso simulado
- **FR-005**: Users MUST be able to adjuntar opcionalmente uno o mas archivos del modelo DesignBuilder/EnergyPlus
- **FR-006**: System MUST listar todas las simulaciones cargadas con sus datos principales en una vista de tabla
- **FR-007**: Users MUST be able to editar cualquier campo de una simulacion existente
- **FR-008**: Users MUST be able to eliminar una simulacion existente con confirmacion previa
- **FR-009**: System MUST permitir exportar el listado de simulaciones a formato CSV
- **FR-010**: System MUST agrupar todas las simulaciones bajo un unico estudio o proyecto academico
- **FR-011**: System MUST persistir los datos de simulacion en una base de datos SQLite compartida para que Feature 003 (optimizacion MILP) pueda leerlos
- **FR-012**: System MUST exponer la carga de simulaciones mediante tres interfaces: CLI (comandos), GUI (formularios) e importacion CSV masiva
- **FR-013**: Users MUST be able to importar simulaciones masivamente mediante archivo CSV con validacion de formato y rangos fisicos

### Key Entities

- **Estudio**: Contenedor unico del proyecto academico. Contiene el conjunto completo de 36 simulaciones. Atributos: id, nombre, descripcion, fecha de creacion
- **Simulacion**: Representa una ejecucion de DesignBuilder para una combinacion especifica de tipologia y zona termica. Atributos: id, tipologia (aislada 1 piso, aislada 2 pisos, pareada 1 piso, pareada 2 pisos), zona_termica (1-9), descripcion, archivos_adjuntos (opcional), fecha_carga, foreign_key a Estudio
- **ResultadoSimulacion**: Valores numericos de salida de la simulacion. Atributos: id, simulacion_id, U_prom, demanda_anual_kwh, peak_demanda_kw, GDC

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario puede completar la carga de una simulacion individual en menos de 2 minutos
- **SC-002**: El sistema puede almacenar y mostrar las 36 simulaciones sin degradacion de rendimiento
- **SC-003**: El 100% de los valores numericos ingresados son validados contra rangos fisicos plausibles al momento de guardar
- **SC-004**: Los datos pueden exportarse a CSV y reimportarse en herramientas academicas (Excel, MATLAB, R) sin perdida de informacion

## Assumptions

- El proyecto tiene un solo estudio academico que agrupa las 36 simulaciones (no se requiere multi-proyecto)
- El archivo del modelo adjunto es opcional; los valores calculados son los datos criticos obligatorios
- El usuario es un investigador academico con familiaridad basica con los conceptos termicos (U_prom, demanda, GDC)
- No se requiere autenticacion de usuarios para esta version (monousuario local)
- Los rangos de validacion fisica se definieron en FR-003 basados en valores tipicos para viviendas de interes social en Chile segun normativa MINVU 2024
- El formato de exportacion inicial es CSV; otros formatos se evaluaran en etapas posteriores
- Los datos del estudio y simulaciones se almacenan en una base de datos SQLite compartida con Feature 003 (001 escribe, 003 lee)
