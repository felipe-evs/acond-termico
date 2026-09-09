from dataclasses import dataclass
from typing import Optional


@dataclass
class Estudio:
    id: Optional[int] = None
    nombre: str = ""
    descripcion: Optional[str] = None
    fecha_creacion: Optional[str] = None


@dataclass
class Simulacion:
    id: Optional[int] = None
    estudio_id: int = 0
    tipologia: str = ""
    zona_termica: int = 0
    descripcion: Optional[str] = None
    archivo_modelo: Optional[str] = None
    fecha_carga: Optional[str] = None


@dataclass
class ResultadoSimulacion:
    id: Optional[int] = None
    simulacion_id: int = 0
    u_prom: float = 0.0
    demanda_anual_kwh: float = 0.0
    peak_demanda_kw: float = 0.0
    gdc: float = 0.0
