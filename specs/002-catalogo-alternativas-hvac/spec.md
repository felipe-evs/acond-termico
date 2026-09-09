# Feature Specification: Catalogo de Alternativas de Climatizacion

**Feature Directory**: `specs/002-catalogo-alternativas-hvac`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Construir una base de datos estandarizada de alternativas de climatizacion del mercado chileno, con parametros de combustible, equipos HVAC, y matriz de eleccion discreta."

## Clarifications

### Session 2026-07-27

- Q: Como interactua el usuario con el catalogo? -> A: CLI + GUI + CSV Import (carga masiva)
- Q: Como se obtienen los precios CNE? -> A: Multiple: API directa si disponible, web scraping, CSV descargable, e ingreso manual
- Q: Como entrega 002 los datos a 003? -> A: DB SQLite compartida (002 escribe, 003 lee) + CSV export para el investigador

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gestionar Combustibles (Priority: P1)

El usuario investigador administra un catalogo de combustibles con sus parametros fisicos y economicos. Cada combustible tiene: unidad de medida, PCI, PCS, rendimiento de transformacion, costo por unidad y unidades por Gcal neta. Los precios pueden obtenerse automaticamente desde fuentes CNE o ingresarse manualmente con capacidad de especificar region y fecha de vigencia.

**Why this priority**: Los combustibles son la base de todo calculo energetico y economico posterior. Sin ellos no se puede normalizar ni comparar alternativas.

**Independent Test**: Crear un combustible (ej. parafina) con todos sus parametros, verificar que aparece en el listado, editarlo y eliminarlo.

**Acceptance Scenarios**:

1. **Given** el usuario accede al modulo de combustibles, **When** crea un nuevo combustible con todos los parametros obligatorios, **Then** el sistema guarda el registro y lo muestra en el listado de combustibles
2. **Given** que existen precios CNE disponibles para un combustible, **When** el usuario activa la carga automatica, **Then** el sistema importa los precios y los asocia al combustible
3. **Given** el usuario necesita un precio regional especifico, **When** ingresa manualmente precio, region y fecha de vigencia, **Then** el sistema almacena el precio regional con trazabilidad temporal
4. **Given** que el usuario intenta eliminar un combustible asociado a equipos, **When** confirma la eliminacion, **Then** el sistema advierte de dependencias y bloquea la operacion

---

### User Story 2 - Gestionar Equipos HVAC (Priority: P1)

El usuario investigador registra equipos de climatizacion disponibles en el mercado chileno. Cada equipo incluye: tipo de tecnologia (split inverter, estufa a le~na, pellet, parafina, gas, electrica), combustible asociado, potencia nominal, rendimiento termico, costo de adquisicion, tasa de consumo, costo de instalacion y costo de mantencion. Las fuentes de datos deben ser exclusivamente tiendas especializadas, grandes cadenas de retail y distribuidores oficiales. El sistema ofrece tres modalidades de entrada: GUI (formulario individual), CLI (comandos para CRUD) y CSV Import (carga masiva de equipos desde archivo CSV).

**Why this priority**: Sin los equipos no existe la matriz de decision ni la optimizacion. Es la base del Objetivo Especifico 2.

**Independent Test**: Registrar 3 equipos de distintos tipos y verificar que aparecen en la matriz de eleccion discreta calculada.

**Acceptance Scenarios**:

1. **Given** el usuario crea un equipo HVAC, **When** completa tecnologia, combustible asociado, potencia nominal, rendimiento y costo, **Then** el sistema guarda el equipo y lo muestra en el catalogo
2. **Given** que el usuario ingresa un equipo con fuente de datos no valida (ej. mercado informal), **When** intenta guardar, **Then** el sistema rechaza el registro con mensaje sobre las fuentes permitidas
3. **Given** que existen al menos 10 equipos por tipo de tecnologia, **When** se consulta el catalogo, **Then** el sistema muestra la distribucion y contador de equipos por tipo
4. **Given** que se registran los 70 modelos objetivo, **When** se actualiza la matriz de eleccion discreta, **Then** el sistema calcula automaticamente los costos fijos anualizados y costos variables por energia util

---

### User Story 3 - Visualizar Matriz de Eleccion Discreta (Priority: P2)

El sistema organiza y visualiza las alternativas tecnologicas en una matriz estructurada, indexada por costos fijos anualizados y costos variables por unidad de energia util entregada.

**Why this priority**: La matriz es el insumo directo para el modelo de optimizacion MILP. Sin ella no se puede ejecutar la Fase 3.

**Independent Test**: Verificar que al registrar equipos con distintos combustibles, la matriz calcula correctamente los costos normalizados.

**Acceptance Scenarios**:

1. **Given** que existen equipos y combustibles registrados, **When** el usuario accede a la matriz, **Then** ve cada alternativa con costo fijo anualizado y costo variable por Gcal util
2. **Given** que se agrega un nuevo equipo, **When** se actualiza la matriz, **Then** el nuevo equipo aparece con sus costos normalizados calculados

