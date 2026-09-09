# CLI Contract: Carga de Resultados de Simulacion

## Command: `estudio init`

Inicializa el estudio academico (se ejecuta una vez al iniciar el proyecto).

```bash
estudio init --nombre "Modelo Optimizacion Termico Chile" --descripcion "Tesis academica"
```

**Output**: `{"id": 1, "nombre": "...", "fecha_creacion": "2026-07-27"}`

---

## Command: `simulacion create`

Crea una nueva simulacion con sus resultados.

```bash
simulacion create \
    --tipologia aislada_1piso \
    --zona-termica 5 \
    --u-prom 2.3 \
    --demanda-anual 8500 \
    --peak-demanda 4.5 \
    --gdc 1500 \
    --descripcion "Vivienda aislada 1 piso, zona central" \
    --archivo-modelo ./modelos/caso_01.idf
```

**Output**: `{"id": 1, "tipologia": "aislada_1piso", "zona_termica": 5, ...}`

---

## Command: `simulacion list`

Lista todas las simulaciones cargadas.

```bash
simulacion list
```

**Output**: Tabla con columnas: id, tipologia, zona_termica, u_prom, demanda_anual, peak, gdc, fecha_carga

Opciones: `--format json` para output en JSON.

---

## Command: `simulacion update`

Actualiza una simulacion existente.

```bash
simulacion update 1 --descripcion "Texto actualizado" --u-prom 2.5
```

**Output**: `{"id": 1, "updated": true}`
**Error**: `{"error": "Simulacion no encontrada"}` (si id no existe)

---

## Command: `simulacion delete`

Elimina una simulacion (con confirmacion).

```bash
simulacion delete 1 --force
```

**Output**: `{"id": 1, "deleted": true}`

---

## Command: `simulacion import`

Importa simulaciones desde archivo CSV.

```bash
simulacion import ./datos/simulaciones.csv
```

**Expected CSV format**:

```csv
tipologia,zona_termica,u_prom,demanda_anual_kwh,peak_demanda_kw,gdc,descripcion,archivo_modelo
aislada_1piso,5,2.3,8500,4.5,1500,Caso zona central,
pareada_2pisos,8,1.8,12000,6.2,2500,Caso zona sur,modelo_sur.idf
```

**Validacion previa**: El sistema valida el formato y rangos antes de importar.
**Output**: `{"imported": 30, "errors": 0, "failed_rows": []}`

---

## Command: `simulacion export`

Exporta simulaciones a CSV.

```bash
simulacion export ./output/simulaciones_export.csv
```

**Output**: Archivo CSV con todas las simulaciones y resultados.
