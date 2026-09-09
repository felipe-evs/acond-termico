# Data Contract: Input desde Feature 003

Feature 004 espera un archivo CSV generado por Feature 003 (`specs/003-optimizacion-milp/contracts/csv_format.md`) con las siguientes columnas:

```csv
zona_termica,tipologia,u_prom,gdc,tecnologia_seleccionada,combustible,capacidad_kw,costo_anual_equivalente_clp
```

Feature 004 construye las variables independientes a partir de estos datos:

| Variable en 004 | Columna en CSV de 003 | Origen |
|-----------------|----------------------|--------|
| Y_costo | costo_anual_equivalente_clp | Feature 003 |
| U_prom | u_prom | Feature 001 |
| GDC | gdc | Feature 001 |
| Zona_termica | zona_termica (factor) | Feature 001 |
| Tipologia | tipologia (factor) | Feature 001 |
| Tecnologia | tecnologia_seleccionada | Feature 003 |
| Combustible | combustible | Feature 003 |
| Capacidad | capacidad_kw | Feature 003 |

Feature 004 enriquece los datos consultando precios de combustible desde la DB
compartida (`hvac_precio_combustible`) y atributos de equipos desde (`hvac_equipo`),
usando tecnologia_seleccionada y combustible como claves de busqueda.
