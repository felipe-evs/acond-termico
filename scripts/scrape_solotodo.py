#!/usr/bin/env python3
"""
SoloTodo HVAC & Heating Scraper (V2 - Currency & Country Normalized)
===================================================================
Scrapes heating systems and air conditioners from www.solotodo.cl across:
1. https://www.solotodo.cl/estufas?ordering=offer_price_usd&page=1&page_size=200 (Cat 47)
2. https://www.solotodo.cl/estufas?ordering=offer_price_usd&page=2&page_size=200 (Cat 47)
3. https://www.solotodo.cl/estufas?ordering=offer_price_usd&page=3&page_size=200 (Cat 47)
4. https://www.solotodo.cl/aires_acondicionados_portatiles?page_size=200 (Cat 417)
5. https://www.solotodo.cl/aires_acondicionados_split?page_size=200 (Cat 43)

Key Features:
- Direct REST API integration with api.solotodo.com for fast, high-reliability extraction.
- Prioritizes Chilean stores (country_id == 1, CLP) with official IVA list prices.
- Converts foreign currencies (USD, GTQ, etc.) to CLP using live exchange rates from SoloTodo.
- Strict selection of the HIGHEST retail price (c/IVA) across stores, capturing store name and direct link.
- Extracts all technical specifications for the HVAC database:
  Marca, Modelo, Tipo Armonizado, Combustible, Consumo Bruto, Rendimiento (η), COP Calor,
  Poder Calorífico, Rango Calefacción, Precio Adquisición c/IVA, Tienda Precio Máximo,
  Costo Instalación c/IVA, Mantención Anual c/IVA, Otros (SEC QR, Wi-Fi, Inverter, Logística Zonas Extremas).
- Exports results to CSV and JSON.
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("solotodo_scraper")

BASE_API_URL = "https://api.solotodo.com"
BASE_WEB_URL = "https://www.solotodo.cl"

# Target endpoints corresponding to the user's requested URLs
TARGET_URLS = [
    {
        "category_id": 47,
        "category_name": "Estufas",
        "page": 1,
        "page_size": 200,
        "ordering": "offer_price_usd",
        "original_url": "https://www.solotodo.cl/estufas?ordering=offer_price_usd&page=1&page_size=200",
    },
    {
        "category_id": 47,
        "category_name": "Estufas",
        "page": 2,
        "page_size": 200,
        "ordering": "offer_price_usd",
        "original_url": "https://www.solotodo.cl/estufas?ordering=offer_price_usd&page=2&page_size=200",
    },
    {
        "category_id": 47,
        "category_name": "Estufas",
        "page": 3,
        "page_size": 200,
        "ordering": "offer_price_usd",
        "original_url": "https://www.solotodo.cl/estufas?ordering=offer_price_usd&page=3&page_size=200",
    },
    {
        "category_id": 417,
        "category_name": "Aire Acondicionado Portátil",
        "page": 1,
        "page_size": 200,
        "ordering": None,
        "original_url": "https://www.solotodo.cl/aires_acondicionados_portatiles?page_size=200",
    },
    {
        "category_id": 43,
        "category_name": "Aire Acondicionado Split",
        "page": 1,
        "page_size": 200,
        "ordering": None,
        "original_url": "https://www.solotodo.cl/aires_acondicionados_split?page_size=200",
    },
]


def create_session() -> requests.Session:
    """Creates a requests session with retries and headers."""
    session = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=25, pool_maxsize=25)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
    )
    return session


def fetch_currencies(session: requests.Session) -> Tuple[Dict[int, Dict[str, Any]], float]:
    """Fetches currencies and calculates conversion rate to CLP."""
    logger.info("Fetching currency exchange rates...")
    url = f"{BASE_API_URL}/currencies/"
    try:
        resp = session.get(url, timeout=12)
        resp.raise_for_status()
        cur_list = resp.json()
        cur_map = {c["id"]: c for c in cur_list}
        clp_rate = float(cur_map.get(1, {}).get("exchange_rate", 934.39))
        logger.info(f"CLP exchange rate: {clp_rate} CLP per USD")
        return cur_map, clp_rate
    except Exception as e:
        logger.warning(f"Error fetching currencies: {e}. Using fallback 935 CLP/USD.")
        return {}, 935.0


def convert_to_clp(amount: float, currency_id: int, cur_map: Dict[int, Dict[str, Any]], clp_rate: float) -> float:
    """Converts any currency amount to CLP."""
    if currency_id == 1:
        return float(amount)
    cur = cur_map.get(currency_id)
    if not cur:
        return float(amount) * clp_rate
    # exchange_rate is units of currency per 1 USD
    rate_to_usd = float(cur.get("exchange_rate", 1.0))
    if rate_to_usd <= 0:
        return float(amount)
    amount_usd = float(amount) / rate_to_usd
    return amount_usd * clp_rate


def fetch_stores(session: requests.Session) -> Dict[int, Dict[str, Any]]:
    """Fetches all stores to map store_id -> store dict."""
    logger.info("Fetching store list from SoloTodo API...")
    url = f"{BASE_API_URL}/stores/"
    try:
        resp = session.get(url, timeout=12)
        resp.raise_for_status()
        stores = resp.json()
        store_map = {s["id"]: s for s in stores}
        logger.info(f"Loaded {len(store_map)} stores successfully.")
        return store_map
    except Exception as e:
        logger.warning(f"Failed to fetch store list: {e}. Using empty mapping.")
        return {}


def fetch_browse_products(
    session: requests.Session, target: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Fetches products from a single browse page."""
    params = {
        "categories": target["category_id"],
        "page": target["page"],
        "page_size": target["page_size"],
    }
    if target.get("ordering"):
        params["ordering"] = target["ordering"]

    url = f"{BASE_API_URL}/products/browse/"
    logger.info(
        f"Fetching {target['category_name']} (Page {target['page']}, size {target['page_size']})..."
    )
    try:
        resp = session.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        logger.info(
            f"  -> Got {len(results)} products for {target['category_name']} (Page {target['page']}) [Total in category: {data.get('count')}]"
        )
        return results
    except Exception as e:
        logger.error(f"Error fetching {target['original_url']}: {e}")
        return []


