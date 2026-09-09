import pandas as pd
import json

df = pd.read_csv("data/solotodo_scraped_products.csv")

print("=== RESUMEN GENERAL ===")
print(f"Total productos scrapeados: {len(df)}")
print(f"Productos con precio > 0: {(df['precio_max_c_iva_clp'] > 0).sum()}")
print(f"Productos con múltiples tiendas: {(df['num_tiendas_activas'] > 1).sum()}")
print(f"Productos con 1 tienda: {(df['num_tiendas_activas'] == 1).sum()}")
print(f"Productos sin oferta activa en tiendas (referencia): {(df['num_tiendas_activas'] == 0).sum()}")

print("\n=== DISTRIBUCIÓN POR CATEGORÍA ===")
for cat, grp in df.groupby("categoria_solotodo"):
    print(f"• {cat}: {len(grp)} equipos | Rango: CLP ${grp['precio_max_c_iva_clp'].min():,} - ${grp['precio_max_c_iva_clp'].max():,}")

print("\n=== TOP 10 MARCAS MÁS FRECUENTES ===")
print(df['marca'].value_counts().head(10).to_string())

print("\n=== TOP 10 TIENDAS CON PRECIO MÁS ALTO ===")
# Clean marketplace suffix
tiendas_clean = df['tienda_precio_max'].apply(lambda x: x.split(" (")[0] if isinstance(x, str) else x)
print(tiendas_clean.value_counts().head(10).to_string())

print("\n=== DIFERENCIA DE PRECIOS ENTRE TIENDAS (SPREAD MÁX - MÍN) ===")
multi = df[df['num_tiendas_activas'] > 1].copy()
multi['spread_clp'] = multi['precio_max_c_iva_clp'] - multi['precio_min_c_iva_clp']
multi['spread_pct'] = (multi['spread_clp'] / multi['precio_min_c_iva_clp']) * 100
print(f"Equipos con múltiples tiendas comparadas: {len(multi)}")
print(f"Diferencia promedio de precio (Máx vs Mín): CLP ${multi['spread_clp'].mean():,.0f} ({multi['spread_pct'].mean():.1f}%)")
print(f"Diferencia máxima de precio encontrada: CLP ${multi['spread_clp'].max():,.0f}")

print("\nTop 5 casos con mayor variación de precio entre tiendas:")
for _, row in multi.sort_values(by='spread_clp', ascending=False).head(5).iterrows():
    print(f"  • {row['marca']} {row['modelo']} ({row['tipo']}):")
    print(f"      Máx: CLP ${row['precio_max_c_iva_clp']:,} ({row['tienda_precio_max']})")
    print(f"      Mín: CLP ${row['precio_min_c_iva_clp']:,} ({row['tienda_precio_min']})")
    print(f"      Diferencia: CLP ${row['spread_clp']:,} (+{row['spread_pct']:.1f}%)")

