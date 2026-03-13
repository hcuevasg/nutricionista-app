"""
Generación de ideas de menú usando la API de Claude (Anthropic).
Una sola llamada genera 2 opciones para TODOS los tiempos de comida del día.
"""
import json
import threading
from typing import Optional, List, Dict, Callable

MODELO = "claude-haiku-4-5-20251001"
TIMEOUT = 90
MAX_TOKENS = 8192

TIEMPOS_NOMBRES = {
    "desayuno": "Desayuno", "colacion1": "Colacion 1",
    "colacion2": "Colacion 2", "almuerzo": "Almuerzo",
    "once": "Once", "cena": "Cena"
}


def _obtener_ejemplos_referencia(tipo_pauta: str, kcal_objetivo: float) -> List[Dict]:
    """Busca plantillas de referencia en BD para usar como ejemplos few-shot."""
    try:
        import database.db_manager as db
        plantillas = db.get_plantillas_ref(tipo_pauta)
        margen = 300
        cercanas = [
            p for p in plantillas
            if p.get("kcal_objetivo") and
            abs(float(p["kcal_objetivo"]) - kcal_objetivo) <= margen
        ]
        resultado = []
        for p in cercanas[:1]:  # Solo 1 ejemplo para reducir tokens
            detalle = db.get_plantilla_ref_completa(p["id"])
            if detalle:
                resultado.append(detalle)
        return resultado
    except Exception:
        return []


def _construir_prompt_sistema() -> str:
    return (
        "Eres un asistente de nutricion clinica para Chile. "
        "Genera opciones de menu practicas respetando las porciones indicadas. "
        "Usa nombres de alimentos en espanol con gramajes y medidas caseras. "
        "Responde UNICAMENTE en JSON valido, sin texto adicional."
    )


def _construir_prompt_todos_tiempos(
    tipo_pauta: str,
    tiempos_con_porciones: Dict[str, Dict[str, float]],
    grupos_macros: Dict,
    nombres_grupos: Dict,
    get_total: float,
    ejemplos: List[Dict]
) -> str:
    # Construir descripcion compacta de cada tiempo
    tiempos_texto = []
    for tiempo, porciones in tiempos_con_porciones.items():
        kcal_tiempo = sum(
            float(porciones.get(g, 0)) * grupos_macros.get(g, {}).get("kcal", 0)
            for g in porciones
        )
        grupos_activos = []
        for grupo, cant in porciones.items():
            cant = float(cant or 0)
            if cant > 0:
                nombre = nombres_grupos.get(grupo, grupo)
                kcal_g = cant * grupos_macros.get(grupo, {}).get("kcal", 0)
                grupos_activos.append(f"{nombre}:{cant}p({kcal_g:.0f}kcal)")
        label = TIEMPOS_NOMBRES.get(tiempo, tiempo)
        tiempos_texto.append(
            f"{label} [{kcal_tiempo:.0f}kcal]: {', '.join(grupos_activos)}"
        )

    ejemplos_texto = ""
    if ejemplos:
        ej = ejemplos[0]
        ejemplos_texto = f"\nREFERENCIA ({ej.get('descripcion', '')}):\n"
        for t in ej.get("tiempos", [])[:3]:  # Max 3 tiempos de referencia
            label = TIEMPOS_NOMBRES.get(t["tiempo_comida"], t["tiempo_comida"])
            ejemplos_texto += f"{label}: {t.get('nombre_preparacion', '')}\n"

    schema_ejemplo = (
        '{"desayuno":[{"nombre_preparacion":"Nombre",'
        '"alimentos":[{"nombre":"Alimento","cantidad_g":100,"medida_casera":"1 taza"}],'
        '"total_kcal":200}]}'
    )

    return (
        f"TIPO DE PAUTA: {tipo_pauta}\n"
        f"CALORIAS TOTALES DIA: {get_total:.0f} kcal\n\n"
        f"PORCIONES POR TIEMPO:\n" + "\n".join(tiempos_texto)
        + ejemplos_texto
        + f"\n\nGenera 2 opciones por cada tiempo de comida listado.\n"
        f"Responde SOLO con JSON con esta estructura (una clave por tiempo):\n"
        f"{schema_ejemplo}\n"
        f"Claves del JSON: {', '.join(tiempos_con_porciones.keys())}"
    )


