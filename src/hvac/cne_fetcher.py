"""Cliente para obtener precios de combustibles desde la API de la CNE."""

import base64
import json
import logging
import os
import time
from collections import defaultdict
from typing import Optional

import requests

logger = logging.getLogger(__name__)

CNE_BASE_URL = "https://api.cne.cl"
CNE_LOGIN_PATH = "/api/login"
CNE_ENDPOINTS = {
    "parafina": {
        "path": "/api/ea/precio/combustibleliquido",
        "tipo_key": "tipo_combustible",
        "tipo_val": "kerosene_domestico",
        "precio_key": "precio_por_litro",
        "unidad": "litro",
    },
    "gas_licuado": {
        "path": "/api/ea/precio/glp",
        "tipo_key": "tamanio",
        "tipo_val": "15 kg",
        "precio_key": "precio_pesos",
        "unidad": "kg",
        "divisor": 15.0,
    },
    "gas_natural": {
        "path": "/api/ea/precio/gasnatural",
        "tipo_key": "consumo_m3_gasred",
        "tipo_val": "19,3 m3",
        "precio_key": "precio_pesos",
        "unidad": "m3",
        "divisor": 19.3,
    },
}

_token: Optional[str] = None
_token_exp: float = 0.0


def _parse_chilean_number(value) -> float:
    """Convierte números con formato chileno (1.234,56) a float."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _load_dotenv(path: Optional[str] = None) -> dict:
    """Lee variables KEY=VALUE desde un archivo .env (sin dependencias externas)."""
    if path is None:
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    values = {}
    if not os.path.exists(path):
        return values
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip().strip('"').strip("'")
    except OSError as exc:
        logger.warning("No se pudo leer %s: %s", path, exc)
    return values


def _get_credentials() -> tuple[Optional[str], Optional[str]]:
    """Obtiene credenciales: primero variables de entorno, luego archivo .env."""
    email = os.environ.get("CNE_API_EMAIL")
    password = os.environ.get("CNE_API_PASSWORD")
    if email and password:
        return email, password
    dotenv = _load_dotenv()
    return dotenv.get("CNE_API_EMAIL"), dotenv.get("CNE_API_PASSWORD")


def _decode_jwt_exp(token: str) -> float:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return float(data.get("exp", 0))
    except Exception:
        return 0.0


def _login() -> tuple[Optional[str], Optional[str]]:
    """Autentica contra la API CNE. Retorna (token, error)."""
    global _token, _token_exp
    email, password = _get_credentials()
    if not email or not password:
        return None, (
            "Credenciales CNE no configuradas. Defina CNE_API_EMAIL y CNE_API_PASSWORD "
            "como variables de entorno o en un archivo .env en la raíz del proyecto."
        )
    try:
        resp = requests.post(
            CNE_BASE_URL + CNE_LOGIN_PATH,
            json={"email": email, "password": password},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        logger.error("Login CNE rechazado (HTTP %s): %s", status, exc)
        return None, (
            f"La API CNE rechazó el login (HTTP {status}). "
            "Revise que el email y la contraseña sean correctos."
        )
    except requests.RequestException as exc:
        logger.error("Error de conexión al autenticar en CNE: %s", exc)
        return None, f"Error de conexión con la API CNE al autenticar: {exc}"
    token = resp.json().get("token")
    if not token:
        logger.error("La API CNE no devolvió token.")
        return None, "La API CNE respondió el login sin token."
    _token = token
    _token_exp = _decode_jwt_exp(token) or (time.time() + 3600)
    return _token, None


def _get_token() -> tuple[Optional[str], Optional[str]]:
    """Retorna (token, error). Reutiliza el token cacheado si sigue vigente."""
    global _token
    if _token and time.time() < _token_exp - 60:
        return _token, None
    return _login()


def _fetch_list(endpoint: str, token: str) -> list:
    resp = requests.get(
        CNE_BASE_URL + endpoint,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("data", payload)


def _latest_price(records: list, region_cod: int, precio_key: str, tipo_key: str, tipo_val: str):
    filtered = [
        r for r in records
        if r.get("region_cod") == region_cod and r.get(tipo_key) == tipo_val
    ]
    if not filtered:
        return None, None
    latest_fecha = max(r.get("fecha", "") for r in filtered)
    latest = [r for r in filtered if r.get("fecha") == latest_fecha]
    precios = [_parse_chilean_number(r.get(precio_key)) for r in latest]
    precios = [p for p in precios if p > 0]
    if not precios:
        return None, latest_fecha
    return sum(precios) / len(precios), latest_fecha


def fetch_precio_cne(combustible_nombre: str, region_cod: int) -> dict:
    """
    Obtiene el último precio disponible en la API CNE para un combustible y región.

    Retorna un dict con:
      - status: "ok" | "error"
      - precio_por_unidad: float
      - fecha_vigencia: str (YYYY-MM-DD)
      - unidad: str
      - mensaje: str opcional
    """
    config = CNE_ENDPOINTS.get(combustible_nombre)
    if not config:
        return {
            "status": "error",
            "mensaje": f"El combustible '{combustible_nombre}' no está disponible en la API CNE.",
        }

    token, auth_error = _get_token()
    if not token:
        return {
            "status": "error",
            "mensaje": auth_error or "No se pudo autenticar con la API CNE.",
        }

    try:
        records = _fetch_list(config["path"], token)
    except requests.RequestException as exc:
        logger.warning("Fallo al consultar CNE: %s", exc)
        return {"status": "error", "mensaje": f"Error de conexión con la API CNE: {exc}"}

    precio, fecha = _latest_price(
        records,
        region_cod,
        config["precio_key"],
        config["tipo_key"],
        config["tipo_val"],
    )
    if precio is None:
        return {
            "status": "error",
            "mensaje": f"No se encontró precio CNE para '{combustible_nombre}' en la región {region_cod}.",
        }

    divisor = config.get("divisor", 1.0)
    return {
        "status": "ok",
        "precio_por_unidad": round(precio / divisor, 2),
        "fecha_vigencia": fecha,
        "unidad": config["unidad"],
        "mensaje": f"Precio obtenido desde CNE ({fecha}).",
    }


def fetch_all_regions(combustible_nombre: str) -> dict:
    """
    Obtiene el último precio CNE para todas las regiones de un combustible.

    Retorna dict con:
      - status: "ok" | "error"
      - data: list[{region_cod, precio_por_unidad, fecha_vigencia, unidad}, ...]
      - mensaje: str
    """
    config = CNE_ENDPOINTS.get(combustible_nombre)
    if not config:
        return {
            "status": "error",
            "data": [],
            "mensaje": f"El combustible '{combustible_nombre}' no está disponible en la API CNE.",
        }

    token, auth_error = _get_token()
    if not token:
        return {
            "status": "error",
            "data": [],
            "mensaje": auth_error or "No se pudo autenticar con la API CNE.",
        }

    try:
        records = _fetch_list(config["path"], token)
    except requests.RequestException as exc:
        return {"status": "error", "data": [], "mensaje": f"Error de conexión: {exc}"}

    tipo_key = config["tipo_key"]
    tipo_val = config["tipo_val"]
    precio_key = config["precio_key"]
    divisor = config.get("divisor", 1.0)

    region_data = defaultdict(list)
    for r in records:
        if r.get(tipo_key) != tipo_val:
            continue
        region_data[r.get("region_cod")].append(r)

    results = []
    for region_cod, items in sorted(region_data.items()):
        latest_fecha = max(i.get("fecha", "") for i in items)
        latest = [i for i in items if i.get("fecha") == latest_fecha]
        precios = [_parse_chilean_number(i.get(precio_key)) for i in latest]
        precios = [p for p in precios if p > 0]
        if not precios:
            continue
        avg_price = sum(precios) / len(precios)
        results.append({
            "region_cod": int(region_cod),
            "precio_por_unidad": round(avg_price / divisor, 2),
            "fecha_vigencia": latest_fecha,
            "unidad": config["unidad"],
        })
    return {
        "status": "ok",
        "data": results,
        "mensaje": f"{len(results)} regiones con precio vigente ({results[0]['fecha_vigencia'] if results else 'N/A'}).",
    }
