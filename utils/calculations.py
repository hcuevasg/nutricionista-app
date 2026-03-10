"""
Anthropometric and nutritional calculations.
All weight in kg, height in cm, circumferences in cm, skinfolds in mm.
"""
import math
from typing import Optional, Tuple


ACTIVITY_FACTORS = {
    "Sedentario (sin ejercicio)": 1.2,
    "Ligeramente activo (1-3 dias/sem)": 1.375,
    "Moderadamente activo (3-5 dias/sem)": 1.55,
    "Muy activo (6-7 dias/sem)": 1.725,
    "Extremadamente activo (atleta)": 1.9,
}

# Durnin & Womersley (1974) constants: (min_age, max_age, C, M)
# Body density = C - M × log10(Σ4 skinfolds)
# Σ4 = biceps + triceps + subscapular + cresta iliaca
_DW_WOMEN = [
    (17, 19, 1.1549, 0.0678),
    (20, 29, 1.1599, 0.0717),
    (30, 39, 1.1423, 0.0632),
    (40, 49, 1.1333, 0.0612),
    (50, 999, 1.1339, 0.0645),
]
_DW_MEN = [
    (17, 19, 1.1620, 0.0630),
    (20, 29, 1.1631, 0.0632),
    (30, 39, 1.1422, 0.0544),
    (40, 49, 1.1620, 0.0700),
    (50, 999, 1.1715, 0.0779),
]


def sum_6_skinfolds(triceps, subscapular, supraspinal,
                    abdominal, medial_thigh, max_calf) -> Optional[float]:
    """Sum of 6 ISAK skinfolds (marked with *). All in mm."""
    vals = [triceps, subscapular, supraspinal, abdominal, medial_thigh, max_calf]
    if any(v is None for v in vals):
        return None
    return round(sum(vals), 1)


