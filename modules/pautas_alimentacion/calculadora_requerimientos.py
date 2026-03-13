"""
Calculadora de requerimientos nutricionales.
Fórmula TMB: Oxford 2005 (Henry, 2005).
"""
from typing import Optional

# ── Factores de actividad física ─────────────────────────────────────────────
FACTORES_ACTIVIDAD = {
    "sedentaria": {"label": "Sedentaria (0 hrs/sem)",  "mujer": 1.2,  "hombre": 1.2},
    "liviana":    {"label": "Liviana (3 hrs/sem)",      "mujer": 1.56, "hombre": 1.55},
    "moderada":   {"label": "Moderada (6 hrs/sem)",     "mujer": 1.64, "hombre": 1.8},
    "intensa":    {"label": "Intensa (4 hrs/día)",       "mujer": 1.82, "hombre": 2.1},
}

# Tabla de referencia Oxford 2005 para mostrar en UI
TABLA_OXFORD_REF = [
    # (rango_edad, a_mujer, b_mujer, a_hombre, b_hombre)
    ("10 – 18 a",  13.38, 692,   17.686, 658.2),
    ("18 – 30 a",  14.818, 486.6, 15.057, 692.2),
    ("30 – 60 a",   8.126, 845.6, 11.472, 873.1),
    ("> 60 a",      8.118, 688.3, 11.711, 587.7),
]


def calcular_tmb(sexo: str, edad: int, peso: float) -> float:
    """
    Calcula la Tasa Metabólica Basal usando Oxford 2005 (Henry 2005).

    sexo: 'M' (mujer) o 'H' (hombre)
    edad: años completos
    peso: kg
    Retorna kcal/día redondeado a 1 decimal.

    Nota: Verificar coeficientes con el Excel de referencia.
    Ejemplo esperado: Hombre 68 kg, 18-30 a → ~1716 kcal (Oxford publicado).
    """
    if sexo == "M":
        if 10 <= edad <= 18:
            return round(13.38 * peso + 692, 1)
        elif 18 < edad <= 30:
            return round(14.818 * peso + 486.6, 1)
        elif 30 < edad <= 60:
            return round(8.126 * peso + 845.6, 1)
        else:
            return round(8.118 * peso + 688.3, 1)
    else:  # Hombre
        if 10 <= edad <= 18:
            return round(17.686 * peso + 658.2, 1)
        elif 18 < edad <= 30:
            return round(15.057 * peso + 692.2, 1)
        elif 30 < edad <= 60:
            return round(11.472 * peso + 873.1, 1)
        else:
            return round(11.711 * peso + 587.7, 1)


def calcular_get(tmb: float, fa_key: str, sexo: str) -> float:
    """
    Calcula el Gasto Energético Total: GET = TMB × FA.
    sexo: 'M' o 'H'
    """
    fa_data = FACTORES_ACTIVIDAD.get(fa_key)
    if not fa_data:
        raise ValueError(f"Factor de actividad desconocido: {fa_key}")
    fa = fa_data["mujer"] if sexo == "M" else fa_data["hombre"]
    return round(tmb * fa, 1)


def calcular_macros(
    get: float,
    prot_gr_kg: float,
    peso: float,
    lip_pct: float = 28.0
) -> dict:
    """
    Calcula distribución de macronutrientes.

    get:        kcal totales (GET)
    prot_gr_kg: gramos de proteína por kg de peso corporal
    peso:       kg
    lip_pct:    % de lípidos sobre GET (por defecto 28 %)

    Retorna dict con todos los valores redondeados.
    """
    prot_g = round(prot_gr_kg * peso, 1)
    prot_kcal = round(prot_g * 4, 1)
    prot_pct = round((prot_kcal / get) * 100, 1) if get else 0

    lip_kcal = round(get * (lip_pct / 100), 1)
    lip_g = round(lip_kcal / 9, 1)

    cho_kcal = round(get - prot_kcal - lip_kcal, 1)
    cho_g = round(cho_kcal / 4, 1)
    cho_g_kg = round(cho_g / peso, 2) if peso else 0
    cho_pct = round((cho_kcal / get) * 100, 1) if get else 0

    return {
        "prot_g":     prot_g,
        "prot_kcal":  prot_kcal,
        "prot_pct":   prot_pct,
        "lip_g":      lip_g,
        "lip_kcal":   lip_kcal,
        "lip_pct":    round(lip_pct, 1),
        "cho_g":      cho_g,
        "cho_kcal":   cho_kcal,
        "cho_pct":    cho_pct,
        "cho_g_kg":   cho_g_kg,
    }


def get_fa_label(fa_key: str) -> str:
    """Retorna la etiqueta legible del factor de actividad."""
    data = FACTORES_ACTIVIDAD.get(fa_key, {})
    return data.get("label", fa_key)


def get_fa_valor(fa_key: str, sexo: str) -> float:
    """Retorna el valor numérico del FA según sexo."""
    data = FACTORES_ACTIVIDAD.get(fa_key, {})
    return data.get("mujer" if sexo == "M" else "hombre", 1.0)