def fetch_product_entities(
    session: requests.Session, product_id: int
) -> List[Dict[str, Any]]:
    """Fetches all store entities for a specific product ID."""
    url = f"{BASE_API_URL}/products/{product_id}/entities/"
    try:
        resp = session.get(url, timeout=12)
        if resp.status_code == 200:
            return resp.json()
        else:
            return []
    except Exception:
        return []


def harmonize_system_type(
    category_id: int, specs: Dict[str, Any], product_name: str
) -> Tuple[str, str]:
    """
    Harmonizes system type and fuel according to the technical definitions
    and reference classifications in the project documents.
    Returns: (tipo_armonizado, combustible)
    """
    name_lower = product_name.lower()

    if category_id == 43:
        # Split AC
        inverter = specs.get("has_inverter_technology", False)
        tipo = (
            "Aire Acondicionado Split (Bomba de Calor Inverter)"
            if inverter
            else "Aire Acondicionado Split (Bomba de Calor)"
        )
        return tipo, "Electricidad"

    if category_id == 417:
        # Portable AC
        return "Aire Acondicionado Portátil", "Electricidad"

    # Category 47: Estufas
    sh_type = specs.get("sh_type_name", "")
    energy_source = specs.get("sh_type_energy_source_name", "")

    # Harmonize Fuel
    fuel = "Electricidad"
    if energy_source == "Biomasa" or "pellet" in sh_type.lower():
        fuel = "Pellet"
    elif energy_source == "Leña" or "leña" in sh_type.lower():
        fuel = "Leña"
    elif energy_source == "Parafina" or "parafina" in sh_type.lower() or "kerosene" in name_lower:
        fuel = "Kerosene / Parafina"
    elif energy_source == "Gas Natural" or "gas natural" in sh_type.lower():
        fuel = "Gas Natural (GN)"
    elif energy_source == "Gas" or "gas" in sh_type.lower() or "glp" in name_lower:
        fuel = "Gas Licuado (GLP)"
    elif energy_source == "Electricidad":
        fuel = "Electricidad"

    # Harmonize Type
    if "pellet" in sh_type.lower():
        tipo = "Estufa a Pellet"
    elif "leña" in sh_type.lower():
        tipo = "Estufa a Leña Combustión Lenta"
    elif "parafina" in sh_type.lower() or "kerosene" in name_lower:
        # Distinguish laser (electronic) vs mecha vs tiro forzado
        if "ff" in name_lower or "tiro forzado" in name_lower or specs.get("nominal_thermal_power", 0) > 4000:
            tipo = "Estufa Kerosene Láser Tiro Forzado"
        elif any(k in name_lower for k in ["laser", "láser", "lc", "fhk", "fh", "electrónica", "electronica"]):
            tipo = "Estufa Kerosene Láser (Electrónica)"
        else:
            tipo = "Estufa Kerosene Mecha (Cámara Conv/Rad)"
    elif "gas natural" in sh_type.lower():
        tipo = "Calefactor Gas Tiro Balanceado (Hermético)"
    elif "gas" in sh_type.lower():
        if "patio" in sh_type.lower() or "terraza" in sh_type.lower() or "exterior" in name_lower:
            tipo = "Calefactor Exterior Terraza / Patio (Gas GLP)"
        elif "catalit" in name_lower:
            tipo = "Estufa Gas Catalítica"
        elif "blue flame" in name_lower or "llama azul" in name_lower:
            tipo = "Estufa Gas Convectiva (Blue Flame)"
        else:
            tipo = "Estufa Gas Radiante Infrarroja"
    elif "convector" in sh_type.lower() or "panel" in sh_type.lower():
        tipo = "Convector Eléctrico"
    elif "termoventilador" in sh_type.lower():
        tipo = "Termoventilador Eléctrico"
    elif "oleo" in sh_type.lower() or "óleo" in sh_type.lower() or "aceite" in name_lower:
        tipo = "Calefactor Óleo-eléctrico"
    elif "cuarzo" in sh_type.lower():
        tipo = "Calefactor Eléctrico a Cuarzo"
    elif "halógen" in sh_type.lower() or "halogen" in sh_type.lower():
        tipo = "Estufa Eléctrica Halógena"
    elif "infrarrojo" in sh_type.lower() or "carbono" in sh_type.lower():
        tipo = "Calefactor Eléctrico Infrarrojo"
    elif "cerámico" in sh_type.lower() or "ptc" in sh_type.lower():
        tipo = "Calefactor Eléctrico Cerámico / PTC"
    elif "chimenea" in sh_type.lower():
        tipo = "Chimenea Eléctrica Decorativa"
    elif "radiador" in sh_type.lower():
        tipo = "Radiador Eléctrico"
    else:
        tipo = sh_type if sh_type else "Calefactor Eléctrico"

    return tipo, fuel


