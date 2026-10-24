"""IA para pautas (Claude): prompts, llamadas al API y validación de respuestas.

Único lugar donde se arman prompts y se llama a Anthropic. Los routers solo
cargan datos de la BD y traducen AIError a HTTP/SSE.

Configuración por variables de entorno:
- ANTHROPIC_API_KEY: key de la organización de Console vinculada al plan Max
- ANTHROPIC_MODEL:   modelo a usar (por defecto claude-haiku-5-5)
- ANTHROPIC_WORKSPACE_ID: solo si la key no pertenece a un workspace de Console
"""
import json
import logging
import os
from dataclasses import dataclass
from typing import AsyncIterator, Dict, List, Optional

import anthropic
from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-haiku-5-5"
PROVIDER = "Anthropic"

TIEMPOS_COMIDA = [
    ("desayuno", "Desayuno"), ("colacion1", "Colación 1"), ("almuerzo", "Almuerzo"),
    ("colacion2", "Colación 2"), ("once", "Once"), ("cena", "Cena"),
]

NOMBRES_GRUPOS = {
    "cereales": "Cereales", "verduras_cg": "Verduras CG", "verduras_lc": "Verduras LC",
    "frutas": "Frutas", "lacteos_ag": "Lácteos AG", "lacteos_mg": "Lácteos MG",
    "lacteos_bg": "Lácteos BG", "legumbres": "Legumbres", "carnes_ag": "Carnes AG",
    "carnes_bg": "Carnes BG", "otros_proteicos": "Otros Proteicos",
    "aceite_grasas": "Aceite y Grasas", "alim_ricos_lipidos": "Ricos en Lípidos",
    "leches_vegetales": "Leches Vegetales", "lacteos_soya": "Lácteos de Soya",
    "semillas_chia": "Semillas Chía", "azucares": "Azúcares",
    "omega_3": "Omega 3", "suplemento_proteico": "Suplemento Proteico",
}

TIPO_LABELS = {
    "omnivoro": "Omnívoro",
    "ovolacto": "Ovo-lacto vegetariano",
    "vegano": "Vegano",
    "vegetariano": "Vegetariano",
    "renal": "Renal",
    "diabetico": "Diabético",
    "hipocalorico": "Hipocalórico",
}

_SYSTEM_MENU = (
    "Eres nutricionista clínico en Chile. Diseñas menús concretos con alimentos "
    "chilenos reales (marraqueta, cazuela, porotos, plateada, yogur, quesillo, etc.) "
    "que respetan exactamente las porciones indicadas por grupo de alimentos."
)
_SYSTEM_SUGGEST = (
    "Eres nutricionista clínico experto en Chile. Eres conciso, práctico y basas "
    "tus análisis en evidencia."
)


