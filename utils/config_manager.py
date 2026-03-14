"""Gestión de configuración local (API keys, preferencias)."""
import os
import json
from typing import Optional

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".nutriapp", "config.json")


def _cargar_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _guardar_config(config: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def guardar_api_key(key: str):
    config = _cargar_config()
    config["anthropic_api_key"] = key.strip()
    _guardar_config(config)


def cargar_api_key() -> Optional[str]:
    return _cargar_config().get("anthropic_api_key")


def api_key_configurada() -> bool:
    key = cargar_api_key()
    return bool(key and len(key) > 10)
