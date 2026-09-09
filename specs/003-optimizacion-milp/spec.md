# Feature Specification: Modelo de Optimizacion MILP

**Feature Directory**: `specs/003-optimizacion-milp`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Desarrollar un modelo de Programacion Lineal Entera Mixta (MILP) que minimice el costo global del ciclo de vida del sistema de climatizacion, usando los datos de demanda termica (Fase 1) y la matriz de eleccion discreta (Fase 2)."

## Clarifications

### Session 2026-07-27

- Q: Como ejecuta el usuario la optimizacion? -> A: CLI + GUI (ambas opciones disponibles)
- Q: Como fluyen los datos desde Features 001 y 002 a 003? -> A: DB SQLite compartida (001 y 002 escriben, 003 lee)
- Q: Los 36 escenarios se ejecutan secuencialmente o en paralelo? -> A: Paralelo (concurrent.futures)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ejecutar Optimizacion MILP (Priority: P1)

El sistema ejecuta el modelo MILP que selecciona las tecnologias, capacidades y combustibles optimos para cada zona climatica. La funcion objetivo minimiza el Costo Anual Equivalente total, sujeto a restricciones de satisfaccion del pico de demanda y la energia anual requerida por cada tipologia habitacional. El modelo usa variables binarias para representar la naturaleza dicotomica e indivisible de la seleccion tecnologica. El modulo esta disponible tanto via CLI como via GUI (boton "Ejecutar optimizacion").

**Why this priority**: Es el nucleo del Objetivo Especifico 3. Sin la optimizacion no se pueden determinar las soluciones optimas por zona climatica.

**Independent Test**: Ejecutar la optimizacion con los datos de las 36 simulaciones (Fase 1) y 70 equipos (Fase 2), verificar que el solver retorna una solucion factible con asignaciones discretas.

**Acceptance Scenarios**:

1. **Given** que existen datos de demanda termica (U_prom, demanda anual, peak, GDC) y matriz de eleccion discreta, **When** el usuario ejecuta la optimizacion, **Then** el modelo MILP resuelve y retorna las variables de seleccion con un valor de funcion objetivo
2. **Given** que el modelo se ejecuta con los 36 escenarios (4 tipologias x 9 zonas), **When** termina la optimizacion, **Then** cada escenario tiene asignada al menos una tecnologia con capacidad y combustible definidos
3. **Given** que la optimizacion no encuentra solucion factible (ej. restricciones demasiado estrictas), **When** el solver retorna error, **Then** el sistema muestra un mensaje claro con las restricciones que provocaron la infactibilidad

---

### User Story 2 - Configurar Parametros de Optimizacion (Priority: P2)

El usuario investigador puede configurar los parametros economicos del modelo: tasa de descuento, vida util de los equipos y parametro de perdida sistemica que captura desviaciones operacionales no modeladas.

**Why this priority**: La configuracion de parametros permite analisis de sensibilidad y ajuste del modelo a diferentes escenarios.

**Independent Test**: Modificar la tasa de descuento y verificar que el resultado de optimizacion cambia consistentemente.

**Acceptance Scenarios**:

1. **Given** el usuario accede a la configuracion de parametros, **When** modifica la tasa de descuento, vida util o perdida sistemica, **Then** los cambios se guardan y aplican en la siguiente ejecucion
2. **Given** que se ejecuta la optimizacion con parametros actualizados, **When** se comparan los resultados con la ejecucion anterior, **Then** las diferencias son atribuibles a los cambios de parametros

---

### User Story 3 - Visualizar Resultados de Optimizacion (Priority: P3)

El sistema presenta los resultados de la optimizacion: que tecnologias, capacidades y combustibles representan el optimo economico para cada zona climatica evaluada.

**Why this priority**: La visualizacion permite al investigador interpretar y validar los resultados del modelo.

**Independent Test**: Verificar que los resultados se muestran agrupados por zona climatica con indicacion de tecnologia seleccionada y costo anual equivalente.