class AIError(Exception):
    """Error con un mensaje apto para mostrar al usuario."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ── Validación del menú ─────────────────────────────────────────────────────

class MenuItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=120)
    cantidad: float = Field(gt=0, le=2000)
    unidad: str = Field(pattern="^(g|ml)$")
    kcal_100: float = Field(ge=0, le=950)
    prot_100: float = Field(ge=0, le=100)
    cho_100: float = Field(ge=0, le=100)
    lip_100: float = Field(ge=0, le=100)


class MenuTiempo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opcion1: List[MenuItem] = Field(min_length=1, max_length=6)
    opcion2: List[MenuItem] = Field(min_length=1, max_length=6)


_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "nombre": {"type": "string", "description": "Alimento y preparación, en español de Chile"},
        "cantidad": {"type": "number", "description": "Cantidad en la unidad indicada"},
        "unidad": {"type": "string", "enum": ["g", "ml"]},
        "kcal_100": {"type": "number", "description": "kcal por 100 g/ml del alimento tal cual"},
        "prot_100": {"type": "number", "description": "g de proteína por 100 g/ml"},
        "cho_100": {"type": "number", "description": "g de carbohidratos por 100 g/ml"},
        "lip_100": {"type": "number", "description": "g de lípidos por 100 g/ml"},
    },
    "required": ["nombre", "cantidad", "unidad", "kcal_100", "prot_100", "cho_100", "lip_100"],
    "additionalProperties": False,
}
def menu_schema(tiempos: List[str]) -> dict:
    """JSON schema del menú.

    Es un arreglo de tiempos con una sola definición (y no un objeto con una
    propiedad por tiempo) porque repetir la estructura por cada tiempo hace que
    la gramática compilada de structured outputs supere el límite del API.
    Que estén exactamente los tiempos de la pauta lo verifica parse_menu.
    """
    return {
        "type": "object",
        "properties": {
            "tiempos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tiempo": {"type": "string", "enum": list(tiempos)},
                        "opcion1": {"type": "array", "items": _ITEM_SCHEMA},
                        "opcion2": {"type": "array", "items": _ITEM_SCHEMA},
                    },
                    "required": ["tiempo", "opcion1", "opcion2"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["tiempos"],
        "additionalProperties": False,
    }


def parse_menu(raw: str, tiempos: List[str]) -> Dict[str, dict]:
    """Valida el JSON del modelo y lo devuelve como {tiempo: {opcion1, opcion2}}.
    Lanza ValueError (ValidationError hereda de ValueError)."""
    data = json.loads(raw)
    entries = data.get("tiempos") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise ValueError("El menú no tiene la lista de tiempos")
    menu: Dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("tiempo") not in tiempos:
            raise ValueError(f"Tiempo inesperado: {entry!r:.80}")
        if entry["tiempo"] in menu:
            raise ValueError(f"Tiempo repetido: {entry['tiempo']}")
        body = {k: v for k, v in entry.items() if k != "tiempo"}
        menu[entry["tiempo"]] = MenuTiempo.model_validate(body).model_dump()
    faltantes = [t for t in tiempos if t not in menu]
    if faltantes:
        raise ValueError(f"Faltan tiempos: {faltantes}")
    return {t: menu[t] for t in tiempos}


# ── Construcción de prompts ─────────────────────────────────────────────────

@dataclass
class MenuRequest:
    prompt: str
    tiempos: List[str]


def _load_json(value: Optional[str], default):
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def build_menu_request(pauta, allergies_json: Optional[str]) -> MenuRequest:
    distribucion = _load_json(pauta.distribucion_json, {})
    tiempos: List[str] = []
    lineas: List[str] = []
    for key, label in TIEMPOS_COMIDA:
        grupos = distribucion.get(key) or {}
        activos = [(g, float(p)) for g, p in grupos.items() if float(p or 0) > 0]
        if not activos:
            continue
        tiempos.append(key)
        detalle = ", ".join(f"{NOMBRES_GRUPOS.get(g, g)} {p:g} porción(es)" for g, p in activos)
        lineas.append(f"- {key} ({label}): {detalle}")

    if not tiempos:
        raise AIError("La pauta no tiene distribución por tiempos definida", status_code=400)

    alergias = _load_json(allergies_json, [])
    restriccion = (
        f"\nAlergias del paciente: {', '.join(alergias)}. No incluyas ningún alimento "
        "que las contenga ni sus derivados.\n"
        if alergias else ""
    )
    tipo = TIPO_LABELS.get(pauta.tipo_pauta, pauta.tipo_pauta)
    prompt = f"""Pauta {tipo} de {pauta.kcal_objetivo:.0f} kcal/día para un paciente en Chile.{restriccion}
Porciones por tiempo de comida:
{chr(10).join(lineas)}

Para cada tiempo de comida listado, propone dos opciones de menú (opcion1 y opcion2) de 2 a 4 alimentos cada una, que cubran esas porciones.
- Incluye cada tiempo listado una sola vez, con su identificador exacto en el campo "tiempo".
- Cantidades en g o ml; kcal_100, prot_100, cho_100 y lip_100 son por 100 g o 100 ml del alimento tal como se consume."""
    return MenuRequest(prompt=prompt, tiempos=tiempos)


def build_suggest_prompt(pauta, evals) -> str:
    lineas = []
    for e in evals:
        partes = [f"Fecha: {e.date}"]
        if e.weight_kg: partes.append(f"Peso: {e.weight_kg}kg")
        if e.fat_mass_pct: partes.append(f"Grasa: {e.fat_mass_pct:.1f}%")
        if e.lean_mass_kg: partes.append(f"Masa magra: {e.lean_mass_kg:.1f}kg")
        if e.fat_mass_kg: partes.append(f"Masa grasa: {e.fat_mass_kg:.1f}kg")
        lineas.append(" | ".join(partes))
    historial = "\n".join(lineas) if lineas else "Sin evaluaciones registradas"

    return f"""Analiza la siguiente pauta nutricional y el historial antropométrico del paciente.

PAUTA ACTUAL:
- Nombre: {pauta.name}
- Tipo: {TIPO_LABELS.get(pauta.tipo_pauta, pauta.tipo_pauta)}
- Kcal objetivo: {pauta.kcal_objetivo:.0f} kcal
- Proteínas: {pauta.prot_g:.1f}g ({pauta.prot_pct:.0f}%)
- Lípidos: {pauta.lip_g:.1f}g ({pauta.lip_pct:.0f}%)
- Carbohidratos: {pauta.cho_g:.1f}g ({pauta.cho_pct:.0f}%)
- Proteínas por kg: {pauta.prot_g_kg:.2f} g/kg
- TMB: {pauta.tmb:.0f} kcal | GET: {pauta.get_kcal:.0f} kcal
- Factor actividad: {pauta.fa_key}
- Paciente: {pauta.sexo}, {pauta.edad} años, {pauta.peso}kg

HISTORIAL ANTROPOMÉTRICO (de más antiguo a más reciente):
{historial}

