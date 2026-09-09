from dataclasses import dataclass
from typing import Optional


@dataclass
class Combustible:
    id: Optional[int] = None
    nombre: str = ""
    unidad_medida: str = ""
    pci: float = 0.0
    pcs: float = 0.0
    rendimiento_transformacion: float = 0.0
    unidades_por_gcal: float = 0.0


@dataclass
class PrecioCombustible:
    id: Optional[int] = None
    combustible_id: int = 0
    region: int = 0
    precio_por_unidad: float = 0.0
    fecha_vigencia: str = ""
    fuente: str = "MANUAL"
    fecha_registro: Optional[str] = None


@dataclass
class TipoTecnologia:
    id: Optional[int] = None
    nombre: str = ""


@dataclass
class EquipoHVAC:
    id: Optional[int] = None
    tipo_tecnologia_id: int = 0
    combustible_id: int = 0
    modelo: str = ""
    potencia_nominal_kw: float = 0.0
    rendimiento_termico_pct: float = 0.0
    costo_adquisicion_clp: float = 0.0
    tasa_consumo: float = 0.0
    unidad_tasa_consumo: str = ""
    costo_instalacion_clp: float = 0.0
    costo_mantencion_anual_clp: float = 0.0
    fuente_datos: str = ""
    url_fuente: Optional[str] = None
    fecha_registro: Optional[str] = None
