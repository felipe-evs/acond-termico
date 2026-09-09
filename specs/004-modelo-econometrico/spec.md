# Feature Specification: Modelacion Econometrica y Validacion

**Feature Directory**: `specs/004-modelo-econometrico`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Construir una funcion analitica continua que explique el costo total optimizado mediante regresion lineal multiple, con bloque condicional de validacion estadistica y ruta alternativa de analisis por escenarios."

## Clarifications

### Session 2026-07-27

- Q: Como interactua el usuario con el modulo econometrico? -> A: CLI + GUI (ambas opciones disponibles)
- Q: Como fluyen los datos desde Feature 003 (MILP) a Feature 004? -> A: Archivos intermedios CSV (003 exporta, 004 importa)
- Q: Se deben detallar las variables de X_fisica, X_fuel, X_atrib ahora? -> A: Dejar para la fase de diseno (data-model.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Estimar Modelo de Regresion (Priority: P1)

El sistema estima un modelo de regresion lineal multiple donde el costo total optimizado Y_costo es funcion de: variables constructivas y climaticas (X_fisica), precios y rendimientos de combustibles (X_fuel), y atributos de equipos tecnologicos (X_atrib). La estimacion usa el metodo de Minimos Cuadrados Ordinarios (OLS). El modulo esta disponible tanto via CLI (ejecucion manual desde terminal) como via interfaz grafica (boton "Ejecutar modelo econometrico").

**Why this priority**: Sin el modelo estimado no se puede realizar la validacion estadistica ni obtener una herramienta analitica continua para el analisis de sensibilidad. Es el nucleo del Objetivo Especifico 4.

**Independent Test**: Ejecutar la regresion con los datos de las 36 optimizaciones y verificar que se generan los coeficientes beta y estadisticos asociados.

**Acceptance Scenarios**:

1. **Given** que existen resultados de optimizacion MILP para los 36 escenarios, **When** el usuario ejecuta la estimacion, **Then** el sistema calcula y muestra la ecuacion: Y_costo = beta_0 + beta_1*X_fisica + beta_2*X_fuel + beta_3*X_atrib + u
2. **Given** que la estimacion se completa, **When** se presentan los resultados, **Then** se muestran los coeficientes beta, errores estandar, y significancia individual (t-student)

---

### User Story 2 - Validacion Estadistica del Modelo (Priority: P1)

El sistema ejecuta el bloque de validacion estadistica para verificar si el modelo cumple los supuestos de linealidad, consistencia, ausencia de multicolinealidad y significancia global.

**Why this priority**: La validacion determina si el modelo es aceptable como herramienta definitiva o si se debe activar la ruta alternativa de analisis por escenarios.

**Independent Test**: Ejecutar la bateria completa de tests sobre el modelo estimado y verificar que cada test produce un resultado interpretable (p-value, estadistico, decision).

**Acceptance Scenarios**:

1. **Given** que el modelo esta estimado, **When** se ejecuta la validacion, **Then** el sistema aplica: Jarque-Bera (normalidad), White (heterocedasticidad), Durbin-Watson (autocorrelacion), Ramsey RESET (especificacion), VIF (multicolinealidad), F-test (significancia global), t-test (significancia individual), R2 y R2 ajustado, y ECM
2. **Given** que todos los tests pasan los umbrales definidos, **When** se evalua la validacion, **Then** el sistema consolida el Modelo Propuesto como valido
3. **Given** que uno o mas tests fallan, **When** se evalua la validacion, **Then** el sistema activa la ruta alternativa de analisis por escenarios

---

### User Story 3 - Analisis por Escenarios (Ruta Alternativa) (Priority: P2)

Si el modelo econometrico no logra validarse, el sistema ejecuta un analisis What-if con tres componentes: analisis parametrico de cambios individuales, construccion de escenarios criticos (desabastecimiento energetico, alzas extremas de tarifas), y analisis de sensibilidad multifactorial.

**Why this priority**: Garantiza que el proyecto entrega resultados validos incluso si el modelo de regresion no cumple los supuestos estadisticos.

**Independent Test**: Forzar condiciones que hagan fallar la validacion (datos no lineales) y verificar que la ruta alternativa se activa y produce resultados.

**Acceptance Scenarios**:

1. **Given** que la validacion fallo, **When** se activa la ruta alternativa, **Then** el sistema ejecuta el analisis parametrico variando un parametro a la vez y registrando el impacto en Y_costo
2. **Given** la ruta alternativa activa, **When** se construyen escenarios criticos, **Then** el sistema modela desabastecimiento (+50% precio combustible) y alza tarifaria (+100% costo electricidad)
3. **Given** la ruta alternativa activa, **When** se ejecuta el analisis de sensibilidad multifactorial, **Then** el sistema varia multiples parametros simultaneamente y presenta los resultados en una tabla de escenarios

---

### Edge Cases

- Que ocurre si hay menos de 36 observaciones (datos incompletos de Fase 1)?
- Que ocurre si el modelo tiene perfecta multicolinealidad (VIF infinito)?
- Que ocurre si la matriz de datos no es invertible (OLS falla)?
- Como se maneja un escenario donde ni la ruta principal ni la alternativa producen resultados?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST estimar un modelo de regresion lineal multiple por OLS usando statsmodels
- **FR-002**: System MUST definir Y_costo como la variable dependiente (costo total optimizado del sistema de climatizacion)
- **FR-003**: System MUST construir X_fisica a partir de variables: demanda termica, U_prom y GDC por escenario
- **FR-004**: System MUST construir X_fuel a partir de precios y rendimientos de combustibles por escenario
- **FR-005**: System MUST construir X_atrib a partir de atributos de equipos seleccionados en la optimizacion
- **FR-006**: System MUST ejecutar tests de diagnostico: Jarque-Bera, White, Durbin-Watson, Ramsey RESET, VIF
- **FR-007**: System MUST verificar significancia global (F-test) e individual (t-test) del modelo
- **FR-008**: System MUST calcular R2, R2 ajustado y Error Cuadratico Medio (ECM) del modelo
- **FR-009**: System MUST implementar bloque condicional: si validacion OK -> Modelo Propuesto definitivo; si no -> ruta alternativa What-if
- **FR-010**: System MUST ejecutar ruta alternativa con: analisis parametrico individual, escenarios criticos (desabastecimiento y alza tarifaria), y analisis de sensibilidad multifactorial
- **FR-011**: System MUST exportar resultados del modelo econometrico y/o analisis de escenarios a CSV
- **FR-012**: System MUST exponer el modulo econometrico mediante dos interfaces: CLI (linea de comandos) y GUI (interfaz grafica con boton de ejecucion)

### Key Entities

- **ModeloEconometrico**: id, formula, R2, R2_ajustado, ECM, F_statistic, F_pvalue, timestamp
- **CoeficienteRegresion**: id, modelo_id, variable_nombre, beta, error_std, t_statistic, pvalue, VIF
- **TestDiagnostico**: id, modelo_id, test_nombre (JarqueBera, White, DurbinWatson, RamseyRESET), estadistico, pvalue, resultado (pasa/falla)
- **EscenarioWhatIf**: id, tipo (parametrico, critico, multifactorial), parametros_variados, valores, resultado_Y_costo
- **ValidacionModelo**: id, modelo_id, resultado_global (validado/no_validado), razon_rechazo

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El modelo OLS se estima en menos de 10 segundos para las 36 observaciones
- **SC-002**: La bateria completa de tests de diagnostico se ejecuta en menos de 30 segundos
- **SC-003**: El bloque condicional decide correctamente entre ruta principal y alternativa segun los resultados de validacion
- **SC-004**: El analisis por escenarios (ruta alternativa) produce resultados interpretables en menos de 2 minutos
- **SC-005**: Todos los resultados son exportables a CSV

## Assumptions

- Los datos de entrada provienen de archivos CSV generados por la ejecucion de la optimizacion MILP (Feature 003)
- Existen 36 observaciones (4 tipologias x 9 zonas) para la regresion
- Feature 003 exporta resultados a CSV en un directorio de datos compartido; Feature 004 los importa desde ahi
- Se usara statsmodels para la estimacion OLS y tests de diagnostico
- Los umbrales de validacion: p-value > 0.05 para Jarque-Bera, White, Durbin-Watson; VIF < 10; F-test p-value < 0.05; t-test p-value < 0.05
- El analisis por escenarios se ejecuta unicamente si la validacion falla
- No se requiere autenticacion multi-usuario (monousuario local)