Entrega un análisis clínico conciso con:
1. Evaluación de la tendencia de composición corporal
2. Si la pauta actual es adecuada para los resultados observados
3. Sugerencias específicas de ajuste (kcal, macros, proteína/kg) si corresponde
4. Recomendaciones prácticas adicionales

Responde en español, de forma directa y profesional, en máximo 250 palabras.
El texto se muestra tal cual, sin formato: no uses markdown (ni **, ni #, ni tablas); para listas usa guiones."""


# ── Llamadas a Claude ───────────────────────────────────────────────────────

def model_name() -> str:
    return os.getenv("ANTHROPIC_MODEL") or DEFAULT_MODEL


def is_configured() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _client() -> anthropic.AsyncAnthropic:
    if not is_configured():
        raise AIError("IA no configurada: falta ANTHROPIC_API_KEY en el servidor", status_code=503)
    # Las keys que no pertenecen a un workspace exigen indicar cuál usar
    workspace_id = os.getenv("ANTHROPIC_WORKSPACE_ID")
    headers = {"anthropic-workspace-id": workspace_id} if workspace_id else None
    return anthropic.AsyncAnthropic(timeout=120.0, default_headers=headers)


def _api_error(exc: Exception, context: str) -> AIError:
    logger.exception("Error de Anthropic (%s)", context)
    if isinstance(exc, anthropic.RateLimitError):
        return AIError("Se alcanzó el límite de uso de la IA. Intenta en unos minutos.", 429)
    if isinstance(exc, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)):
        return AIError("La API key de Anthropic no es válida o no tiene permisos.", 503)
    if isinstance(exc, anthropic.BadRequestError):
        # Saldo agotado, key sin workspace, etc.; el detalle queda en el log
        return AIError("La IA rechazó la solicitud. Revisa la configuración y los créditos de la API en Console.", 502)
    return AIError("No se pudo conectar con la IA. Intenta de nuevo.", 502)


def _check_stop(message, context: str) -> None:
    if message.stop_reason == "refusal":
        logger.warning("Claude rechazó la solicitud (%s): %s", context, message.stop_details)
        raise AIError("La IA no pudo procesar esta solicitud.", 422)
    if message.stop_reason == "max_tokens":
        raise AIError("La respuesta de la IA quedó incompleta. Intenta de nuevo.", 502)


async def stream_menu(req: MenuRequest, attempts: int = 2) -> AsyncIterator[dict]:
    """Genera el menú en streaming.

    Emite {"type": "progress", "done": n, "total": m} a medida que el modelo
    completa tiempos de comida y termina con {"type": "menu", "menu": {...}}.
    Reintenta una vez si el JSON no pasa la validación.
    """
    client = _client()
    total = len(req.tiempos)
    for attempt in range(1, attempts + 1):
        text = ""
        done = 0
        try:
            async with client.messages.stream(
                model=model_name(),
                max_tokens=16000,
                system=_SYSTEM_MENU,
                messages=[{"role": "user", "content": req.prompt}],
                output_config={
                    "effort": "low",
                    "format": {"type": "json_schema", "schema": menu_schema(req.tiempos)},
                },
            ) as stream:
                async for chunk in stream.text_stream:
                    text += chunk
                    # Cada tiempo cierra con su opcion2: sirve como avance real
                    completed = max(text.count('"opcion2"') - 1, 0)
                    if completed > done:
                        done = completed
                        yield {"type": "progress", "done": done, "total": total}
                final = await stream.get_final_message()
        except anthropic.APIError as exc:
            raise _api_error(exc, "menú") from exc

        _check_stop(final, "menú")
        try:
            menu = parse_menu(text, req.tiempos)
        except (ValueError, ValidationError) as exc:
            logger.warning("Menú IA inválido (intento %s/%s): %s", attempt, attempts, exc)
            if attempt == attempts:
                raise AIError("La IA devolvió un menú inválido. Intenta de nuevo.", 502) from exc
            continue
        yield {"type": "progress", "done": total, "total": total}
        yield {"type": "menu", "menu": menu}
        return


async def generate_menu(req: MenuRequest) -> Dict[str, dict]:
    async for event in stream_menu(req):
        if event["type"] == "menu":
            return event["menu"]
    raise AIError("La IA no devolvió un menú.", 502)


async def suggest_adjustments(pauta, evals) -> str:
    client = _client()
    try:
        message = await client.messages.create(
            model=model_name(),
            max_tokens=8000,
            system=_SYSTEM_SUGGEST,
            messages=[{"role": "user", "content": build_suggest_prompt(pauta, evals)}],
            output_config={"effort": "medium"},
        )
    except anthropic.APIError as exc:
        raise _api_error(exc, "sugerencias") from exc
    _check_stop(message, "sugerencias")
    text = "".join(b.text for b in message.content if b.type == "text").strip()
    if not text:
        raise AIError("La IA no devolvió sugerencias. Intenta de nuevo.", 502)
    return text
