# Quickstart: Carga de Resultados de Simulacion

## Prerequisites

- Python 3.10+
- Clonar repositorio y ubicarse en la raiz
- Instalar dependencias: `pip install click streamlit pandas`

## Setup

```bash
# Inicializar el estudio (una vez)
python -m src.estudio.cli estudio init --nombre "Modelo Optimizacion Termico Chile"
```

## Test Scenarios

### Scenario 1: Carga individual via CLI

```bash
python -m src.estudio.cli simulacion create \
    --tipologia aislada_1piso \
    --zona-termica 5 \
    --u-prom 2.3 \
    --demanda-anual 8500 \
    --peak-demanda 4.5 \
    --gdc 1500 \
    --descripcion "Caso zona central"
```

**Expected output**: JSON con id, tipologia, zona_termica y valores cargados.

### Scenario 2: Carga masiva via CSV

```bash
python -m src.estudio.cli simulacion import tests/fixtures/simulaciones_ejemplo.csv
```

**Expected output**: `{"imported": 36, "errors": 0, "failed_rows": []}`

### Scenario 3: Listar simulaciones

```bash
python -m src.estudio.cli simulacion list
```

**Expected output**: Tabla con todas las simulaciones cargadas.

### Scenario 4: Exportar a CSV

```bash
python -m src.estudio.cli simulacion export ./output/simulaciones.csv
```

**Expected output**: Archivo CSV en `./output/simulaciones.csv`.

### Scenario 5: Interfaz grafica

```bash
streamlit run src/estudio/gui.py
```

**Expected output**: Navegador abre formulario web para gestionar simulaciones.

### Scenario 6: Validacion de rango

```bash
python -m src.estudio.cli simulacion create \
    --tipologia aislada_1piso \
    --zona-termica 9 \
    --u-prom -1 \
    --demanda-anual 8500 \
    --peak-demanda 4.5 \
    --gdc 1500
```

**Expected output**: Error de validacion: "u_prom debe estar entre 0.5 y 5.0 W/m2K".

## Verification

```bash
# Verificar DB compartida
sqlite3 data/acond-termico.db "SELECT COUNT(*) FROM sim_simulacion;"
# Expected: 36

sqlite3 data/acond-termico.db "SELECT * FROM sim_resultado LIMIT 5;"
# Expected: 5 filas con valores validados
```
