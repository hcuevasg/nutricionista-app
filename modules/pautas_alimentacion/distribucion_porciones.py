"""
Lógica de cálculo para distribución de porciones por grupo y tiempo de comida.
"""
from typing import Dict, Tuple


def calcular_aporte_total(
    porciones_dict: Dict[str, float],
    grupos_macros: dict
) -> Dict[str, float]:
    """
    Calcula el aporte total de macronutrientes a partir de las porciones asignadas.

    porciones_dict: {grupo: porciones, ...}
    grupos_macros:  referencia GRUPOS_MACROS con {kcal, cho, lip, prot} por porción

    Retorna: {"kcal": x, "cho": x, "lip": x, "prot": x}
    """
    totales = {"kcal": 0.0, "cho": 0.0, "lip": 0.0, "prot": 0.0}
    for grupo, porciones in porciones_dict.items():
        if porciones and grupo in grupos_macros:
            macros = grupos_macros[grupo]
            totales["kcal"] += macros["kcal"] * porciones
            totales["cho"]  += macros["cho"]  * porciones
            totales["lip"]  += macros["lip"]  * porciones
            totales["prot"] += macros["prot"] * porciones
    return {k: round(v, 1) for k, v in totales.items()}


def calcular_aporte_grupo(grupo: str, porciones: float, grupos_macros: dict) -> dict:
    """Calcula el aporte de un solo grupo para el número de porciones dado."""
    if grupo not in grupos_macros or not porciones:
        return {"kcal": 0.0, "cho": 0.0, "lip": 0.0, "prot": 0.0}
    m = grupos_macros[grupo]
    return {
        "kcal": round(m["kcal"] * porciones, 1),
        "cho":  round(m["cho"]  * porciones, 1),
        "lip":  round(m["lip"]  * porciones, 1),
        "prot": round(m["prot"] * porciones, 1),
    }


def calcular_adecuacion(
    aporte: Dict[str, float],
    requerimiento: Dict[str, float]
) -> Dict[str, dict]:
    """
    Calcula el porcentaje de adecuación para kcal, cho, lip, prot.

    requerimiento: {"kcal": x, "cho": x, "lip": x, "prot": x}
    Retorna: {
        "kcal": {"pct": 98.5, "estado": "ok"},
        ...
    }
    Estados: "ok" (90-110%), "warning" (85-115%), "bad" (fuera de rango)
    """
    result = {}
    for key in ("kcal", "cho", "lip", "prot"):
        req = requerimiento.get(key, 0)
        ap  = aporte.get(key, 0)
        if req and req > 0:
            pct = round((ap / req) * 100, 1)
        else:
            pct = 0.0
        if 90 <= pct <= 110:
            estado = "ok"
        elif 85 <= pct <= 115:
            estado = "warning"
        else:
            estado = "bad"
        result[key] = {"pct": pct, "estado": estado}
    return result


def calcular_aporte_por_tiempo(
    distribucion_dict: Dict[str, Dict[str, float]],
    grupos_macros: dict
) -> Dict[str, dict]:
    """
    Calcula kcal, cho, lip, prot por tiempo de comida.

    distribucion_dict: {tiempo: {grupo: porciones, ...}, ...}

    Retorna: {
        tiempo: {"kcal": x, "cho": x, "lip": x, "prot": x, "pct_vct": x},
        ...
        "total": {"kcal": x, ...}
    }
    Nota: pct_vct se calcula después de conocer el total, por lo que se
    devuelve como 0 y el llamador debe calcularlo si necesita el VCT.
    """
    resultado: Dict[str, dict] = {}
    grand_total = {"kcal": 0.0, "cho": 0.0, "lip": 0.0, "prot": 0.0}

    for tiempo, grupos in distribucion_dict.items():
        aporte = calcular_aporte_total(grupos, grupos_macros)
        resultado[tiempo] = dict(aporte)
        for k in grand_total:
            grand_total[k] += aporte.get(k, 0)

    grand_total = {k: round(v, 1) for k, v in grand_total.items()}
    resultado["total"] = grand_total

    # Calcular %VCT por tiempo
    total_kcal = grand_total["kcal"]
    for tiempo in list(resultado.keys()):
        if tiempo == "total":
            continue
        kcal_tiempo = resultado[tiempo]["kcal"]
        resultado[tiempo]["pct_vct"] = (
            round((kcal_tiempo / total_kcal) * 100, 1) if total_kcal else 0.0
        )

    return resultado


def validar_porciones_totales(
    porciones_dia: Dict[str, float],
    distribucion: Dict[str, Dict[str, float]]
) -> Dict[str, float]:
    """
    Verifica que la suma de porciones distribuidas no supere las asignadas por día.

    porciones_dia:  {grupo: porciones_totales_dia}
    distribucion:   {tiempo: {grupo: porciones}}

    Retorna: {grupo: diferencia}
    diferencia > 0 → hay exceso (rojo en UI)
    diferencia = 0 → exacto (verde en UI)
    diferencia < 0 → faltan porciones por distribuir
    """
    # Suma distribuida por grupo
    distribuido: Dict[str, float] = {}
    for grupos in distribucion.values():
        for grupo, porciones in grupos.items():
            distribuido[grupo] = distribuido.get(grupo, 0.0) + (porciones or 0.0)

    diferencias: Dict[str, float] = {}
    for grupo in porciones_dia:
        asignado = porciones_dia.get(grupo, 0.0) or 0.0
        dist = distribuido.get(grupo, 0.0)
        diferencias[grupo] = round(dist - asignado, 4)

    return diferencias
