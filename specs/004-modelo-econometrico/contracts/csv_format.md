# CSV Format Contract: Modelo Econometrico

## Export Format (coeficientes)

```csv
variable_nombre,beta,error_std,t_statistic,pvalue,VIF
const,125000,15000,8.33,0.000,0
U_prom,2.3,0.5,4.6,0.001,2.1
GDC,45,12,3.75,0.003,3.2
demanda_anual_kwh,0.8,0.2,4.0,0.002,2.8
...
```

## Export Format (tests de diagnostico)

```csv
test_nombre,estadistico,pvalue,resultado
JarqueBera,1.2,0.55,pasa
White,8.5,0.75,pasa
DurbinWatson,1.95,0.40,pasa
RamseyRESET,1.1,0.35,pasa
```

## Export Format (what-if)

```csv
tipo,parametros_variados,valores,resultado_Y_costo
parametrico,Precio gas,+50%,425000
critico,Desabastecimiento,gas no disponible,550000
multifactorial,Precio gas+10% y GDC+20%,"+10%,+20%",380000
```
