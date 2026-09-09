# Research: Catalogo de Alternativas de Climatizacion

## Tech Stack Decisions

### GUI Framework: Streamlit
Consistente con Feature 001. Streamlit maneja formularios CRUD y tablas de datos
sin boilerplate. Ideal para el catalogo de equipos (70+ registros).

### CNE Data Acquisition: Multi-estrategia

**Decision**: Implementar 4 estrategias en orden de preferencia:

1. **API directa**: Si CNE expone endpoint JSON/XML, consultar directamente.
2. **Web scraping**: Parsear HTML del sitio oficial de CNE con beautifulsoup4.
3. **CSV descargable**: Permitir al usuario descargar CSV desde CNE e importarlo.
4. **Manual**: Formulario de ingreso manual con campos: region, precio, fecha, fuente.

**Rationale**: No existe garantia de que CNE mantenga una API estable. La estrategia
hibrida maximiza la probabilidad de obtener datos automaticamente sin depender de
un unico mecanismo.

**Alternatives considered**:
- Solo manual: Exige mucho trabajo al usuario, inconsistente con Facilidad de Uso.
- Solo scraping: Fragil ante cambios del sitio web de CNE.

### Normalizacion Energetica

Todas las alternativas se normalizan a:
- **Energia**: Giga-calorias (Gcal) como unidad comun de energia util entregada.
- **Costo**: Pesos chilenos (CLP) por Gcal util, considerando eficiencia del equipo
  y poder calorifico del combustible.

Formula de normalizacion:
```
costo_variable_por_Gcal = (precio_combustible / PCI_combustible) * rendimiento_equipo * factor_conversion
costo_fijo_anualizado = (costo_adquisicion + costo_instalacion) * factor_recuperacion_capital + costo_mantencion_anual
```

Donde `factor_recuperacion_capital = (tasa * (1+tasa)^vida_util) / ((1+tasa)^vida_util - 1)`

### Validation: Fuente de datos

Las fuentes permitidas son: tienda especializada, cadena retail, distribuidor oficial.
Se implementa como lista blanca configurable. Por defecto incluye las principales
cadenas del mercado chileno (Sodimac, Easy, MTS, etc.) mas la opcion "Otra" que
requiere justificacion.

### SQLite Shared DB

Tablas con prefijo `hvac_*` para evitar colisiones con otras features.
La conexion se reutiliza desde `src/db/connection.py` (misma DB que Feature 001).
