# Data Model: Catalogo de Alternativas de Climatizacion

## Entities

### Combustible

Catalogo de combustibles disponibles para climatizacion.

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|---------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Identificador unico |
| nombre | TEXT | NOT NULL, UNIQUE | parafina, gas_licuado, gas_natural, pellet, lena, electricidad |
| unidad_medida | TEXT | NOT NULL | litro, kg, m3, kWh |
| pci | REAL | NOT NULL, > 0 | Poder Calorifico Inferior (kcal/kg o kWh/kg segun unidad) |
| pcs | REAL | NOT NULL, > 0 | Poder Calorifico Superior (misma unidad que PCI) |
| rendimiento_transformacion | REAL | NOT NULL, 0-100 | Rendimiento de transformacion (%) |
| unidades_por_gcal | REAL | NOT NULL, > 0 | Unidades del combustible equivalentes a 1 Gcal neta |

**Relationships**: 1 Combustible -> N PrecioCombustible, 1 Combustible -> N EquipoHVAC

### PrecioCombustible

Historial de precios por combustible, region y fecha de vigencia.

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|---------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Identificador unico |
| combustible_id | INTEGER | FK -> Combustible.id, NOT NULL | Combustible asociado |
| region | INTEGER | NOT NULL, CHECK (1-16) | Region de Chile (1-16) |
| precio_por_unidad | REAL | NOT NULL, > 0 | Precio en CLP por unidad del combustible |
| fecha_vigencia | TEXT | NOT NULL | Fecha desde la cual el precio es valido (ISO 8601) |
| fuente | TEXT | NOT NULL, CHECK IN ('CNE_API', 'CNE_SCRAPING', 'CNE_CSV', 'MANUAL') | Origen del precio |
| fecha_registro | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Momento de registro en el sistema |

**Unique Constraint**: UNIQUE(combustible_id, region, fecha_vigencia)

### TipoTecnologia

Tipos de tecnologia de climatizacion considerados.

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|---------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Identificador unico |
| nombre | TEXT | NOT NULL, UNIQUE | split_inverter, estufa_lena, estufa_pellet, estufa_parafina, estufa_gas, estufa_electrica |

**Relationships**: 1 TipoTecnologia -> N EquipoHVAC

### EquipoHVAC

Equipos de climatizacion disponibles en el mercado chileno.

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|---------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Identificador unico |
| tipo_tecnologia_id | INTEGER | FK -> TipoTecnologia.id, NOT NULL | Tipo de tecnologia |
| combustible_id | INTEGER | FK -> Combustible.id, NOT NULL | Combustible que utiliza |
| modelo | TEXT | NOT NULL | Nombre comercial del modelo |
| potencia_nominal_kw | REAL | NOT NULL, > 0 | Potencia nominal de placa (kW) |
| rendimiento_termico_pct | REAL | NOT NULL, 0-100 | Rendimiento termico homologado (%) |
| costo_adquisicion_clp | REAL | NOT NULL, > 0 | Costo de adquisicion en CLP |
| tasa_consumo | REAL | NOT NULL, > 0 | Tasa de consumo (unidades del combustible por hora) |
| unidad_tasa_consumo | TEXT | NOT NULL | Unidad de la tasa de consumo (L/h, kg/h, m3/h, kWh/h) |
| costo_instalacion_clp | REAL | 0 por defecto | Costo de instalacion en CLP |
| costo_mantencion_anual_clp | REAL | 0 por defecto | Costo de mantencion anual en CLP |
| fuente_datos | TEXT | NOT NULL | Tienda, retail o distribuidor oficial |
| url_fuente | TEXT | | URL de la ficha del producto |
| fecha_registro | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Momento de registro |

**Unique Constraint**: UNIQUE(modelo, tipo_tecnologia_id)

### MatrizEleccionDiscreta (vista calculada)

Vista materializada o calculada que organiza las alternativas con costos normalizados.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| equipo_id | INTEGER | FK -> EquipoHVAC.id |
| tecnologia | TEXT | Nombre del tipo de tecnologia |
| combustible | TEXT | Nombre del combustible |
| modelo | TEXT | Modelo del equipo |
| potencia_nominal_kw | REAL | Potencia nominal |
| costo_fijo_anualizado_clp | REAL | Costo fijo anual (adquisicion + instalacion amortizados + mantencion) |
| costo_variable_por_gcal | REAL | Costo variable por Gcal util entregada |
| timestamp_calculo | TEXT | Momento del calculo |

## SQL Schema

```sql
CREATE TABLE hvac_combustible (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    unidad_medida TEXT NOT NULL,
    pci REAL NOT NULL CHECK (pci > 0),
    pcs REAL NOT NULL CHECK (pcs > 0),
    rendimiento_transformacion REAL NOT NULL CHECK (rendimiento_transformacion BETWEEN 0 AND 100),
    unidades_por_gcal REAL NOT NULL CHECK (unidades_por_gcal > 0)
);

CREATE TABLE hvac_precio_combustible (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    combustible_id INTEGER NOT NULL REFERENCES hvac_combustible(id),
    region INTEGER NOT NULL CHECK (region BETWEEN 1 AND 16),
    precio_por_unidad REAL NOT NULL CHECK (precio_por_unidad > 0),
    fecha_vigencia TEXT NOT NULL,
    fuente TEXT NOT NULL CHECK (fuente IN ('CNE_API', 'CNE_SCRAPING', 'CNE_CSV', 'MANUAL')),
    fecha_registro TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(combustible_id, region, fecha_vigencia)
);

CREATE TABLE hvac_tipo_tecnologia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE hvac_equipo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_tecnologia_id INTEGER NOT NULL REFERENCES hvac_tipo_tecnologia(id),
    combustible_id INTEGER NOT NULL REFERENCES hvac_combustible(id),
    modelo TEXT NOT NULL,
    potencia_nominal_kw REAL NOT NULL CHECK (potencia_nominal_kw > 0),
    rendimiento_termico_pct REAL NOT NULL CHECK (rendimiento_termico_pct BETWEEN 0 AND 100),
    costo_adquisicion_clp REAL NOT NULL CHECK (costo_adquisicion_clp > 0),
    tasa_consumo REAL NOT NULL CHECK (tasa_consumo > 0),
    unidad_tasa_consumo TEXT NOT NULL,
    costo_instalacion_clp REAL DEFAULT 0 CHECK (costo_instalacion_clp >= 0),
    costo_mantencion_anual_clp REAL DEFAULT 0 CHECK (costo_mantencion_anual_clp >= 0),
    fuente_datos TEXT NOT NULL,
    url_fuente TEXT,
    fecha_registro TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(modelo, tipo_tecnologia_id)
);
```

## State Transitions

- **Combustible/TipoTecnologia**: Datos semilla pre-cargados (6 combustibles, 6 tecnologias).
  No se eliminan si tienen equipos asociados (protegido por FK).
- **PrecioCombustible**: Solo INSERT (append-only para trazabilidad historica).
  No se permite UPDATE o DELETE de precios historicos.
- **EquipoHVAC**: CRUD completo. Al eliminar un equipo, se recalcula la matriz.
- **MatrizEleccionDiscreta**: Se recalcula automaticamente ante cualquier cambio en
  equipos, combustibles o precios.

## Data Volume

- 6 Combustibles (fijos)
- 6 TiposTecnologia (fijos)
- ~192 precios historicos (6 combustibles x 16 regiones x 2 fechas promedio)
- 70+ EquiposHVAC
- 1 Matriz de 70+ filas (recalculada en < 5s)
