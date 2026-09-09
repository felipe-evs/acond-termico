# CSV Format Contract: Import/Export Equipos

## Import Format (equipos)

```csv
tipo_tecnologia,combustible,modelo,potencia_nominal_kw,rendimiento_termico_pct,costo_adquisicion_clp,tasa_consumo,unidad_tasa_consumo,costo_instalacion_clp,costo_mantencion_anual_clp,fuente_datos,url_fuente
split_inverter, electricidad,"Midea Xtreme 12000",3.5,320,450000,1.2,kWh/h,0,0,Sodimac,https://...
estufa_lena,lena,"Chilena Nórdica",8.0,75,250000,2.0,kg/h,50000,30000,"Tienda Especializada",
```

## Import Format (precios CNE)

```csv
combustible,region,precio_por_unidad,fecha_vigencia,fuente
parafina,13,1200,2026-07-01,MANUAL
gas_licuado,13,850,2026-07-01,CNE_CSV
```

## Export Format

Misma estructura que el import format. Archivo: `catalogo_hvac_YYYY-MM-DD.csv`
