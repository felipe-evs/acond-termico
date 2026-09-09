# Data Model: Modelacion Econometrica y Validacion

## Entities

### ModeloEconometrico

Resultado de la estimacion OLS.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INTEGER, PK | Identificador unico |
| formula | TEXT | Especificacion: Y = b0 + b1*X1 + ... |
| R2 | REAL | Coeficiente de determinacion |
| R2_ajustado | REAL | R2 ajustado por numero de variables |
| ECM | REAL | Error Cuadratico Medio |
| F_statistic | REAL | Estadistico F del modelo |
| F_pvalue | REAL | P-value del F-test |
| n_observaciones | INTEGER | Numero de observaciones (36) |
| timestamp | TEXT | Momento de estimacion |

### CoeficienteRegresion

Coeficientes de la regresion con sus estadisticos.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INTEGER, PK | Identificador unico |
| modelo_id | INTEGER, FK | Modelo al que pertenece |
| variable_nombre | TEXT | Nombre de la variable |
| beta | REAL | Coeficiente estimado |
| error_std | REAL | Error estandar |
| t_statistic | REAL | Estadistico t |
| pvalue | REAL | P-value del t-test |
| VIF | REAL | Factor de Inflacion de la Varianza |

### TestDiagnostico

Resultados de cada prueba de diagnostico.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INTEGER, PK | Identificador unico |
| modelo_id | INTEGER, FK | Modelo al que pertenece |
| test_nombre | TEXT | JarqueBera, White, DurbinWatson, RamseyRESET |
| estadistico | REAL | Valor del estadistico |
| pvalue | REAL | P-value del test |
| resultado | TEXT | pasa / falla |

### EscenarioWhatIf

Resultados de la ruta alternativa (analisis por escenarios).

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INTEGER, PK | Identificador unico |
| tipo | TEXT | parametrico, critico, multifactorial |
| parametros_variados | TEXT | Descripcion de parametros modificados |
| valores | TEXT | Valores de los parametros |
| resultado_Y_costo | REAL | Costo resultante del escenario |

### ValidacionModelo

Resultado del bloque condicional.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INTEGER, PK | Identificador unico |
| modelo_id | INTEGER, FK | Modelo evaluado |
| resultado_global | TEXT | validado / no_validado |
| razon_rechazo | TEXT | Causa del rechazo si aplica |

## SQL Schema

```sql
CREATE TABLE eco_modelo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula TEXT NOT NULL,
    R2 REAL,
    R2_ajustado REAL,
    ECM REAL,
    F_statistic REAL,
    F_pvalue REAL,
    n_observaciones INTEGER NOT NULL DEFAULT 36,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE eco_coeficiente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL REFERENCES eco_modelo(id),
    variable_nombre TEXT NOT NULL,
    beta REAL NOT NULL,
    error_std REAL,
    t_statistic REAL,
    pvalue REAL,
    VIF REAL
);

CREATE TABLE eco_test_diagnostico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL REFERENCES eco_modelo(id),
    test_nombre TEXT NOT NULL,
    estadistico REAL,
    pvalue REAL,
    resultado TEXT NOT NULL CHECK (resultado IN ('pasa', 'falla'))
);

CREATE TABLE eco_escenario_whatif (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK (tipo IN ('parametrico', 'critico', 'multifactorial')),
    parametros_variados TEXT,
    valores TEXT,
    resultado_Y_costo REAL
);

CREATE TABLE eco_validacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL REFERENCES eco_modelo(id),
    resultado_global TEXT NOT NULL CHECK (resultado_global IN ('validado', 'no_validado')),
    razon_rechazo TEXT
);
```

## State Transitions

- **eco_modelo**: Se INSERT al ejecutar la estimacion. Historial de ejecuciones.
- **eco_coeficiente**: Se INSERT junto con el modelo. Solo lectura posterior.
- **eco_test_diagnostico**: Se INSERT junto con el modelo.
- **eco_escenario_whatif**: Se INSERT solo si la validacion falla.
- **eco_validacion**: Se INSERT con el resultado del bloque condicional.