def generar_todos_los_tiempos(
    pauta_id: int,
    tipo_pauta: str,
    distribucion: Dict[str, Dict[str, float]],
    grupos_macros: Dict,
    nombres_grupos: Dict,
    get_total: float,
    callback_progreso: Optional[Callable] = None,
    callback_completado: Optional[Callable] = None
):
    """
    Genera ideas para todos los tiempos en UNA SOLA llamada a la API.
    callback_completado(resultados): llamado al terminar con {tiempo: [opciones]}
    """
    def _run():
        resultados = {}
        try:
            from utils.config_manager import cargar_api_key
            api_key = cargar_api_key()
            if not api_key:
                if callback_progreso:
                    callback_progreso("ERROR: Configura tu API key en Configuracion")
                if callback_completado:
                    callback_completado({})
                return

            tiempos_con_porciones = {
                t: g for t, g in distribucion.items()
                if any(float(v or 0) > 0 for v in g.values())
            }
            if not tiempos_con_porciones:
                if callback_completado:
                    callback_completado({})
                return

            if callback_progreso:
                callback_progreso(f"Generando menú para {len(tiempos_con_porciones)} tiempos...")

            ejemplos = _obtener_ejemplos_referencia(tipo_pauta, get_total)

            import anthropic
            cliente = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT)

            respuesta = cliente.messages.create(
                model=MODELO,
                max_tokens=MAX_TOKENS,
                system=_construir_prompt_sistema(),
                messages=[{
                    "role": "user",
                    "content": _construir_prompt_todos_tiempos(
                        tipo_pauta, tiempos_con_porciones,
                        grupos_macros, nombres_grupos, get_total, ejemplos
                    )
                }]
            )

            texto = respuesta.content[0].text.strip()

            # Limpiar markdown fences si los hay
            if "```" in texto:
                partes = texto.split("```")
                for parte in partes:
                    p = parte.strip()
                    if p.startswith("json"):
                        p = p[4:].strip()
                    if p.startswith("{"):
                        texto = p
                        break

            datos = json.loads(texto)

            # Normalizar: la respuesta puede tener clave "opciones" o directamente listas
            for tiempo in tiempos_con_porciones:
                raw = datos.get(tiempo, [])
                # Si viene envuelto en {"opciones": [...]}
                if isinstance(raw, dict):
                    raw = raw.get("opciones", [])
                opciones = raw[:2]
                # Eliminar macros por alimento si la IA los incluyó (no los necesitamos)
                for op in opciones:
                    for alim in op.get("alimentos", []):
                        for k in ("kcal", "proteinas_g", "carbohidratos_g", "grasas_g",
                                  "prot_g", "cho_g", "lip_g"):
                            alim.pop(k, None)
                resultados[tiempo] = opciones if opciones else None

            if callback_progreso:
                ok = sum(1 for v in resultados.values() if v)
                callback_progreso(f"Listo: {ok}/{len(tiempos_con_porciones)} tiempos generados")

        except json.JSONDecodeError as e:
            print(f"[IA ERROR JSON] {e}")
            if callback_progreso:
                callback_progreso(f"ERROR: respuesta JSON inválida ({e})")
        except Exception as e:
            err = str(e)
            err_lower = err.lower()
            if "credit balance is too low" in err_lower or "insufficient" in err_lower:
                msg = "Sin créditos en la API de Anthropic. Recarga en console.anthropic.com"
            elif "authentication" in err_lower or "api_key" in err_lower or "invalid x-api-key" in err_lower:
                msg = "API key inválida. Verifica tu clave en Configuración"
            elif "connection" in err_lower or "timeout" in err_lower or "network" in err_lower:
                msg = "Error de conexión. Verifica tu internet e intenta de nuevo"
            else:
                import traceback
                traceback.print_exc()
                msg = err[:120]
            print(f"[IA ERROR] {msg}")
            if callback_progreso:
                callback_progreso(f"ERROR: {msg}")

        if callback_completado:
            callback_completado(resultados)

    hilo = threading.Thread(target=_run, daemon=True)
    hilo.start()


# Mantener compatibilidad con posibles llamadas directas a generar_ideas_menu
def generar_ideas_menu(
    pauta_id: int,
    tiempo_comida: str,
    tipo_pauta: str,
    porciones_tiempo: Dict[str, float],
    grupos_macros: Dict,
    nombres_grupos: Dict,
    get_total: float,
    callback_progreso: Optional[Callable] = None
) -> Optional[List[Dict]]:
    """Wrapper de compatibilidad — usa generar_todos_los_tiempos en su lugar."""
    resultado = []
    event = threading.Event()

    def _cb(res):
        resultado.extend(res.get(tiempo_comida) or [])
        event.set()

    generar_todos_los_tiempos(
        pauta_id=pauta_id,
        tipo_pauta=tipo_pauta,
        distribucion={tiempo_comida: porciones_tiempo},
        grupos_macros=grupos_macros,
        nombres_grupos=nombres_grupos,
        get_total=get_total,
        callback_progreso=callback_progreso,
        callback_completado=_cb
    )
    event.wait(timeout=TIMEOUT + 5)
    return resultado or None
