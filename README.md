# Climatización Residencial: Evaluación Energética, CAE y Optimización HVAC Chile 2026

Plataforma de evaluación tecno-económica de alternativas de calefacción residencial y optimización del Costo Anual Equivalente (CAE) en viviendas sociales de Chile, abarcando las 9 Zonas Térmicas reglamentarias (Zonas A a I).

## 🚀 Características Principales

1. **📦 Catálogo HVAC 2026:**
   - 653 modelos actualizados (Splits Inverter, estufas a pellet, leña, parafina/kerosene, gas licuado, gas natural y eléctricas).
   - Precios de mercado más altos vigentes c/IVA (scraping SoloTodo 2026) con enlaces a distribuidores y especificaciones técnicas completas (potencia nominal, rendimiento SEC, COP modo calor).

2. **⚡ Precios de Energía por Zona Térmica (Tabla 2):**
   - 41 cotizaciones comerciales detalladas en 9 ciudades de referencia (Antofagasta, Calama, Valparaíso, Santiago, Concepción, Temuco, Puerto Montt, Los Andes, Punta Arenas).
   - Comparativas visuales de costo normalizado por energía útil ($/kWh_t) y por unidad física base ($/kg, $/L, $/m³, $/kWh).

3. **📊 Matriz de Elección y Evaluación CAE por Gcal:**
   - Cálculo del Factor de Recuperación de Capital (FRC) con tasa de descuento social/familiar (r).
   - Costos fijos anualizados (inversión amortizada, instalación y mantención preventiva).
   - Costos variables por Gcal útil y kWh térmico según precios locales y poderes caloríficos (PCI).
   - Indicador LCOH (Levelized Cost of Heat) en CLP/kWh_t y en UF/kWh_t.
   - Escalado de potencia según demanda peak de la vivienda ($N_{\text{equipos}} = \lceil P_{\text{peak}} / P_{\text{nominal}} \rceil$).

4. **📐 Simulación Térmica Dinámica (Fase 1):**
   - Demanda térmica anual y peak por tipología de vivienda y zona climática.

5. **⚙️ Optimizador MILP (Fase 3):**
   - Motor de programación lineal entera mixta con PuLP / CBC para selección óptima de equipos minimizando el CAE.

6. **📈 Modelo Econométrico (Fase 4):**
   - Estimación OLS y 8 tests diagnósticos de especificación.

## 💻 Ejecución Local

```bash
# Clonar repositorio
git clone https://github.com/felipe-evs/acond-termico.git
cd acond-termico

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación Streamlit
streamlit run app.py
```
