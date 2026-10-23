"""Catálogo de exámenes de laboratorio frecuentes en la consulta nutricional.

Rangos de referencia habituales para adultos. Cada laboratorio publica los
suyos: al registrar un resultado se guarda el rango usado (editable), para que
el historial no cambie si este catálogo se ajusta.
"""
from typing import Dict, Optional, Tuple

# key: (nombre, grupo, unidad, rango hombres, rango mujeres) — (mín, máx), None = sin límite
Range = Tuple[Optional[float], Optional[float]]
CATALOG: Dict[str, Tuple[str, str, str, Range, Range]] = {
    "glicemia":       ("Glicemia en ayunas", "Metabolismo de la glucosa", "mg/dL", (70, 99), (70, 99)),
    "hba1c":          ("Hemoglobina glicosilada (HbA1c)", "Metabolismo de la glucosa", "%", (None, 5.6), (None, 5.6)),
    "insulina":       ("Insulina basal", "Metabolismo de la glucosa", "µUI/mL", (2.6, 24.9), (2.6, 24.9)),
    "colesterol":     ("Colesterol total", "Perfil lipídico", "mg/dL", (None, 199), (None, 199)),
    "ldl":            ("Colesterol LDL", "Perfil lipídico", "mg/dL", (None, 129), (None, 129)),
    "hdl":            ("Colesterol HDL", "Perfil lipídico", "mg/dL", (40, None), (50, None)),
    "trigliceridos":  ("Triglicéridos", "Perfil lipídico", "mg/dL", (None, 149), (None, 149)),
    "hemoglobina":    ("Hemoglobina", "Hemograma y hierro", "g/dL", (13.5, 17.5), (12.0, 15.5)),
    "ferritina":      ("Ferritina", "Hemograma y hierro", "ng/mL", (30, 400), (15, 150)),
    "vitamina_b12":   ("Vitamina B12", "Vitaminas", "pg/mL", (200, 900), (200, 900)),
    "vitamina_d":     ("Vitamina D (25-OH)", "Vitaminas", "ng/mL", (30, 100), (30, 100)),
    "tsh":            ("TSH", "Tiroides", "mUI/L", (0.4, 4.0), (0.4, 4.0)),
    "creatinina":     ("Creatinina", "Función renal y hepática", "mg/dL", (0.7, 1.3), (0.6, 1.1)),
    "acido_urico":    ("Ácido úrico", "Función renal y hepática", "mg/dL", (3.4, 7.0), (2.4, 6.0)),
    "got":            ("GOT / AST", "Función renal y hepática", "U/L", (None, 40), (None, 32)),
    "gpt":            ("GPT / ALT", "Función renal y hepática", "U/L", (None, 41), (None, 33)),
    "albumina":       ("Albúmina", "Función renal y hepática", "g/dL", (3.5, 5.0), (3.5, 5.0)),
    "pcr":            ("Proteína C reactiva", "Inflamación", "mg/L", (None, 5.0), (None, 5.0)),
}


def is_female(sex: Optional[str]) -> bool:
    return (sex or "").strip().upper().startswith("F")


def reference(key: str, sex: Optional[str]) -> Range:
    entry = CATALOG[key]
    return entry[4] if is_female(sex) else entry[3]


def status(valor: float, ref_min: Optional[float], ref_max: Optional[float]) -> str:
    if ref_min is not None and valor < ref_min:
        return "bajo"
    if ref_max is not None and valor > ref_max:
        return "alto"
    return "normal"


def as_list(sex: Optional[str]):
    out = []
    for key, (nombre, grupo, unidad, _, _) in CATALOG.items():
        ref_min, ref_max = reference(key, sex)
        out.append({"key": key, "nombre": nombre, "grupo": grupo, "unidad": unidad,
                    "ref_min": ref_min, "ref_max": ref_max})
    return out