**Acceptance Scenarios**:

1. **Given** que la optimizacion se ha ejecutado exitosamente, **When** el usuario accede a los resultados, **Then** ve una tabla con zona, tipologia, tecnologia seleccionada, capacidad, combustible y costo anual equivalente
2. **Given** que existen resultados para las 9 zonas, **When** se visualiza por zona, **Then** cada zona muestra su combinacion optima con los valores numericos correspondientes

---

### Edge Cases

- Que ocurre si no hay datos de demanda termica cargados (Fase 1)?
- Que ocurre si la matriz de eleccion discreta esta vacia (Fase 2)?
- Como se maneja un problema MILP que requiere mas memoria de la disponible?
- Que ocurre si el solver no converge dentro del tiempo limite?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implementar un modelo de Programacion Lineal Entera Mixta (MILP) con variables binarias para seleccion de equipos
- **FR-002**: System MUST utilizar PuLP como libreria de modelado con solver CBC incluido para resolver el MILP
- **FR-003**: System MUST definir la funcion objetivo como minimizacion del Costo Anual Equivalente total: costo_fijo_anualizado + costo_variable_por_energia_util
- **FR-004**: System MUST aplicar restriccion de satisfaccion del pico de demanda termica (kW) para cada tipologia y zona
- **FR-005**: System MUST aplicar restriccion de satisfaccion de la energia anual requerida (kWh/ano) para cada tipologia y zona
- **FR-006**: System MUST incorporar el parametro de perdida sistemica en los calculos de eficiencia
- **FR-007**: Users MUST be able to configurar: tasa de descuento (%), vida util de equipos (anos), y perdida sistemica (%)
- **FR-008**: System MUST validar la factibilidad del problema y reportar restricciones conflictivas si no encuentra solucion
- **FR-009**: System MUST mostrar resultados por escenario con: zona termica, tipologia, tecnologia seleccionada, capacidad instalada (kW), combustible, costo anual equivalente (CLP/ano)
- **FR-010**: System MUST exportar los resultados de optimizacion a formato CSV
- **FR-011**: System MUST exponer el modulo de optimizacion mediante dos interfaces: CLI (linea de comandos) y GUI (interfaz grafica con boton de ejecucion)

### Key Entities

- **EscenarioOptimizacion**: id, zona_termica, tipologia, demanda_anual_kwh, peak_demanda_kw, U_prom, GDC
- **ParametroOptimizacion**: id, tasa_descuento_pct, vida_util_anos, perdida_sistemica_pct
- **ResultadoOptimizacion**: id, escenario_id, equipo_hvac_id, capacidad_asignada_kw, costo_anual_equivalente_CLP, timestamp
- **VariableSeleccion**: id, resultado_id, tecnologia_nombre, combustible_nombre, es_seleccionado (binario)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El modelo MILP resuelve los 36 escenarios (4 tipologias x 9 zonas) en menos de 3 minutos gracias a la ejecucion paralela
- **SC-002**: Cada escenario produce una solucion factible con seleccion discreta de equipos
- **SC-003**: El usuario puede modificar parametros economicos y re-ejecutar en menos de 30 segundos de interaccion
- **SC-004**: Los resultados son exportables a CSV para su revision y validacion academica

## Assumptions

- Los datos de Fase 1 (demanda termica) estan cargados en el sistema via la feature 001
- Los datos de Fase 2 (catalogo equipos y matriz de eleccion) estan cargados via la feature 002
- Los datos residen en una base de datos SQLite compartida entre las features; 001 y 002 escriben, 003 lee directamente desde ahi
- Se usara PuLP con solver CBC (incluido en la libreria, sin instalacion externa)
- El modelo asume costo fijo anualizado mediante metodo de recuperacion de capital con la tasa de descuento y vida util configuradas
- Las 36 simulaciones se optimizan en paralelo (no hay restricciones entre zonas)
- No se requiere autenticacion multi-usuario (monousuario local)