---

### Edge Cases

- Que ocurre cuando un precio de combustible no esta disponible para una region especifica?
- Que ocurre cuando hay multiples precios historicos para el mismo combustible y region?
- Como se maneja un equipo con rendimiento termico superior al 100% (error de datos)?
- Que ocurre si no existen suficientes equipos (menos de 10) para un tipo de tecnologia?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to crear, leer, actualizar y eliminar combustibles con parametros: nombre, unidad medida, PCI (kcal/kg o kWh/kg), PCS, rendimiento de transformacion, y conversion a Gcal
- **FR-002**: System MUST obtener precios de combustibles mediante multiples estrategias segun disponibilidad: API directa, web scraping del sitio CNE, importacion de CSV descargable, o ingreso manual
- **FR-003**: Users MUST be able to ingresar precios de combustibles manualmente con campos: region, precio por unidad, fecha de vigencia, y fuente
- **FR-004**: System MUST almacenar el historico de precios por combustible, region y fecha para permitir trazabilidad
- **FR-005**: Users MUST be able to crear, leer, actualizar y eliminar equipos HVAC con: tipo tecnologia, combustible asociado, potencia nominal (kW), rendimiento termico (%), costo adquisicion (CLP), tasa consumo (unidad/h), costo instalacion, costo mantencion anual, y fuente de datos
- **FR-006**: System MUST validar que la fuente de datos del equipo sea de tienda especializada, retail o distribuidor oficial; rechazar fuentes informales
- **FR-007**: System MUST calcular automaticamente la Matriz de Eleccion Discreta con costo fijo anualizado (CLP/ano) y costo variable por energia util entregada (CLP/Gcal)
- **FR-008**: System MUST normalizar todas las alternativas a unidades comparables (Gcal, CLP) independientemente del combustible o tecnologia
- **FR-009**: System MUST llevar un contador de equipos por tipo de tecnologia y alertar si algun tipo tiene menos de 10 registros
- **FR-010**: Users MUST be able to exportar el catalogo de equipos, combustibles y matriz de eleccion a formato CSV
- **FR-011**: Users MUST be able to importar equipos y combustibles masivamente mediante archivo CSV con validacion previa de formato y datos
- **FR-012**: System MUST exponer el catalogo mediante tres interfaces: CLI (comandos), GUI (formularios) e importacion CSV
- **FR-013**: System MUST persistir los datos del catalogo en una base de datos SQLite compartida para que Feature 003 (optimizacion MILP) pueda leerlos

### Key Entities

- **Combustible**: id, nombre (parafina, gas licuado, gas natural, pellet, le~na, electricidad), unidad_medida, PCI, PCS, rendimiento_transformacion, unidades_por_Gcal
- **PrecioCombustible**: id, combustible_id, region, precio_por_unidad, fecha_vigencia, fuente (CNE o manual), fecha_registro
- **TipoTecnologia**: id, nombre (split_inverter, estufa_lena, estufa_pellet, estufa_parafina, estufa_gas, estufa_electrica)
- **EquipoHVAC**: id, tipo_tecnologia_id, combustible_id, modelo, potencia_nominal_kW, rendimiento_termico_pct, costo_adquisicion_CLP, tasa_consumo, unidad_tasa_consumo, costo_instalacion_CLP, costo_mantencion_anual_CLP, fuente_datos, url_fuente, fecha_registro
- **MatrizEleccionDiscreta**: vista calculada con equipo_id, costo_fijo_anualizado_CLP, costo_variable_por_Gcal, timestamp_calculo

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El catalogo contiene al menos 70 equipos HVAC distribuidos en al menos 6 tipos de tecnologia
- **SC-002**: Cada tipo de tecnologia tiene al menos 10 equipos registrados
- **SC-003**: Los precios de combustibles pueden cargarse automaticamente desde CNE o manualmente por region
- **SC-004**: La Matriz de Eleccion Discreta se calcula en menos de 5 segundos tras cada actualizacion
- **SC-005**: Todos los valores economicos y energeticos estan normalizados a CLP y Gcal para comparabilidad directa

## Assumptions

- Los precios CNE se obtienen mediante estrategia hibrida: API directa si existe, web scraping como alternativa, CSV descargable como respaldo, y entrada manual siempre disponible
- El proyecto considera combustibles: parafina, gas licuado, gas natural, pellet, le~na y electricidad
- Las tecnologias consideradas: split inverter, estufa le~na, estufa pellet, estufa parafina, estufa gas, estufa electrica
- Los datos de equipos se recopilan manualmente por el investigador desde las fuentes oficiales
- Las 12 regiones de Chile pueden tener precios de combustible diferenciados
- Los datos del catalogo se almacenan en una base de datos SQLite compartida con Feature 003 (002 escribe, 003 lee)
- No se requiere autenticacion multi-usuario (monousuario local)
