# CSV Format Contract: Import/Export

## Import Format

Archivo CSV con las siguientes columnas (orden no restrictivo, se detecta por header):

| Columna | Tipo | Obligatorio | Descripcion |
|---------|------|-------------|-------------|
| tipologia | TEXT | SI | aislada_1piso / aislada_2pisos / pareada_1piso / pareada_2pisos |
| zona_termica | INTEGER | SI | 1-9 |
| u_prom | REAL | SI | 0.5-5.0 W/m2K |
| demanda_anual_kwh | REAL | SI | 500-20000 kWh/ano |
| peak_demanda_kw | REAL | SI | 1-20 kW |
| gdc | REAL | SI | 200-4000 grados dia |
| descripcion | TEXT | NO | Caracterizacion cualitativa |
| archivo_modelo | TEXT | NO | Ruta al archivo .idf/.eso |

**Validaciones en importacion**:
1. Encabezados deben coincidir exactamente (case-insensitive)
2. Tipos de datos deben ser convertibles (texto a REAL, etc.)
3. Valores fuera de rango fisico -> error por fila
4. Duplicados (misma tipologia + zona) -> error por fila
5. Filas sin error se importan; filas con error se reportan
6. Importacion es transaccional (todo o nada por defecto; opcion `--partial` para importar filas validas)

## Export Format

Mismas columnas que el import format, con el siguiente orden estandar:

```csv
tipologia,zona_termica,u_prom,demanda_anual_kwh,peak_demanda_kw,gdc,descripcion,archivo_modelo
aislada_1piso,1,3.5,12000,5.0,500,Caso norte extremo,
aislada_1piso,2,3.2,11000,4.8,800,...
```

- Codificacion: UTF-8
- Separador: coma (,)
- Decimal: punto (.)
- Texto: entre comillas dobles si contiene comas
- Sin BOM
- Fecha ISO 8601 en nombres de archivo exportados: `simulaciones_2026-07-27.csv`
