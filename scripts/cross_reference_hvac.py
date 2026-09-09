import pandas as pd
import re

df_scraped = pd.read_csv("data/solotodo_scraped_products.csv")
df_hist = pd.read_csv("data_catalogo_equipos_hvac_normalizado.csv")

def parse_price(val):
    if pd.isna(val):
        return 0
    s = str(val).split(",")[0]
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else 0

def clean_alphanumeric(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r"[^a-z0-9]", "", text.lower())

def extract_model_code(model_str):
    """Extracts distinctive model alphanumeric tokens like 'ks27', 'ml25', 'ff55', 'omni230'."""
    s = clean_alphanumeric(model_str)
    return s

matches = []

for idx, hrow in df_hist.iterrows():
    h_brand = str(hrow["Marca"]).strip()
    h_model = str(hrow["Modelo"]).strip()
    h_tipo = str(hrow["Tipo"]).strip()
    h_price = parse_price(hrow["Precio_Adquisicion_IVA"])
    h_brand_clean = clean_alphanumeric(h_brand)
    h_model_clean = extract_model_code(h_model)

    best_match = None

    for _, srow in df_scraped.iterrows():
        s_brand_clean = clean_alphanumeric(srow["marca"])
        s_model_clean = clean_alphanumeric(srow["modelo"])
        s_name_clean = clean_alphanumeric(srow["nombre_completo"])

        # Must match brand
        if h_brand_clean not in s_brand_clean and s_brand_clean not in h_brand_clean:
            continue

        # Check model code containment
        # e.g. 'ks27' in 'ks27rojo', 'ff55' in 'ff55', 'omni230' in 'omni230'
        if len(h_model_clean) >= 3 and (h_model_clean == s_model_clean or h_model_clean in s_name_clean):
            # prioritize exact model code match
            if best_match is None or len(s_model_clean) < len(clean_alphanumeric(best_match["modelo"])):
                best_match = srow

    if best_match is not None:
        p_max = int(best_match["precio_max_c_iva_clp"])
        p_min = int(best_match["precio_min_c_iva_clp"])
        diff_clp = p_max - h_price
        diff_pct = (diff_clp / h_price) * 100 if h_price > 0 else 0

        matches.append({
            "item_historico": idx + 1,
            "marca": h_brand,
            "modelo_historico": h_model,
            "nombre_solotodo": best_match["nombre_completo"],
            "tipo_normalizado": best_match["tipo"],
            "combustible": best_match["combustible"],
            "precio_historico_clp": h_price,
            "precio_solotodo_max_clp": p_max,
            "precio_solotodo_min_clp": p_min,
            "tienda_max": best_match["tienda_precio_max"],
            "num_tiendas": best_match["num_tiendas_activas"],
            "variacion_precio_clp": diff_clp,
            "variacion_precio_pct": round(diff_pct, 1),
            "url_solotodo": best_match["url_solotodo"]
        })

df_res = pd.DataFrame(matches)
df_res.to_csv("data/comparacion_historico_vs_solotodo.csv", index=False)

print(f"=== COMPARACIÓN MODELOS HISTÓRICOS VS SOLOTODO 2026 ===")
print(f"Modelos históricos identificados con equivalente exacto/vigente en SoloTodo: {len(df_res)}")
print("\nListado detallado de equivalencias encontradas:")
for _, r in df_res.iterrows():
    print(f"#{r['item_historico']:02d} {r['marca']} {r['modelo_historico']} -> {r['nombre_solotodo']}")
    print(f"    Histórico: CLP ${r['precio_historico_clp']:,} | SoloTodo Máx: CLP ${r['precio_solotodo_max_clp']:,} ({r['tienda_max']}) | Mín: CLP ${r['precio_solotodo_min_clp']:,} | Var Máx: {r['variacion_precio_pct']:+.1f}%")