def determine_consumption_raw(specs: Dict[str, Any], fuel: str) -> str:
    """Formats raw consumption preserving all manufacturer units."""
    parts = []
    g_hr = specs.get("consumption_g_hr")
    if g_hr and float(g_hr) > 0:
        parts.append(f"{g_hr} g/hora")

    ml_hr = specs.get("consumption_ml_hr")
    if ml_hr and float(ml_hr) > 0:
        parts.append(f"{ml_hr} ml/hora")

    cooling_cons = specs.get("cooling_consumption")
    if cooling_cons and float(cooling_cons) > 0:
        parts.append(f"{cooling_cons} kWh/mes (Norma SEC)")

    power_w = specs.get("power_w")
    if power_w and float(power_w) > 0 and fuel == "Electricidad":
        parts.append(f"{float(power_w)/1000.0:.2f} kWh/hora ({power_w} W)")

    nom_power = specs.get("nominal_thermal_power")
    if nom_power and float(nom_power) > 0:
        parts.append(f"{nom_power} kW térmico")

    if not parts:
        if fuel == "Electricidad":
            btu = specs.get("btu_power") or specs.get("cooling_power_btu_value")
            if btu:
                parts.append(f"Capacidad {btu} BTU/h")
            else:
                parts.append("Según potencia eléctrica conectada")
        elif fuel == "Pellet":
            parts.append("0,6 - 1,8 kg/hora (estándar)")
        elif fuel == "Leña":
            parts.append("1,5 - 3,0 kg/hora (estándar)")
        elif fuel == "Gas Licuado (GLP)":
            parts.append("120 - 320 g/hora (estándar)")
        elif fuel == "Kerosene / Parafina":
            parts.append("0,15 - 0,35 lt/hora (estándar)")
        else:
            parts.append("-")

    return " / ".join(parts)


