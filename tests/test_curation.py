import pytest
import pandas as pd
from src.hvac.curation import (
    cargar_catalogo_completo,
    auditar_anomalias_catalogo,
    generar_muestra_representativa,
    identificar_equipos_terraza,
)


def test_cargar_catalogo_completo():
    df = cargar_catalogo_completo()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 653
    assert "tecnologia" in df.columns
    assert "potencia_nominal_kw" in df.columns
    assert "costo_adquisicion_clp" in df.columns


def test_auditoria_anomalias():
    df = cargar_catalogo_completo()
    df_audit = auditar_anomalias_catalogo(df, iqr_multiplier=1.5)
    assert "estado_auditoria" in df_audit.columns
    assert "motivo_alerta" in df_audit.columns
    assert "es_terraza" in df_audit.columns
    assert "outlier_precio_iqr" in df_audit.columns
    assert df_audit["es_terraza"].sum() > 0


def test_generar_muestra_medoid_estandar():
    df = cargar_catalogo_completo()
    df_arch, df_audit = generar_muestra_representativa(df, metodo="medoid", granularidad="estandar")
    assert isinstance(df_arch, pd.DataFrame)
    # The sample size should be around 60 to 75 equipments
    assert 55 <= len(df_arch) <= 80
    assert "cluster_id" in df_arch.columns
    assert "n_representados" in df_arch.columns
    assert "potencia_nominal_kw" in df_arch.columns
    assert df_arch["es_sintetico"].all() == False


def test_generar_muestra_centroide_sintetico():
    df = cargar_catalogo_completo()
    df_arch, _ = generar_muestra_representativa(df, metodo="centroide", granularidad="estandar")
    assert isinstance(df_arch, pd.DataFrame)
    assert 55 <= len(df_arch) <= 80
    assert df_arch["es_sintetico"].all() == True
    assert df_arch["modelo"].str.startswith("[Equipo Tipo]").all()


def test_exclusion_a_voluntad_terraza():
    df = cargar_catalogo_completo()
    # Without exclusion
    df_con, _ = generar_muestra_representativa(df, excluir_terraza=False)
    # With exclusion
    df_sin, _ = generar_muestra_representativa(df, excluir_terraza=True)
    # The excluded sample should have fewer or equal equipments
    assert len(df_sin) <= len(df_con)