def body_fat_durnin_womersley(biceps_mm: float, triceps_mm: float,
                               subscapular_mm: float, iliac_crest_mm: float,
                               age: int, sex: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Durnin & Womersley (1974) — ISAK Level 1.
    Σ4 = bíceps + tríceps + subescapular + cresta iliaca.
    Returns (body_density, fat_mass_pct) via Siri equation.
    """
    try:
        sigma4 = biceps_mm + triceps_mm + subscapular_mm + iliac_crest_mm
        if sigma4 <= 0:
            return None, None
        log_s = math.log10(sigma4)

        table = _DW_MEN if sex.lower() in ("masculino", "m", "hombre") else _DW_WOMEN
        C, M = table[-1][2], table[-1][3]   # default: oldest range
        for min_a, max_a, c, m in table:
            if min_a <= age <= max_a:
                C, M = c, m
                break

        density = C - M * log_s
        fat_pct = (4.95 / density - 4.5) * 100
        return round(density, 4), round(fat_pct, 1)
    except (ValueError, ZeroDivisionError):
        return None, None


def fat_mass_kg(weight_kg: float, fat_pct: float) -> float:
    return round(weight_kg * fat_pct / 100, 2)


def lean_mass_kg(weight_kg: float, fat_kg: float) -> float:
    return round(weight_kg - fat_kg, 2)


# ── Classic formulas (kept for full report compatibility) ────────────────────

def bmi(weight_kg: float, height_cm: float) -> float:
    if height_cm <= 0:
        return 0.0
    return round(weight_kg / (height_cm / 100) ** 2, 2)


def bmi_category(bmi_val: float) -> str:
    if bmi_val < 18.5:
        return "Bajo peso"
    elif bmi_val < 25.0:
        return "Normal"
    elif bmi_val < 30.0:
        return "Sobrepeso"
    elif bmi_val < 35.0:
        return "Obesidad grado I"
    elif bmi_val < 40.0:
        return "Obesidad grado II"
    else:
        return "Obesidad grado III"


def ideal_weight_lorentz(height_cm: float, sex: str) -> float:
    if height_cm <= 0:
        return 0.0
    if sex.lower() in ("masculino", "m", "hombre"):
        return round(height_cm - 100 - (height_cm - 150) / 4, 1)
    return round(height_cm - 100 - (height_cm - 150) / 2, 1)


def bmr_mifflin(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if sex.lower() in ("masculino", "m", "hombre"):
        return round(base + 5, 1)
    return round(base - 161, 1)


def tdee(bmr_val: float, activity_level: str) -> float:
    return round(bmr_val * ACTIVITY_FACTORS.get(activity_level, 1.2), 1)


def macro_distribution(total_calories: float,
                        protein_pct: float = 30,
                        carbs_pct: float = 45,
                        fat_pct: float = 25) -> dict:
    return {
        "protein_g": round(total_calories * protein_pct / 100 / 4, 1),
        "carbs_g":   round(total_calories * carbs_pct   / 100 / 4, 1),
        "fat_g":     round(total_calories * fat_pct     / 100 / 9, 1),
    }


def waist_hip_ratio(waist_cm: float, hip_cm: float) -> float:
    return round(waist_cm / hip_cm, 3) if hip_cm > 0 else 0.0


def whr_risk(ratio: float, sex: str) -> str:
    is_male = sex.lower() in ("masculino", "m", "hombre")
    if is_male:
        return "Riesgo bajo" if ratio < 0.90 else ("Riesgo moderado" if ratio <= 0.99 else "Riesgo alto")
    return "Riesgo bajo" if ratio < 0.80 else ("Riesgo moderado" if ratio <= 0.85 else "Riesgo alto")


def body_fat_navy(sex: str, height_cm: float,
                  waist_cm: float, neck_cm: float,
                  hip_cm: float = 0.0) -> Optional[float]:
    try:
        if sex.lower() in ("masculino", "m", "hombre"):
            if waist_cm <= neck_cm:
                return None
            val = 495 / (1.0324 - 0.19077 * math.log10(waist_cm - neck_cm)
                         + 0.15456 * math.log10(height_cm)) - 450
        else:
            if (waist_cm + hip_cm) <= neck_cm:
                return None
            val = 495 / (1.29579 - 0.35004 * math.log10(waist_cm + hip_cm - neck_cm)
                         + 0.22100 * math.log10(height_cm)) - 450
        return round(val, 1)
    except (ValueError, ZeroDivisionError):
        return None


def body_fat_category(pct: float, sex: str, age: int) -> str:
    is_male = sex.lower() in ("masculino", "m", "hombre")
    if is_male:
        if pct < 6:   return "Esencial"
        if pct < 14:  return "Atleta"
        if pct < 18:  return "En forma"
        if pct < 25:  return "Aceptable"
        return "Obesidad"
    else:
        if pct < 14:  return "Esencial"
        if pct < 21:  return "Atleta"
        if pct < 25:  return "En forma"
        if pct < 32:  return "Aceptable"
        return "Obesidad"


# ── ISAK Level 2 formulas ────────────────────────────────────────────────────

def somatotype_heath_carter(
    height_cm: float, weight_kg: float,
    triceps_mm: float, subscapular_mm: float, supraspinal_mm: float,
    humerus_width_cm: float, femur_width_cm: float,
    arm_contracted_cm: float, calf_cm: float, max_calf_mm: float,
) -> tuple:
    """
    Heath & Carter (1990) somatotype.
    Returns (endomorphy, mesomorphy, ectomorphy) or (None, None, None).
    Requires diameters in cm, skinfolds in mm, perimeters in cm.
    """
    vals = [height_cm, weight_kg, triceps_mm, subscapular_mm, supraspinal_mm,
            humerus_width_cm, femur_width_cm, arm_contracted_cm, calf_cm, max_calf_mm]
    if any(v is None for v in vals):
        return None, None, None
    try:
        # Endomorphy — Σ3 skinfolds corrected to 170.18 cm height
        sigma3 = triceps_mm + subscapular_mm + supraspinal_mm
        sigma3_corr = sigma3 * (170.18 / height_cm)
        endo = (-0.7182 + 0.1451 * sigma3_corr
                - 0.00068 * sigma3_corr ** 2
                + 0.0000014 * sigma3_corr ** 3)

        # Mesomorphy — corrected arm and calf perimeters
        arm_corr = arm_contracted_cm - triceps_mm / 10
        calf_corr = calf_cm - max_calf_mm / 10
        meso = (0.858 * humerus_width_cm + 0.601 * femur_width_cm
                + 0.188 * arm_corr + 0.161 * calf_corr
                - height_cm * 0.131 + 4.5)

        # Ectomorphy via Height-Weight Ratio
        hwr = height_cm / (weight_kg ** (1 / 3))
        if hwr > 40.75:
            ecto = 0.732 * hwr - 28.58
        elif hwr > 38.25:
            ecto = 0.463 * hwr - 17.63
        else:
            ecto = 0.1

        return round(max(0.1, endo), 2), round(max(0.1, meso), 2), round(max(0.1, ecto), 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return None, None, None


def waist_height_ratio(waist_cm: float, height_cm: float) -> Optional[float]:
    """Índice cintura/talla. Saludable < 0.5."""
    try:
        if not waist_cm or not height_cm:
            return None
        return round(waist_cm / height_cm, 3)
    except (TypeError, ZeroDivisionError):
        return None


# ── Puntos de corte / clasificación ─────────────────────────────────────────

LEVEL_COLOR = {
    "excellent": "#16a34a",
    "good":      "#16a34a",
    "average":   "#ca8a04",
    "high":      "#ea580c",
    "very_high": "#dc2626",
    "low":       "#2563eb",
    "moderate":  "#ca8a04",
    "risk":      "#dc2626",
}

LEVEL_EMOJI = {
    "excellent": "🟢",
    "good":      "🟢",
    "average":   "🟡",
    "high":      "🟠",
    "very_high": "🔴",
    "low":       "🔵",
    "moderate":  "🟡",
    "risk":      "🔴",
}

# Fat% tables: (min_age, max_age, [excellent_max, good_max, average_max, high_max])
_FAT_WOMEN_TABLE = [
    (20, 29, [15, 19, 28, 31]),
    (30, 39, [16, 20, 29, 32]),
    (40, 49, [17, 21, 30, 33]),
    (50, 59, [18, 22, 31, 34]),
    (60, 999, [19, 23, 32, 35]),
]
_FAT_MEN_TABLE = [
    (20, 29, [11, 13, 20, 23]),
    (30, 39, [12, 15, 21, 24]),
    (40, 49, [14, 17, 23, 26]),
    (50, 59, [15, 18, 24, 27]),
    (60, 999, [16, 19, 25, 28]),
]


def classify_fat_pct(pct: float, sex: str, age: int) -> tuple:
    """Returns (category_text, level_key) for % body fat."""
    is_male = sex.lower() in ("masculino", "m", "hombre")
    table = _FAT_MEN_TABLE if is_male else _FAT_WOMEN_TABLE
    t = table[-1][2]
    for min_a, max_a, thresh in table:
        if min_a <= age <= max_a:
            t = thresh
            break
    if pct <= t[0]: return "Excelente",    "excellent"
    if pct <= t[1]: return "Bueno",        "good"
    if pct <= t[2]: return "Promedio",     "average"
    if pct <= t[3]: return "Elevado",      "high"
    return "Muy elevado", "very_high"


def classify_bmi(bmi_val: float) -> tuple:
    """Returns (category_text, level_key) for BMI."""
    if bmi_val < 18.5: return "Bajo peso",   "low"
    if bmi_val < 25.0: return "Normal",       "excellent"
    if bmi_val < 30.0: return "Sobrepeso",    "average"
    if bmi_val < 35.0: return "Obesidad I",   "high"
    if bmi_val < 40.0: return "Obesidad II",  "very_high"
    return "Obesidad III", "very_high"


def classify_whr(ratio: float, sex: str) -> tuple:
    """Returns (category_text, level_key) for waist-hip ratio."""
    is_male = sex.lower() in ("masculino", "m", "hombre")
    if is_male:
        if ratio < 0.95:  return "Riesgo bajo",     "excellent"
        if ratio <= 1.00: return "Riesgo moderado",  "moderate"
        return "Riesgo alto", "risk"
    else:
        if ratio < 0.80:  return "Riesgo bajo",     "excellent"
        if ratio <= 0.85: return "Riesgo moderado",  "moderate"
        return "Riesgo alto", "risk"


def classify_whtr(ratio: float) -> tuple:
    """Returns (category_text, level_key) for waist-height ratio."""
    if ratio < 0.50: return "Saludable",           "excellent"
    if ratio < 0.60: return "Riesgo incrementado",  "average"
    return "Riesgo alto", "very_high"


def arm_muscle_area(arm_relaxed_cm: float, triceps_mm: float) -> Optional[float]:
    """
    Área Muscular del Brazo (AMB) en cm².
    AMB = (C - π × T/10)² / (4π)  donde C = perím. brazo relajado (cm), T = tríceps (mm).
    """
    try:
        if arm_relaxed_cm is None or triceps_mm is None:
            return None
        T_cm = triceps_mm / 10
        muscle_perim = arm_relaxed_cm - math.pi * T_cm
        if muscle_perim <= 0:
            return None
        return round(muscle_perim ** 2 / (4 * math.pi), 2)
    except (TypeError, ValueError):
        return None