def determine_efficiency_and_cop(
    tipo: str, fuel: str, specs: Dict[str, Any], category_id: int
) -> Tuple[str, str]:
    """
    Computes Rendimiento (η) and COP (calor):
    - All electric resistive = 1.0 (100%)
    - Heat pump / Split AC = '-' for Rendimiento, COP for Heating Mode.
    - Combustion = factor η (0.65 - 0.95), COP = '-'
    """
    if category_id == 43:
        # Split AC
        rendimiento = "-"
        iee = specs.get("indice_eficiencia_energetica")
        heat_pwr = specs.get("heating_power", 0)
        eff_class = specs.get("heating_energy_efficiency_cl_name", "")

        if iee and float(iee) > 0:
            cop = f"{float(iee):.2f}"
            if eff_class and eff_class != "Desconocido":
                cop += f" (Clase {eff_class})"
        elif heat_pwr and float(heat_pwr) > 0:
            cop = "3.21 (Clase A Inverter)"
        else:
            cop = "3.00 (Inverter Modo Calor)"
        return rendimiento, cop

    if category_id == 417:
        # Portable AC
        rendimiento = "-"
        cop = "2.60 (Portátil Calor)" if "calor" in specs.get("commercial_model", "").lower() else "-"
        return rendimiento, cop

    # Non-AC heaters
    cop = "-"
    if fuel == "Electricidad":
        rendimiento = "1,0 (100%)"
    elif fuel == "Pellet":
        eff_pct = specs.get("energy_efficiency_percentage")
        if eff_pct and float(eff_pct) > 0:
            rendimiento = f"{float(eff_pct)/100.0:.3f} ({eff_pct}%)"
        else:
            rendimiento = "0,850 (85%)"
    elif fuel == "Leña":
        eff_pct = specs.get("energy_efficiency_percentage")
        if eff_pct and float(eff_pct) > 0:
            rendimiento = f"{float(eff_pct)/100.0:.3f} ({eff_pct}%)"
        else:
            rendimiento = "0,650 (65%)"
    elif "tiro forzado" in tipo.lower() or "tiro balanceado" in tipo.lower():
        rendimiento = "0,927 (92,7%)"
    elif fuel in ["Gas Licuado (GLP)", "Gas Natural (GN)", "Kerosene / Parafina"]:
        rendimiento = "0,800 (80%)"
    else:
        rendimiento = "1,0 (100%)"

    return rendimiento, cop


def determine_thermal_power_raw(specs: Dict[str, Any], category_id: int) -> str:
    """Formats raw calorific power combining all available units (W, kcal/h, BTU/h, kW)."""
    parts = []
    p_w = specs.get("power_w")
    if p_w and float(p_w) > 0:
        parts.append(f"{p_w} W")

    p_kcal = specs.get("power_kcal_hr")
    if p_kcal and float(p_kcal) > 0:
        parts.append(f"{p_kcal} Kcal/h")

    p_btu = specs.get("power_btu_hr") or specs.get("btu_power") or specs.get("cooling_power_btu_value")
    if p_btu and float(p_btu) > 0:
        parts.append(f"{p_btu} BTU/h")

    heat_pwr = specs.get("heating_power")
    if heat_pwr and float(heat_pwr) > 0:
        parts.append(f"{heat_pwr} W (Calefacción)")

    nom_pwr = specs.get("nominal_thermal_power")
    if nom_pwr and float(nom_pwr) > 0:
        parts.append(f"{nom_pwr} kW")

    if not parts:
        return "-"
    return " / ".join(parts)


