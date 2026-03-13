"""
Definición de grupos de alimentos, macros por porción, grupos por tipo de pauta
y tiempos de comida para el módulo de Pautas de Alimentación.
"""

# Macronutrientes por 1 porción de cada grupo
GRUPOS_MACROS = {
    "cereales":            {"kcal": 140, "cho": 30,   "lip": 1,  "prot": 3},
    "verduras_cg":         {"kcal": 30,  "cho": 5,    "lip": 0,  "prot": 2},
    "verduras_lc":         {"kcal": 10,  "cho": 2.5,  "lip": 0,  "prot": 0},
    "frutas":              {"kcal": 65,  "cho": 15,   "lip": 0,  "prot": 1},
    "lacteos_ag":          {"kcal": 110, "cho": 9,    "lip": 6,  "prot": 5},
    "lacteos_mg":          {"kcal": 85,  "cho": 9,    "lip": 3,  "prot": 5},
    "lacteos_bg":          {"kcal": 70,  "cho": 10,   "lip": 0,  "prot": 7},
    "legumbres":           {"kcal": 170, "cho": 32,   "lip": 1,  "prot": 13},
    "carnes_ag":           {"kcal": 120, "cho": 1,    "lip": 8,  "prot": 11},
    "carnes_bg":           {"kcal": 65,  "cho": 1,    "lip": 2,  "prot": 11},
    "otros_proteicos":     {"kcal": 75,  "cho": 5,    "lip": 3,  "prot": 7},
    "aceite_grasas":       {"kcal": 180, "cho": 0,    "lip": 20, "prot": 0},
    "alim_ricos_lipidos":  {"kcal": 175, "cho": 5,    "lip": 15, "prot": 5},
    "leches_vegetales":    {"kcal": 80,  "cho": 10,   "lip": 2,  "prot": 1},
    "lacteos_soya":        {"kcal": 80,  "cho": 9,    "lip": 4,  "prot": 6},
    "semillas_chia":       {"kcal": 37,  "cho": 2,    "lip": 2,  "prot": 1.5},
    "azucares":            {"kcal": 20,  "cho": 5,    "lip": 0,  "prot": 0},
}

# Grupos disponibles según tipo de pauta
GRUPOS_POR_PAUTA = {
    "omnivoro": [
        "cereales", "verduras_cg", "verduras_lc", "frutas",
        "lacteos_ag", "lacteos_mg", "lacteos_bg",
        "legumbres", "carnes_ag", "carnes_bg",
        "aceite_grasas", "alim_ricos_lipidos", "azucares",
    ],
    "ovolacto": [
        "cereales", "verduras_cg", "verduras_lc", "frutas",
        "lacteos_ag", "lacteos_mg", "lacteos_bg",
        "legumbres", "otros_proteicos",
        "aceite_grasas", "alim_ricos_lipidos",
        "leches_vegetales", "lacteos_soya", "semillas_chia", "azucares",
    ],
    "vegano": [
        "cereales", "verduras_cg", "verduras_lc", "frutas",
        "legumbres", "otros_proteicos",
        "aceite_grasas", "alim_ricos_lipidos",
        "leches_vegetales", "lacteos_soya", "semillas_chia", "azucares",
    ],
    "pescetariano": [
        "cereales", "verduras_cg", "verduras_lc", "frutas",
        "lacteos_ag", "lacteos_mg", "lacteos_bg",
        "legumbres", "carnes_bg", "otros_proteicos",
        "aceite_grasas", "alim_ricos_lipidos", "azucares",
    ],
    "sin_gluten": [
        "cereales", "verduras_cg", "verduras_lc", "frutas",
        "lacteos_ag", "lacteos_mg", "lacteos_bg",
        "legumbres", "carnes_ag", "carnes_bg", "otros_proteicos",
        "aceite_grasas", "alim_ricos_lipidos", "azucares",
    ],
}

# Nombres para mostrar en la UI y PDF
NOMBRES_GRUPOS = {
    "cereales":           "Cereales",
    "verduras_cg":        "Verduras CG",
    "verduras_lc":        "Verduras LC",
    "frutas":             "Frutas",
    "lacteos_ag":         "Lácteos AG",
    "lacteos_mg":         "Lácteos MG",
    "lacteos_bg":         "Lácteos BG",
    "legumbres":          "Legumbres",
    "carnes_ag":          "Carnes AG",
    "carnes_bg":          "Carnes BG",
    "otros_proteicos":    "Otros Proteicos",
    "aceite_grasas":      "Aceite y Grasas",
    "alim_ricos_lipidos": "Ricos en Lípidos",
    "leches_vegetales":   "Leches Vegetales",
    "lacteos_soya":       "Lácteos de Soya",
    "semillas_chia":      "Semillas Chía/Linaza",
    "azucares":           "Azúcares",
}

# Etiquetas de tipo de pauta
NOMBRES_TIPOS_PAUTA = {
    "omnivoro":     "Omnívoro",
    "ovolacto":     "Ovo-lacto Vegetariano",
    "vegano":       "Vegano",
    "pescetariano": "Pescetariano",
    "sin_gluten":   "Sin Gluten",
}

TIEMPOS_COMIDA = [
    ("desayuno",  "Desayuno"),
    ("colacion1", "Colación 1"),
    ("colacion2", "Colación 2"),
    ("almuerzo",  "Almuerzo"),
    ("once",      "Once"),
    ("cena",      "Cena"),
]
