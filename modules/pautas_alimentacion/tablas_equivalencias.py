"""
Tablas de equivalencias de alimentos por tipo de pauta.
Cada tabla define: {grupo: [lista de strings "gramaje — alimento (medida casera)"]}

NOTA: Completar con los datos exactos del documento
      TABLAS_SEGUN_PAUTA_DE_ALIMENTACION.docx
"""

TABLAS_EQUIVALENCIAS = {

    # ── OVO-LACTO VEGETARIANO ─────────────────────────────────────────────────
    "ovolacto": {
        "cereales": [
            "160 g — Choclo (1 T.)",
            "150 g — Papas (2 U. chicas)",
            "120 g — Arroz integral cocido (3/4 T.)",
            "120 g — Fideos o pasta cocida (3/4 T.)",
            "100 g — Pan de molde integral (2 rebanadas)",
            "60 g  — Pan marraqueta (1 U.)",
            "50 g  — Avena cruda (5 Cdas.)",
            "50 g  — Quinoa cocida (3 Cdas.)",
            "40 g  — Tostadas integrales (4 U.)",
            "30 g  — Cereal de desayuno sin azúcar (1/2 T.)",
        ],
        "grasa_saludable": [
            "50 g  — Palta (1/4 U. grande)",
            "15 g  — Aceite de oliva (1 Cda.)",
            "15 g  — Nueces (5 mariposas)",
            "15 g  — Almendras (10 U.)",
            "15 g  — Maní sin sal (1 Cda.)",
            "10 g  — Mantequilla de maní (1 Cda.)",
        ],
        "proteicos": [
            "88 g  — Tofu Moringa (1/4 caja) / Seitán (1/2 churrasco)",
            "50 g  — Tofu firme (1/2 T.)",
            "50 g  — Huevo (1 U.)",
            "50 g  — Soya s/hidratar (3 Cdas.)",
            "15 g  — Barra Wild Protein Vegana",
            "1 U   — Barrita Underfive",
        ],
        "lacteos": [
            "200 ml — Leche descremada (1 vaso)",
            "150 g  — Yogur sin azúcar (3/4 T.)",
            "120 g  — Yogur griego descremado (1/2 T.)",
            "40 g   — Queso fresco (2 rebanadas)",
            "30 g   — Quesillo (2 rebanadas)",
        ],
        "omega3": [
            "18 g  — Semillas de chía (2 Cdas.)",
            "15 g  — Nueces (5 mariposas)",
            "5 g   — Linaza molida (1 Cda.)",
        ],
        "frutas": [
            "200 g — Sandía (2 T. en cubos)",
            "180 g — Melón (2 T. en cubos)",
            "150 g — Naranja (1 U. grande)",
            "150 g — Manzana (1 U. mediana)",
            "140 g — Pera (1 U. mediana)",
            "120 g — Kiwi (2 U.)",
            "100 g — Plátano (1/2 U.)",
            "100 g — Uvas (15 U.)",
            "80 g  — Frutillas (6-8 U.)",
        ],
        "legumbres": [
            "180 g — Lentejas cocidas (3/4 T.)",
            "180 g — Porotos cocidos (3/4 T.)",
            "180 g — Garbanzos cocidos (3/4 T.)",
            "180 g — Arvejas cocidas (3/4 T.)",
        ],
        "aceites": [
            "5 ml  — Aceite de oliva (1 Cdta.)",
            "5 ml  — Aceite de canola (1 Cdta.)",
            "5 ml  — Aceite de maravilla (1 Cdta.)",
        ],
        "verduras_cg": [
            "200 g — Zanahoria (2 U. medianas)",
            "200 g — Betarraga (1 U. mediana)",
            "200 g — Zapallo (1 T. en trozos)",
            "150 g — Choclo desgranado (3/4 T.)",
            "150 g — Arvejas (3/4 T.)",
        ],
        "verduras_lc": [
            "300 g — Lechuga (2 T. picada)",
            "250 g — Pepino (1 U. grande)",
            "200 g — Tomate (2 U. medianas)",
            "200 g — Pimentón (1 U. grande)",
            "200 g — Apio (4 ramas)",
            "150 g — Champiñones (1 T.)",
            "150 g — Espinaca (1 T.)",
            "150 g — Brócoli (1 T.)",
            "150 g — Coliflor (1 T.)",
        ],
    },

    # ── VEGANO ────────────────────────────────────────────────────────────────
    "vegano": {
        "cereales": [
            "160 g — Choclo (1 T.)",
            "150 g — Papas (2 U. chicas)",
            "120 g — Arroz integral cocido (3/4 T.)",
            "120 g — Fideos o pasta cocida (3/4 T.)",
            "100 g — Pan de molde integral (2 rebanadas)",
            "60 g  — Pan marraqueta (1 U.)",
            "50 g  — Avena cruda (5 Cdas.)",
            "50 g  — Quinoa cocida (3 Cdas.)",
        ],
        "grasa_saludable": [
            "50 g  — Palta (1/4 U. grande)",
            "15 g  — Aceite de oliva (1 Cda.)",
            "15 g  — Nueces (5 mariposas)",
            "15 g  — Almendras (10 U.)",
            "15 g  — Maní sin sal (1 Cda.)",
        ],
        "proteicos": [
            "100 g — Tofu firme (1/2 T.)",
            "100 g — Tempeh (1/2 T.)",
            "88 g  — Seitán (1/2 churrasco)",
            "50 g  — Soya texturizada hidratada (1/2 T.)",
            "30 g  — Soya s/hidratar (3 Cdas.)",
        ],
        "leches_vegetales": [
            "200 ml — Leche de soya sin azúcar (1 vaso)",
            "200 ml — Leche de almendra sin azúcar (1 vaso)",
            "200 ml — Leche de avena sin azúcar (1 vaso)",
        ],
        "omega3": [
            "18 g  — Semillas de chía (2 Cdas.)",
            "15 g  — Nueces (5 mariposas)",
            "5 g   — Linaza molida (1 Cda.)",
        ],
        "frutas": [
            "200 g — Sandía (2 T. en cubos)",
            "180 g — Melón (2 T. en cubos)",
            "150 g — Naranja (1 U. grande)",
            "150 g — Manzana (1 U. mediana)",
            "100 g — Plátano (1/2 U.)",
            "80 g  — Frutillas (6-8 U.)",
        ],
        "legumbres": [
            "180 g — Lentejas cocidas (3/4 T.)",
            "180 g — Porotos negros cocidos (3/4 T.)",
            "180 g — Garbanzos cocidos (3/4 T.)",
            "180 g — Arvejas cocidas (3/4 T.)",
            "180 g — Edamame cocido (3/4 T.)",
        ],
        "aceites": [
            "5 ml  — Aceite de oliva (1 Cdta.)",
            "5 ml  — Aceite de linaza (1 Cdta.)",
            "5 ml  — Aceite de canola (1 Cdta.)",
        ],
        "verduras_cg": [
            "200 g — Zanahoria (2 U. medianas)",
            "200 g — Betarraga (1 U. mediana)",
            "200 g — Zapallo (1 T. en trozos)",
            "150 g — Arvejas (3/4 T.)",
        ],
        "verduras_lc": [
            "300 g — Lechuga (2 T. picada)",
            "200 g — Tomate (2 U. medianas)",
            "200 g — Pepino (1 U. grande)",
            "150 g — Espinaca (1 T.)",
            "150 g — Brócoli (1 T.)",
            "150 g — Champiñones (1 T.)",
        ],
    },

    # ── PESCETARIANO ─────────────────────────────────────────────────────────
    "pescetariano": {
        "cereales": [
            "160 g — Choclo (1 T.)",
            "150 g — Papas (2 U. chicas)",
            "120 g — Arroz integral cocido (3/4 T.)",
            "120 g — Fideos o pasta cocida (3/4 T.)",
            "100 g — Pan de molde integral (2 rebanadas)",
            "60 g  — Pan marraqueta (1 U.)",
            "50 g  — Avena cruda (5 Cdas.)",
        ],
        "grasa_saludable": [
            "50 g  — Palta (1/4 U. grande)",
            "15 g  — Aceite de oliva (1 Cda.)",
            "15 g  — Nueces (5 mariposas)",
            "15 g  — Almendras (10 U.)",
        ],
        "proteicos_pescado": [
            "100 g — Salmón (filete mediano)",
            "100 g — Atún fresco (1 filete)",
            "100 g — Merluza (1 filete)",
            "100 g — Reineta (1 filete)",
            "80 g  — Atún en agua escurrido (1/2 lata)",
            "100 g — Camarones cocidos (1/2 T.)",
            "100 g — Sardinas (2-3 U.)",
            "100 g — Pulpo cocido (1/2 T.)",
            "50 g  — Huevo (1 U.)",
        ],
        "lacteos": [
            "200 ml — Leche descremada (1 vaso)",
            "150 g  — Yogur sin azúcar (3/4 T.)",
            "40 g   — Queso fresco (2 rebanadas)",
        ],
        "frutas": [
            "200 g — Sandía (2 T. en cubos)",
            "150 g — Naranja (1 U. grande)",
            "150 g — Manzana (1 U. mediana)",
            "100 g — Plátano (1/2 U.)",
            "80 g  — Frutillas (6-8 U.)",
        ],
        "legumbres": [
            "180 g — Lentejas cocidas (3/4 T.)",
            "180 g — Porotos cocidos (3/4 T.)",
            "180 g — Garbanzos cocidos (3/4 T.)",
        ],
        "aceites": [
            "5 ml  — Aceite de oliva (1 Cdta.)",
            "5 ml  — Aceite de canola (1 Cdta.)",
        ],
        "verduras_cg": [
            "200 g — Zanahoria (2 U. medianas)",
            "200 g — Betarraga (1 U. mediana)",
            "150 g — Zapallo (1 T. en trozos)",
        ],
        "verduras_lc": [
            "300 g — Lechuga (2 T. picada)",
            "200 g — Tomate (2 U. medianas)",
            "150 g — Brócoli (1 T.)",
            "150 g — Espinaca (1 T.)",
        ],
    },

    # ── OMNÍVORO ─────────────────────────────────────────────────────────────
    "omnivoro": {
        "cereales": [
            "160 g — Choclo (1 T.)",
            "150 g — Papas (2 U. chicas)",
            "120 g — Arroz cocido (3/4 T.)",
            "120 g — Fideos o pasta cocida (3/4 T.)",
            "100 g — Pan de molde integral (2 rebanadas)",
            "60 g  — Pan marraqueta (1 U.)",
            "50 g  — Avena cruda (5 Cdas.)",
            "40 g  — Tostadas integrales (4 U.)",
        ],
        "grasa_saludable": [
            "50 g  — Palta (1/4 U. grande)",
            "15 g  — Aceite de oliva (1 Cda.)",
            "15 g  — Nueces (5 mariposas)",
            "15 g  — Almendras (10 U.)",
            "15 g  — Maní sin sal (1 Cda.)",
        ],
        "proteicos": [
            "100 g — Pechuga de pollo sin piel (1 filete chico)",
            "100 g — Pavo sin piel (1 filete chico)",
            "100 g — Carne vacuna magra (1 filete chico)",
            "100 g — Salmón (1 filete chico)",
            "100 g — Merluza (1 filete chico)",
            "80 g  — Atún en agua escurrido (1/2 lata)",
            "50 g  — Huevo (1 U.)",
            "50 g  — Tofu firme (1/2 T.)",
        ],
        "lacteos": [
            "200 ml — Leche descremada (1 vaso)",
            "150 g  — Yogur sin azúcar (3/4 T.)",
            "120 g  — Yogur griego descremado (1/2 T.)",
            "40 g   — Queso fresco (2 rebanadas)",
            "30 g   — Quesillo (2 rebanadas)",
        ],
        "frutas": [
            "200 g — Sandía (2 T. en cubos)",
            "180 g — Melón (2 T. en cubos)",
            "150 g — Naranja (1 U. grande)",
            "150 g — Manzana (1 U. mediana)",
            "140 g — Pera (1 U. mediana)",
            "120 g — Kiwi (2 U.)",
            "100 g — Plátano (1/2 U.)",
            "100 g — Uvas (15 U.)",
            "80 g  — Frutillas (6-8 U.)",
        ],
        "legumbres": [
            "180 g — Lentejas cocidas (3/4 T.)",
            "180 g — Porotos cocidos (3/4 T.)",
            "180 g — Garbanzos cocidos (3/4 T.)",
            "180 g — Arvejas cocidas (3/4 T.)",
        ],
        "aceites": [
            "5 ml  — Aceite de oliva (1 Cdta.)",
            "5 ml  — Aceite de canola (1 Cdta.)",
            "5 ml  — Aceite de maravilla (1 Cdta.)",
        ],
        "verduras_cg": [
            "200 g — Zanahoria (2 U. medianas)",
            "200 g — Betarraga (1 U. mediana)",
            "200 g — Zapallo (1 T. en trozos)",
            "150 g — Choclo desgranado (3/4 T.)",
            "150 g — Arvejas (3/4 T.)",
        ],
        "verduras_lc": [
            "300 g — Lechuga (2 T. picada)",
            "250 g — Pepino (1 U. grande)",
            "200 g — Tomate (2 U. medianas)",
            "200 g — Pimentón (1 U. grande)",
            "150 g — Champiñones (1 T.)",
            "150 g — Espinaca (1 T.)",
            "150 g — Brócoli (1 T.)",
            "150 g — Coliflor (1 T.)",
        ],
    },

    # ── SIN GLUTEN ────────────────────────────────────────────────────────────
    "sin_gluten": {
        "cereales": [
            "160 g — Choclo (1 T.)",
            "150 g — Papas (2 U. chicas)",
            "120 g — Arroz blanco o integral cocido (3/4 T.)",
            "120 g — Fideos de arroz cocidos (3/4 T.)",
            "50 g  — Avena certificada SG cruda (5 Cdas.)",
            "50 g  — Quinoa cocida (3 Cdas.)",
            "50 g  — Amaranto cocido (3 Cdas.)",
            "40 g  — Tostadas de arroz (4 U.)",
            "40 g  — Pan de molde sin gluten (2 rebanadas)",
        ],
        "grasa_saludable": [
            "50 g  — Palta (1/4 U. grande)",
            "15 g  — Aceite de oliva (1 Cda.)",
            "15 g  — Nueces (5 mariposas)",
            "15 g  — Almendras (10 U.)",
            "15 g  — Maní sin sal (1 Cda.)",
        ],
        "proteicos": [
            "100 g — Pechuga de pollo sin piel (1 filete chico)",
            "100 g — Carne vacuna magra (1 filete chico)",
            "100 g — Salmón (1 filete chico)",
            "100 g — Merluza (1 filete chico)",
            "80 g  — Atún en agua escurrido (1/2 lata)",
            "50 g  — Huevo (1 U.)",
            "50 g  — Tofu firme (1/2 T.)",
        ],
        "lacteos": [
            "200 ml — Leche descremada SG (1 vaso)",
            "150 g  — Yogur natural SG (3/4 T.)",
            "40 g   — Queso fresco SG (2 rebanadas)",
        ],
        "frutas": [
            "200 g — Sandía (2 T. en cubos)",
            "150 g — Naranja (1 U. grande)",
            "150 g — Manzana (1 U. mediana)",
            "100 g — Plátano (1/2 U.)",
            "80 g  — Frutillas (6-8 U.)",
        ],
        "legumbres": [
            "180 g — Lentejas cocidas (3/4 T.)",
            "180 g — Porotos cocidos (3/4 T.)",
            "180 g — Garbanzos cocidos (3/4 T.)",
        ],
        "aceites": [
            "5 ml  — Aceite de oliva (1 Cdta.)",
            "5 ml  — Aceite de canola (1 Cdta.)",
        ],
        "verduras_cg": [
            "200 g — Zanahoria (2 U. medianas)",
            "200 g — Betarraga (1 U. mediana)",
            "150 g — Zapallo (1 T. en trozos)",
        ],
        "verduras_lc": [
            "300 g — Lechuga (2 T. picada)",
            "200 g — Tomate (2 U. medianas)",
            "150 g — Brócoli (1 T.)",
            "150 g — Espinaca (1 T.)",
        ],
    },
}

# Nombres de grupos para las tablas de equivalencias (difieren de GRUPOS_MACROS)
NOMBRES_GRUPOS_EQUIV = {
    "cereales":           "Cereales y Tubérculos",
    "grasa_saludable":    "Grasas Saludables",
    "proteicos":          "Alimentos Proteicos",
    "proteicos_pescado":  "Proteicos (Pescados y Mariscos)",
    "lacteos":            "Lácteos",
    "omega3":             "Fuentes de Omega-3",
    "frutas":             "Frutas",
    "legumbres":          "Legumbres",
    "aceites":            "Aceites",
    "verduras_cg":        "Verduras CG (Carbohidratos)",
    "verduras_lc":        "Verduras LC (Libres de Calorías)",
    "leches_vegetales":   "Leches Vegetales",
    "lacteos_soya":       "Lácteos de Soya",
}

# Texto de abreviaciones para el PDF
ABREVIATURAS = (
    "(T.) Taza   ·   (U.) Unidad   ·   (Cda.) Cuchara de sopa   ·   "
    "(Cdta.) Cuchara de té   ·   (SG) Sin Gluten"
)