def determine_heating_range(specs: Dict[str, Any]) -> str:
    """Extracts heating range in m2 or m3."""
    m2 = specs.get("heating_range_m2") or specs.get("coverage")
    m3 = specs.get("heating_range_m3")

    parts = []
    if m2 and float(m2) > 0:
        parts.append(f"{m2} m2")
    if m3 and float(m3) > 0:
        parts.append(f"{m3} m3")

    if not parts:
        return "No especificado"
    return " / ".join(parts)


def determine_installation_and_maintenance(
    tipo: str, fuel: str, category_id: int
) -> Tuple[str, str]:
    """Assigns standard benchmark installation and annual maintenance costs."""
    if category_id == 43:
        # Split AC
        return (
            "$ 100.000 (Técnico SEC / vacío cañerías)",
            "$ 40.000 / año (Filtros y presiones)",
        )

    if category_id == 417:
        # Portable AC
        return (
            "$ 0 (Portátil / Enchufable)",
            "$ 25.000 / año (Limpieza filtros)",
        )

    # Cat 47
    if "pellet" in tipo.lower():
        return (
            "$ 120.000 (Kit cañones inox / pasamuros)",
            "$ 45.000 / año (Deshollinado / crisol)",
        )
    if "leña" in tipo.lower():
        return (
            "$ 120.000 (Kit cañones / sellado techumbre)",
            "$ 30.000 / año (Deshollinado)",
        )
    if "tiro forzado" in tipo.lower() or "tiro balanceado" in tipo.lower():
        return (
            "$ 75.000 (Perforación mural hermética)",
            "$ 35.000 / año (Sensores y quemador)",
        )
    if fuel == "Kerosene / Parafina":
        if "láser" in tipo.lower() or "laser" in tipo.lower():
            return (
                "$ 0 (Portátil)",
                "$ 35.000 / año (Limpieza sensores)",
            )
        else:
            return (
                "$ 0 (Portátil)",
                "$ 25.000 / 2 años (Cambio mecha)",
            )
    if fuel == "Gas Licuado (GLP)":
        return (
            "$ 0 (Portátil)",
            "$ 20.000 / 2 años (Regulador y flexible)",
        )
    if fuel == "Electricidad":
        return (
            "$ 0 (Enchufable 220V)",
            "$ 0 (Sin mantención periódica)",
        )

    return ("$ 0 (Portátil)", "$ 0")


def determine_other_details(
    specs: Dict[str, Any], tipo: str, fuel: str, category_id: int
) -> str:
    """Builds extra notes including SEC approval, logistics, and special features."""
    notes = []

    sec_qr = specs.get("sec_qr_codes")
    if sec_qr:
        notes.append(f"Certificación SEC QR: {sec_qr}")

    weight = specs.get("weight")
    if weight and float(weight) > 0:
        notes.append(f"Peso: {float(weight)/1000.0:.1f} kg")

    dims = specs.get("pretty_dimensions")
    if dims:
        clean_dims = str(dims).rstrip(" mm").strip() + " mm"
        notes.append(f"Dimensiones: {clean_dims}")

    tank = specs.get("tank_capacity")
    if tank and float(tank) > 0:
        notes.append(f"Capacidad Estanque/Tolva: {tank} L/kg")

    if specs.get("has_inverter_technology"):
        notes.append("Tecnología Inverter")

    if specs.get("has_wifi"):
        notes.append("Control Wi-Fi")

    # Extreme zones & logistics
    if fuel in ["Pellet", "Leña"]:
        notes.append(
            "Flete volumen pesado a zonas extremas (+15-25% H/I). Requiere leña seca (<25% hum) o pellet certificado."
        )
    elif "tiro forzado" in tipo.lower() or "tiro balanceado" in tipo.lower():
        notes.append(
            "Perforación exterior obligatoria. No apto >1500 msnm sin ajuste técnico."
        )
    elif category_id == 43:
        notes.append(
            "Apto zonas templadas/frías. En Zona H/I verificar curvas de descongelamiento (defrost) en subcero."
        )
    elif fuel == "Electricidad":
        notes.append("Enchufable 220V directo. No requiere obras ni ductos.")
    elif fuel == "Kerosene / Parafina":
        notes.append(
            "En Zona H (>1500 msnm) requiere modelo de alta altitud por baja presión de O2."
        )

    return " | ".join(notes) if notes else "-"


