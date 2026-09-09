import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ModeloEconometrico:
    id: Optional[int] = None
    formula: str = ""
    R2: Optional[float] = None
    R2_ajustado: Optional[float] = None
    ECM: Optional[float] = None
    F_statistic: Optional[float] = None
    F_pvalue: Optional[float] = None
    n_observaciones: int = 0
    timestamp: Optional[str] = None


@dataclass
class CoeficienteRegresion:
    id: Optional[int] = None
    modelo_id: int = 0
    variable_nombre: str = ""
    beta: float = 0.0
    error_std: Optional[float] = None
    t_statistic: Optional[float] = None
    pvalue: Optional[float] = None
    VIF: Optional[float] = None


@dataclass
class TestDiagnostico:
    id: Optional[int] = None
    modelo_id: int = 0
    test_nombre: str = ""
    estadistico: Optional[float] = None
    pvalue: Optional[float] = None
    resultado: str = ""


def leer_csv_resultados(archivo):
    df = pd.read_csv(archivo)
    return df


def preparar_datos(df):
    df = df.copy()
    df = pd.get_dummies(df, columns=["zona_termica", "tipologia"], drop_first=True, prefix=["zona", "tip"])
    for col in df.select_dtypes(include=[bool]).columns:
        df[col] = df[col].astype(int)
    return df
