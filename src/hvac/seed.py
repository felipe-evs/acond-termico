from src.hvac.constants import TIPOS_COMBUSTIBLE, TIPOS_TECNOLOGIA
from src.hvac.repository import CombustibleRepository, TipoTecnologiaRepository

COMBUSTIBLES_SEED = {
    "parafina": {"unidad_medida": "litro", "pci": 8200, "pcs": 8800, "rendimiento_transformacion": 85, "unidades_por_gcal": 0.12},
    "gas_licuado": {"unidad_medida": "kg", "pci": 11000, "pcs": 11800, "rendimiento_transformacion": 90, "unidades_por_gcal": 0.09},
    "gas_natural": {"unidad_medida": "m3", "pci": 9300, "pcs": 10300, "rendimiento_transformacion": 92, "unidades_por_gcal": 0.11},
    "pellet": {"unidad_medida": "kg", "pci": 4500, "pcs": 4800, "rendimiento_transformacion": 85, "unidades_por_gcal": 0.22},
    "lena": {"unidad_medida": "kg", "pci": 3500, "pcs": 3800, "rendimiento_transformacion": 70, "unidades_por_gcal": 0.28},
    "electricidad": {"unidad_medida": "kWh", "pci": 1, "pcs": 1, "rendimiento_transformacion": 100, "unidades_por_gcal": 1163},
}


def seed_combustibles():
    for nombre, params in COMBUSTIBLES_SEED.items():
        CombustibleRepository.create({
            "nombre": nombre,
            **params,
        })


def seed_tipos_tecnologia():
    for t in TIPOS_TECNOLOGIA:
        TipoTecnologiaRepository.create(t)


def run_seed():
    seed_combustibles()
    seed_tipos_tecnologia()