def process_product(
    item: Dict[str, Any],
    target: Dict[str, Any],
    store_map: Dict[int, Dict[str, Any]],
    cur_map: Dict[int, Dict[str, Any]],
    clp_rate: float,
    session: requests.Session,
) -> Dict[str, Any]:
    """Processes a single product entry, fetches entities, and finds the highest store price."""
    product_entry = item["product_entries"][0]
    product = product_entry["product"]
    product_id = product["id"]
    product_name = product.get("name", "").strip()
    specs = product.get("specs", {})
    metadata = product_entry.get("metadata", {})

    category_id = target["category_id"]
    category_name = target["category_name"]

    # Fetch store entities
    entities = fetch_product_entities(session, product_id)

    # Filter active entities
    active_entities = [
        e
        for e in entities
        if e.get("active_registry") and e["active_registry"].get("is_available")
    ]

    # Filter by condition (prefer NewCondition)
    new_entities = [
        e
        for e in active_entities
        if "newcondition" in str(e.get("condition", "")).lower()
        and "open box" not in e.get("name", "").lower()
        and "reacondicionado" not in e.get("name", "").lower()
    ]
    candidate_entities = new_entities if new_entities else active_entities

    # Separate Chilean offers (country_id == 1 or currency_id == 1)
    chilean_entities = [
        e
        for e in candidate_entities
        if e.get("currency_id") == 1
        or (store_map.get(e.get("store_id") or e.get("store"), {}).get("country_id") == 1)
    ]

    # If Chilean entities exist, use them exclusively
    selected_entities = chilean_entities if chilean_entities else candidate_entities

    precio_max_clp = 0.0
    precio_min_clp = 0.0
    tienda_max = "Sin stock activo"
    tienda_min = "Sin stock activo"
    url_tienda_max = ""
    oferta_en_tienda_max_clp = 0.0
    num_tiendas = len(selected_entities)
    tiendas_resumen_list = []

    if selected_entities:
        parsed_offers = []
        for e in selected_entities:
            reg = e["active_registry"]
            norm_str = reg.get("normal_price")
            off_str = reg.get("offer_price")
            cur_id = e.get("currency_id", 1)

            raw_norm = float(norm_str) if norm_str else 0.0
            raw_off = float(off_str) if off_str else raw_norm
            if raw_norm == 0.0 and raw_off > 0.0:
                raw_norm = raw_off

            # Convert to CLP if needed
            norm_clp = convert_to_clp(raw_norm, cur_id, cur_map, clp_rate)
            off_clp = convert_to_clp(raw_off, cur_id, cur_map, clp_rate)

            sid = e.get("store_id") or e.get("store")
            store_obj = store_map.get(sid, {})
            st_name = store_obj.get("name", f"Tienda {sid}")
            if cur_id != 1:
                cur_code = cur_map.get(cur_id, {}).get("iso_code", "EXT")
                st_name += f" ({cur_code} conv)"

            seller = e.get("seller")
            if seller:
                st_name += f" ({seller})"

            ext_url = e.get("external_url", "")
            parsed_offers.append(
                {
                    "normal_price": norm_clp,
                    "offer_price": off_clp,
                    "store_name": st_name,
                    "url": ext_url,
                    "condition": e.get("condition", ""),
                }
            )
            tiendas_resumen_list.append(f"{st_name}: ${norm_clp:,.0f}")

        # Sort by normal price descending to find the HIGHEST price
        parsed_offers.sort(key=lambda x: x["normal_price"], reverse=True)
        best_offer = parsed_offers[0]
        min_offer = parsed_offers[-1]

        precio_max_clp = best_offer["normal_price"]
        oferta_en_tienda_max_clp = best_offer["offer_price"]
        tienda_max = best_offer["store_name"]
        url_tienda_max = best_offer["url"]

        precio_min_clp = min_offer["normal_price"]
        tienda_min = min_offer["store_name"]
    else:
        # Fallback to browse metadata if no active store entities found
        prices = metadata.get("prices_per_currency", [])
        if prices:
            p_curr = prices[0]
            cur_id = p_curr.get("currency_id", 1)
            raw_p = float(p_curr.get("normal_price", 0))
            raw_off = float(p_curr.get("offer_price", 0))
            precio_max_clp = convert_to_clp(raw_p, cur_id, cur_map, clp_rate)
            oferta_en_tienda_max_clp = convert_to_clp(raw_off, cur_id, cur_map, clp_rate)
            tienda_max = "Precio referencia SoloTodo"
            tienda_min = tienda_max
            precio_min_clp = precio_max_clp
        elif metadata.get("normal_price_usd"):
            precio_max_clp = round(float(metadata["normal_price_usd"]) * clp_rate)
            tienda_max = "Referencia USD SoloTodo"

    # Harmonize specifications
    marca = (
        specs.get("brand_name")
        or specs.get("brand_brand_name")
        or specs.get("brand_unicode")
        or ""
    ).strip()
    if not marca and " " in product_name:
        marca = product_name.split()[0]

    modelo = (specs.get("commercial_model") or product_name).strip()
    tipo_armonizado, combustible = harmonize_system_type(
        category_id, specs, product_name
    )
    consumo_bruto = determine_consumption_raw(specs, combustible)
    rendimiento_n, cop_calor = determine_efficiency_and_cop(
        tipo_armonizado, combustible, specs, category_id
    )
    poder_calorifico = determine_thermal_power_raw(specs, category_id)
    rango_calefaccion = determine_heating_range(specs)
    costo_instalacion, costo_mantencion = determine_installation_and_maintenance(
        tipo_armonizado, combustible, category_id
    )
    otros = determine_other_details(
        specs, tipo_armonizado, combustible, category_id
    )

    url_solotodo = f"{BASE_WEB_URL}/products/{product_id}"

    return {
        "id_solotodo": product_id,
        "categoria_solotodo": category_name,
        "marca": marca,
        "modelo": modelo,
        "nombre_completo": product_name,
        "tipo": tipo_armonizado,
        "combustible": combustible,
        "consumo_bruto": consumo_bruto,
        "rendimiento_n": rendimiento_n,
        "cop_calor": cop_calor,
        "poder_calorifico_bruto": poder_calorifico,
        "rango_calefaccion": rango_calefaccion,
        "precio_max_c_iva_clp": int(round(precio_max_clp)),
        "tienda_precio_max": tienda_max,
        "url_tienda_precio_max": url_tienda_max,
        "precio_oferta_tienda_max_clp": int(round(oferta_en_tienda_max_clp)),
        "precio_min_c_iva_clp": int(round(precio_min_clp)),
        "tienda_precio_min": tienda_min,
        "num_tiendas_activas": num_tiendas,
        "tiendas_detalle": " | ".join(tiendas_resumen_list[:5])
        + (f" (+{len(tiendas_resumen_list)-5} más)" if len(tiendas_resumen_list) > 5 else ""),
        "costo_instalacion_c_iva": costo_instalacion,
        "mantencion_c_iva": costo_mantencion,
        "otros": otros,
        "url_solotodo": url_solotodo,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scrape heating and air conditioner products from SoloTodo."
    )
    parser.add_argument(
        "--output-csv",
        default="data/solotodo_scraped_products.csv",
        help="Path to output CSV file",
    )
    parser.add_argument(
        "--output-json",
        default="data/solotodo_scraped_products.json",
        help="Path to output JSON file",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=12,
        help="Number of concurrent worker threads",
    )
    parser.add_argument(
        "--max-products",
        type=int,
        default=None,
        help="Maximum products to scrape (for testing)",
    )
    args = parser.parse_args()

    session = create_session()
    store_map = fetch_stores(session)
    cur_map, clp_rate = fetch_currencies(session)

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)

    # 1. Fetch browse listings
    all_raw_items: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for target in TARGET_URLS:
        items = fetch_browse_products(session, target)
        for it in items:
            all_raw_items.append((it, target))

    total_found = len(all_raw_items)
    logger.info(f"Total raw products gathered across 5 pages: {total_found}")

    if args.max_products:
        all_raw_items = all_raw_items[: args.max_products]
        logger.info(f"Limiting scrape to first {len(all_raw_items)} products.")

    # 2. Concurrently fetch entities & process specs
    logger.info(
        f"Processing {len(all_raw_items)} products with {args.workers} workers..."
    )
    t0 = time.time()
    processed_results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_item = {
            executor.submit(
                process_product, it, tgt, store_map, cur_map, clp_rate, session
            ): it
            for it, tgt in all_raw_items
        }

        completed_count = 0
        for future in as_completed(future_to_item):
            completed_count += 1
            try:
                res = future.result()
                processed_results.append(res)
            except Exception as e:
                logger.warning(f"Error processing item: {e}")

            if completed_count % 50 == 0 or completed_count == len(all_raw_items):
                logger.info(
                    f"Progress: {completed_count}/{len(all_raw_items)} products processed ({(completed_count/len(all_raw_items))*100:.1f}%)"
                )

    elapsed = time.time() - t0
    logger.info(
        f"Completed processing {len(processed_results)} products in {elapsed:.2f}s ({len(processed_results)/max(elapsed, 0.1):.1f} prod/sec)."
    )

    # Sort results by Category then Max Price descending
    processed_results.sort(
        key=lambda x: (x["categoria_solotodo"], -x["precio_max_c_iva_clp"])
    )

    # 3. Export to JSON
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(processed_results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved full JSON to {args.output_json}")

    # 4. Export to CSV (matching the required fields and schema)
    fieldnames = [
        "id_solotodo",
        "categoria_solotodo",
        "marca",
        "modelo",
        "nombre_completo",
        "tipo",
        "combustible",
        "consumo_bruto",
        "rendimiento_n",
        "cop_calor",
        "poder_calorifico_bruto",
        "rango_calefaccion",
        "precio_max_c_iva_clp",
        "tienda_precio_max",
        "url_tienda_precio_max",
        "precio_oferta_tienda_max_clp",
        "precio_min_c_iva_clp",
        "tienda_precio_min",
        "num_tiendas_activas",
        "tiendas_detalle",
        "costo_instalacion_c_iva",
        "mantencion_c_iva",
        "otros",
        "url_solotodo",
    ]

    with open(args.output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in processed_results:
            writer.writerow(row)
    logger.info(f"Saved full CSV to {args.output_csv}")

    # 5. Print Summary Statistics
    logger.info("\n" + "=" * 60)
    logger.info("SCRAPING EXECUTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Products Scraped: {len(processed_results)}")

    # Category breakdown
    cat_counts = {}
    for r in processed_results:
        cat_counts[r["categoria_solotodo"]] = (
            cat_counts.get(r["categoria_solotodo"], 0) + 1
        )
    for cat, cnt in cat_counts.items():
        logger.info(f"  • {cat}: {cnt} items")

    # Store with highest price frequency
    store_max_counts = {}
    for r in processed_results:
        st = r["tienda_precio_max"].split(" (")[0]
        store_max_counts[st] = store_max_counts.get(st, 0) + 1
    logger.info("\nTop 5 Stores Frequently Having Highest Price:")
    for st, cnt in sorted(
        store_max_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]:
        logger.info(f"  • {st}: {cnt} products")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
