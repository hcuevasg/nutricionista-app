"""
import_usda.py — Poblar alimentos_db con base de datos nutricional integrada.

Incluye ~400 alimentos comunes + 50 alimentos chilenos.
No requiere descargar ningún archivo externo.

USO:  python import_usda.py

OPCIONAL — datos USDA completos (>8000 alimentos):
  1. Descargar SR Legacy JSON desde https://fdc.nal.usda.gov/download-datasets.html
  2. python import_usda.py ruta/al/archivo.json
"""

import json, os, sys, sqlite3
from typing import Optional

# ── Datos integrados ──────────────────────────────────────────────────────────
# Formato: (nombre_es, nombre_en, kcal, prot_g, carb_g, fat_g, fiber_g)
# Todos los valores son por 100 g de alimento.

_BUILTIN_FOODS = [
    # ── CEREALES Y DERIVADOS ──────────────────────────────────────────────────
    ("Arroz blanco cocido",            "White rice cooked",              130, 2.7, 28.2, 0.3, 0.4),
    ("Arroz integral cocido",          "Brown rice cooked",              111, 2.6, 23.0, 0.9, 1.8),
    ("Arroz blanco crudo",             "White rice raw",                 365, 7.1, 80.0, 0.7, 1.3),
    ("Arroz integral crudo",           "Brown rice raw",                 370, 7.9, 77.2, 2.9, 3.5),
    ("Avena cruda en hojuelas",        "Rolled oats raw",                389, 16.9, 66.3, 6.9, 10.6),
    ("Avena cocida con agua",          "Cooked oatmeal",                  71,  2.5, 12.0, 1.5,  1.7),
    ("Pan blanco",                     "White bread",                    265,  9.0, 49.0, 3.2,  2.7),
    ("Pan integral",                   "Whole wheat bread",              247, 13.0, 41.0, 3.4,  6.0),
    ("Pan de centeno",                 "Rye bread",                      259,  8.5, 48.0, 3.3,  6.2),
    ("Pan pita blanco",                "White pita bread",               275,  9.1, 55.7, 1.2,  2.2),
    ("Pasta cocida sin sal",           "Cooked pasta",                   158,  5.8, 30.9, 0.9,  1.8),
    ("Pasta integral cocida",          "Whole wheat pasta cooked",       124,  5.3, 26.5, 0.5,  3.9),
    ("Pasta cruda",                    "Dry pasta",                      371, 13.0, 74.0, 1.5,  3.2),
    ("Fideos de arroz cocidos",        "Rice noodles cooked",            109,  0.9, 25.9, 0.2,  0.9),
    ("Quinoa cocida",                  "Quinoa cooked",                  120,  4.4, 21.3, 1.9,  2.8),
    ("Quinoa cruda",                   "Quinoa raw",                     368, 14.1, 64.2, 6.1,  7.0),
    ("Cuscús cocido",                  "Couscous cooked",                112,  3.8, 23.2, 0.2,  1.4),
    ("Polenta cocida",                 "Polenta cooked",                  70,  1.5, 15.0, 0.3,  0.9),
    ("Chía cruda",                     "Chia seeds",                     486, 16.5, 42.1, 30.7, 34.4),
    ("Linaza molida",                  "Ground flaxseed",                534, 18.3, 28.9, 42.2, 27.3),
    ("Harina de trigo blanca",         "All-purpose flour",              364, 10.3, 76.3, 1.0,  2.7),
    ("Harina de maíz amarilla",        "Yellow cornmeal",                362,  8.1, 76.8, 3.6,  7.3),
    ("Corn flakes (cereal)",           "Corn flakes cereal",             357,  7.5, 84.0, 0.4,  2.0),
    ("Granola sin azúcar",             "Unsweetened granola",            471, 10.6, 57.0, 22.0, 6.9),
    ("Galletas de agua",               "Water crackers",                 408,  8.0, 74.0, 9.5,  2.5),
    ("Tostadas de arroz",              "Rice cakes",                     392,  8.2, 81.5, 2.8,  3.4),
    ("Maíz dulce cocido",              "Sweet corn cooked",               96,  3.4, 21.0, 1.5,  2.4),
    ("Palomitas de maíz sin sal",      "Unsalted popcorn",               387, 13.0, 78.1, 4.5, 15.1),
    ("Cebada perlada cocida",          "Pearl barley cooked",             123,  2.3, 28.2, 0.4,  3.8),

    # ── CARNES ROJAS ─────────────────────────────────────────────────────────
    ("Posta de vacuno cocida",         "Beef round cooked",              196, 29.5,  0.0, 8.1,  0.0),
    ("Filete de vacuno asado",         "Beef tenderloin roasted",        270, 26.0,  0.0, 17.8, 0.0),
    ("Carne molida 85% magra cocida",  "Ground beef 85% lean cooked",   215, 26.1,  0.0, 11.9, 0.0),
    ("Carne molida 70% magra cocida",  "Ground beef 70% lean cooked",   254, 24.7,  0.0, 17.4, 0.0),
    ("Asado de tira vacuno",           "Beef back ribs cooked",          310, 24.8,  0.0, 23.3, 0.0),
    ("Lomo de vacuno cocido",          "Beef loin cooked",               207, 28.7,  0.0,  9.5, 0.0),
    ("Lomo de cerdo cocido",           "Pork loin roasted",              242, 27.0,  0.0, 14.0, 0.0),
    ("Costillas de cerdo asadas",      "Pork ribs roasted",              361, 22.5,  0.0, 30.3, 0.0),
    ("Filete de cerdo asado",          "Pork tenderloin roasted",        166, 26.2,  0.0,  5.8, 0.0),
    ("Cordero cocido",                 "Lamb cooked",                    258, 25.6,  0.0, 16.5, 0.0),
    ("Hígado de vacuno cocido",        "Beef liver cooked",              191, 29.1,  5.1,  5.3, 0.0),

    # ── AVES ──────────────────────────────────────────────────────────────────
    ("Pechuga de pollo cocida",        "Chicken breast cooked",          165, 31.0,  0.0,  3.6, 0.0),
    ("Pechuga de pollo cruda",         "Chicken breast raw",             120, 22.5,  0.0,  2.6, 0.0),
    ("Muslo de pollo cocido",          "Chicken thigh cooked",           209, 26.0,  0.0, 10.9, 0.0),
    ("Ala de pollo cocida",            "Chicken wing cooked",            290, 27.1,  0.0, 19.5, 0.0),
    ("Pollo entero asado (con piel)",  "Whole roasted chicken",          239, 27.3,  0.0, 14.0, 0.0),
    ("Pollo entero cocido (sin piel)", "Chicken skinless cooked",        185, 27.7,  0.0,  7.6, 0.0),
    ("Pechuga de pavo cocida",         "Turkey breast cooked",           135, 30.1,  0.0,  1.0, 0.0),
    ("Pavo molido cocido",             "Ground turkey cooked",           218, 27.0,  0.0, 11.9, 0.0),

    # ── PESCADOS Y MARISCOS ───────────────────────────────────────────────────
    ("Salmón cocido",                  "Salmon cooked",                  208, 20.4,  0.0, 13.4, 0.0),
    ("Salmón crudo",                   "Salmon raw",                     208, 20.1,  0.0, 13.1, 0.0),
    ("Atún en agua (lata)",            "Canned tuna in water",           116, 25.5,  0.0,  0.8, 0.0),
    ("Atún en aceite (lata)",          "Canned tuna in oil",             198, 29.1,  0.0,  8.2, 0.0),
    ("Merluza cocida",                 "Hake cooked",                    113, 23.4,  0.0,  1.7, 0.0),
    ("Tilapia cocida",                 "Tilapia cooked",                 128, 26.2,  0.0,  2.7, 0.0),
    ("Bacalao cocido",                 "Cod cooked",                      90, 19.4,  0.0,  0.7, 0.0),
    ("Trucha cocida",                  "Trout cooked",                   190, 26.6,  0.0,  8.5, 0.0),
    ("Sardinas en aceite (lata)",      "Sardines in oil canned",         208, 24.6,  0.0, 11.5, 0.0),
    ("Sardinas al natural (lata)",     "Sardines in water canned",       140, 24.0,  0.0,  4.9, 0.0),
    ("Camarones cocidos",              "Shrimp cooked",                   99, 23.0,  0.9,  0.3, 0.0),
    ("Pulpo cocido",                   "Octopus cooked",                 164, 29.8,  4.4,  2.1, 0.0),
    ("Calamares cocidos",              "Squid cooked",                   175, 17.9,  7.8,  7.0, 0.0),
    ("Ostiones cocidos",               "Scallops cooked",                111, 20.5,  5.4,  1.2, 0.0),
    ("Almejas cocidas",                "Clams cooked",                   148, 25.5,  5.1,  2.0, 0.0),
    ("Choritos / Mejillones cocidos",  "Mussels cooked",                 172, 23.8,  7.4,  4.5, 0.0),

    # ── LÁCTEOS ───────────────────────────────────────────────────────────────
    ("Leche entera",                   "Whole milk",                      61,  3.2,  4.8,  3.3, 0.0),
    ("Leche semidescremada 2%",        "Reduced fat milk 2%",             50,  3.3,  4.8,  2.0, 0.0),
    ("Leche descremada",               "Skim milk",                       34,  3.4,  5.0,  0.1, 0.0),
    ("Leche en polvo entera",          "Whole powdered milk",            496, 26.3, 38.4, 26.7, 0.0),
    ("Yogur natural entero",           "Whole plain yogurt",              61,  3.5,  4.7,  3.3, 0.0),
    ("Yogur natural bajo en grasa",    "Low fat plain yogurt",            56,  5.7,  7.7,  0.2, 0.0),
    ("Yogur griego natural",           "Plain Greek yogurt",              59,  10.2,  3.6,  0.4, 0.0),
    ("Queso gauda / chanco",           "Gouda cheese",                   356, 24.9,  2.2, 27.4, 0.0),
    ("Queso cheddar",                  "Cheddar cheese",                 403, 24.9,  1.3, 33.1, 0.0),
    ("Queso mozzarella",               "Mozzarella cheese",              280, 19.4,  2.2, 21.6, 0.0),
    ("Queso fresco / ricotta",         "Fresh cheese / ricotta",         174, 11.3,  3.0, 13.0, 0.0),
    ("Queso crema",                    "Cream cheese",                   350,  6.2,  4.1, 34.4, 0.0),
    ("Queso cottage",                  "Cottage cheese",                  98, 11.1,  3.4,  4.3, 0.0),
    ("Mantequilla con sal",            "Salted butter",                  717,  0.9,  0.1, 81.1, 0.0),
    ("Crema de leche 35%",             "Heavy whipping cream",           340,  2.1,  2.8, 36.1, 0.0),
    ("Crema de leche 18%",             "Half and half cream",            130,  3.0,  4.3, 11.5, 0.0),

    # ── HUEVOS ────────────────────────────────────────────────────────────────
    ("Huevo entero crudo",             "Whole egg raw",                  143,  12.6,  0.7, 9.5, 0.0),
    ("Huevo entero cocido (duro)",     "Hard boiled egg",                155,  12.6,  1.1, 10.6, 0.0),
    ("Clara de huevo cruda",           "Egg white raw",                   52,  10.9,  0.7,  0.2, 0.0),
    ("Yema de huevo cruda",            "Egg yolk raw",                   322,  15.9,  3.6, 26.5, 0.0),

    # ── LEGUMBRES ────────────────────────────────────────────────────────────
    ("Lentejas cocidas",               "Lentils cooked",                 116,  9.0, 20.1,  0.4, 7.9),
    ("Lentejas crudas",                "Lentils raw",                    353, 25.8, 60.1,  1.1, 30.5),
    ("Garbanzos cocidos",              "Chickpeas cooked",               164,  8.9, 27.4,  2.6, 7.6),
    ("Garbanzos crudos",               "Chickpeas raw",                  378, 20.5, 62.9,  6.0, 17.4),
    ("Porotos negros cocidos",         "Black beans cooked",             132,  8.9, 23.7,  0.5, 8.7),
    ("Porotos rojos cocidos",          "Kidney beans cooked",            127,  8.7, 22.8,  0.5, 7.4),
    ("Porotos blancos cocidos",        "White beans cooked",             139,  9.7, 25.1,  0.4, 6.3),
    ("Arvejas cocidas",                "Green peas cooked",               84,  5.4, 15.6,  0.2, 5.5),
    ("Arvejas congeladas",             "Frozen peas",                     77,  5.2, 13.7,  0.4, 5.1),
    ("Edamame cocido",                 "Edamame cooked",                 121,  11.9,  8.9,  5.2, 5.2),
    ("Soja cocida",                    "Soybeans cooked",                173, 16.6, 10.0,  9.0, 6.0),
    ("Tofu firme",                     "Firm tofu",                       76,  8.1,  1.9,  4.8, 0.3),

    # ── FRUTAS ────────────────────────────────────────────────────────────────
    ("Manzana con cáscara",            "Apple with skin",                 52,  0.3, 13.8,  0.2, 2.4),
    ("Manzana verde",                  "Green apple",                     58,  0.4, 15.2,  0.2, 2.8),
    ("Pera",                           "Pear",                            57,  0.4, 15.2,  0.1, 3.1),
    ("Plátano / Banana",               "Banana",                          89,  1.1, 22.8,  0.3, 2.6),
    ("Naranja",                        "Orange",                          47,  0.9, 11.8,  0.1, 2.4),
    ("Mandarina",                      "Mandarin / tangerine",            53,  0.8, 13.3,  0.3, 1.8),
    ("Limón",                          "Lemon",                           29,  1.1,  9.3,  0.3, 2.8),
    ("Pomelo",                         "Grapefruit",                      42,  0.8, 10.7,  0.1, 1.6),
    ("Uvas rojas",                     "Red grapes",                      69,  0.7, 18.1,  0.2, 0.9),
    ("Uvas verdes",                    "Green grapes",                    67,  0.6, 17.2,  0.4, 0.9),
    ("Frutillas / Fresas",             "Strawberries",                    32,  0.7,  7.7,  0.3, 2.0),
    ("Arándanos",                      "Blueberries",                     57,  0.7, 14.5,  0.3, 2.4),
    ("Frambuesas",                     "Raspberries",                     52,  1.2, 11.9,  0.7, 6.5),
    ("Moras",                          "Blackberries",                    43,  1.4,  9.6,  0.5, 5.3),
    ("Sandía",                         "Watermelon",                      30,  0.6,  7.6,  0.2, 0.4),
    ("Melón",                          "Cantaloupe melon",                34,  0.8,  8.2,  0.2, 0.9),
    ("Piña / Ananá",                   "Pineapple",                       50,  0.5, 13.1,  0.1, 1.4),
    ("Mango",                          "Mango",                           60,  0.8, 15.0,  0.4, 1.6),
    ("Papaya",                         "Papaya",                          43,  0.5, 10.8,  0.3, 1.7),
    ("Palta / Aguacate",               "Avocado",                        160,  2.0,  8.5, 14.7, 6.7),
    ("Kiwi verde",                     "Green kiwi",                      61,  1.1, 14.7,  0.5, 3.0),
    ("Durazno / Melocotón",            "Peach",                           39,  0.9, 10.0,  0.3, 1.5),
    ("Ciruela fresca",                 "Fresh plum",                      46,  0.7, 11.4,  0.3, 1.4),
    ("Cereza dulce",                   "Sweet cherry",                    63,  1.1, 16.0,  0.2, 2.1),
    ("Higo fresco",                    "Fresh fig",                       74,  0.8, 19.2,  0.3, 2.9),
    ("Dátil",                          "Medjool date",                   282,  2.5, 75.0,  0.4, 8.0),
    ("Pasas de uva",                   "Raisins",                        299,  3.1, 79.2,  0.5, 3.7),
    ("Arándano seco",                  "Dried cranberry",                308,  0.1, 82.4,  1.4, 5.3),
    ("Ciruela seca",                   "Prune",                          240,  2.2, 63.9,  0.4, 7.1),
    ("Coco rallado sin azúcar",        "Unsweetened shredded coconut",   660,  6.9, 23.7, 64.5, 16.3),
    ("Limón de pica",                  "Small lime",                      30,  0.7, 10.5,  0.2, 2.8),

    # ── VERDURAS ─────────────────────────────────────────────────────────────
    ("Tomate",                         "Tomato",                          18,  0.9,  3.9,  0.2, 1.2),
    ("Lechuga iceberg",                "Iceberg lettuce",                 14,  0.9,  3.0,  0.1, 1.2),
    ("Lechuga romana",                 "Romaine lettuce",                 17,  1.2,  3.3,  0.3, 2.1),
    ("Espinaca cruda",                 "Raw spinach",                     23,  2.9,  3.6,  0.4, 2.2),
    ("Espinaca cocida",                "Cooked spinach",                  23,  3.0,  3.8,  0.3, 2.4),
    ("Brócoli crudo",                  "Raw broccoli",                    34,  2.8,  6.6,  0.4, 2.6),
    ("Brócoli cocido",                 "Cooked broccoli",                 35,  2.4,  7.2,  0.4, 3.3),
    ("Coliflor cruda",                 "Raw cauliflower",                 25,  1.9,  5.3,  0.3, 2.5),
    ("Zanahoria cruda",                "Raw carrot",                      41,  0.9,  9.6,  0.2, 2.8),
    ("Zanahoria cocida",               "Cooked carrot",                   35,  0.8,  8.2,  0.2, 3.0),
    ("Cebolla cruda",                  "Raw onion",                       40,  1.1,  9.3,  0.1, 1.7),
    ("Cebolla morada",                 "Red onion",                       42,  1.3,  9.7,  0.1, 1.5),
    ("Ajo",                            "Garlic",                         149,  6.4, 33.1,  0.5, 2.1),
    ("Puerro cocido",                  "Leek cooked",                     27,  0.9,  6.1,  0.3, 1.8),
    ("Papa con cáscara cocida",        "Potato cooked with skin",         87,  1.9, 20.1,  0.1, 1.8),
    ("Papa sin cáscara cocida",        "Potato cooked peeled",            77,  2.0, 17.8,  0.1, 1.6),
    ("Papa al vapor",                  "Steamed potato",                  76,  1.7, 17.4,  0.1, 1.5),
    ("Camote / Batata cocido",         "Sweet potato cooked",             90,  2.0, 20.7,  0.1, 3.3),
    ("Zapallo italiano / Zucchini",    "Zucchini raw",                    17,  1.2,  3.1,  0.3, 1.0),
    ("Zapallo crudo",                  "Winter squash raw",               26,  1.0,  6.5,  0.1, 0.5),
    ("Berenjena cruda",                "Eggplant raw",                    25,  1.0,  5.9,  0.2, 3.0),
    ("Pimentón rojo",                  "Red bell pepper",                 31,  1.0,  6.0,  0.3, 2.1),
    ("Pimentón verde",                 "Green bell pepper",               20,  0.9,  4.6,  0.2, 1.7),
    ("Pimentón amarillo",              "Yellow bell pepper",              27,  1.0,  6.3,  0.2, 0.9),
    ("Champiñones blancos crudos",     "White mushrooms raw",             22,  3.1,  3.3,  0.3, 1.0),
    ("Champiñones portobello",         "Portobello mushrooms",            29,  3.0,  5.1,  0.3, 1.3),
    ("Pepino con cáscara",             "Cucumber with peel",              15,  0.7,  3.6,  0.1, 0.5),
    ("Apio crudo",                     "Celery raw",                      16,  0.7,  3.0,  0.2, 1.6),
    ("Repollo crudo",                  "Raw cabbage",                     25,  1.3,  5.8,  0.1, 2.5),
    ("Repollo morado",                 "Red cabbage raw",                 31,  1.4,  7.4,  0.2, 2.1),
    ("Betarraga / Remolacha cruda",    "Raw beet",                        43,  1.6,  9.6,  0.2, 2.8),
    ("Betarraga cocida",               "Cooked beet",                     44,  1.7,  9.9,  0.2, 2.9),
    ("Acelga cruda",                   "Swiss chard raw",                 19,  1.8,  3.7,  0.2, 1.6),
    ("Kale / Col rizada cruda",        "Raw kale",                        49,  4.3,  8.8,  0.9, 3.6),
    ("Espárrago cocido",               "Asparagus cooked",                22,  2.4,  4.1,  0.2, 2.2),
    ("Choclo amarillo cocido",         "Yellow sweet corn cooked",       108,  3.3, 25.1,  1.3, 2.8),
    ("Alcachofa cocida",               "Artichoke cooked",                53,  2.8, 11.0,  0.3, 6.9),
    ("Brote de soja / Frijol germinado", "Bean sprouts",                  30,  3.0,  5.9,  0.2, 1.8),
    ("Choclo baby / Mini choclo",      "Baby corn",                       26,  2.5,  5.6,  0.3, 2.9),

    # ── ACEITES Y GRASAS ─────────────────────────────────────────────────────
    ("Aceite de oliva",                "Olive oil",                      884,  0.0,  0.0, 100.0, 0.0),
    ("Aceite de canola",               "Canola oil",                     884,  0.0,  0.0, 100.0, 0.0),
    ("Aceite de girasol",              "Sunflower oil",                  884,  0.0,  0.0, 100.0, 0.0),
    ("Aceite de maravilla",            "Safflower oil",                  884,  0.0,  0.0, 100.0, 0.0),
    ("Aceite de coco",                 "Coconut oil",                    862,  0.0,  0.0, 100.0, 0.0),
    ("Mantequilla sin sal",            "Unsalted butter",                717,  0.9,  0.1, 81.1,  0.0),
    ("Margarina vegetal",              "Margarine",                      718,  0.2,  0.7, 80.7,  0.0),
    ("Aceite de palta / aguacate",     "Avocado oil",                    884,  0.0,  0.0, 100.0, 0.0),
    ("Mayonesa",                       "Mayonnaise",                     680,  1.0,  0.6, 74.9,  0.0),
    ("Aceite de sésamo",               "Sesame oil",                     884,  0.0,  0.0, 100.0, 0.0),

    # ── FRUTOS SECOS Y SEMILLAS ───────────────────────────────────────────────
    ("Almendras",                      "Almonds",                        579, 21.2, 21.6, 49.9, 12.5),
    ("Nueces",                         "Walnuts",                        654, 15.2, 13.7, 65.2,  6.7),
    ("Maní / Cacahuates",              "Peanuts",                        567, 25.8, 16.1, 49.2,  8.5),
    ("Mantequilla de maní",            "Peanut butter",                  588, 25.1, 20.1, 50.4,  6.0),
    ("Mantequilla de almendras",       "Almond butter",                  614, 21.0, 18.8, 55.5,  10.3),
    ("Cajú / Castañas de cajú",        "Cashews",                        553, 18.2, 30.2, 43.9,  3.3),
    ("Pistacho sin sal",               "Pistachios unsalted",            562, 20.2, 27.5, 45.4, 10.3),
    ("Avellanas",                      "Hazelnuts",                      628, 15.0, 16.7, 60.8,  9.7),
    ("Semillas de girasol",            "Sunflower seeds",                584, 20.8, 20.0, 51.5,  8.6),
    ("Semillas de sésamo",             "Sesame seeds",                   573, 17.7, 23.5, 49.7,  11.8),
    ("Semillas de zapallo / Pepitas",  "Pumpkin seeds",                  559, 30.2, 10.7, 49.1,  6.0),
    ("Tahini",                         "Tahini",                         595, 17.0, 21.2, 53.8,  9.3),

    # ── AZÚCARES Y ENDULZANTES ───────────────────────────────────────────────
    ("Azúcar blanca",                  "White sugar",                    387,  0.0, 100.0, 0.0,  0.0),
    ("Azúcar morena / rubio",          "Brown sugar",                    380,  0.0, 97.3, 0.0,   0.0),
    ("Miel",                           "Honey",                          304,  0.3, 82.4, 0.0,   0.2),
    ("Stevia en polvo",                "Powdered stevia",                  0,  0.0,  0.0, 0.0,   0.0),
    ("Mermelada de frutillas",         "Strawberry jam",                 278,  0.4, 69.0, 0.1,   1.0),
    ("Mermelada de durazno",           "Peach jam",                      250,  0.4, 65.0, 0.1,   0.8),
    ("Nutella / crema de avellanas",   "Hazelnut spread",                539,  6.3, 57.5, 30.9,  3.4),

    # ── BEBIDAS ───────────────────────────────────────────────────────────────
    ("Agua",                           "Water",                            0,  0.0,  0.0, 0.0,   0.0),
    ("Leche de almendras sin azúcar",  "Unsweetened almond milk",         15,  0.6,  0.6, 1.2,   0.3),
    ("Leche de soja sin azúcar",       "Unsweetened soy milk",            33,  3.3,  1.7, 1.8,   0.4),
    ("Leche de avena sin azúcar",      "Unsweetened oat milk",            40,  1.0,  6.7, 1.5,   0.5),
    ("Jugo de naranja natural",        "Fresh orange juice",              45,  0.7, 10.4, 0.2,   0.2),
    ("Jugo de manzana",                "Apple juice",                     46,  0.1, 11.3, 0.1,   0.2),
    ("Café solo (espresso)",           "Espresso coffee",                  9,  0.1,  1.7, 0.2,   0.0),
    ("Café con leche (mitad)",         "Café au lait half milk",          30,  1.6,  2.9, 1.5,   0.0),
    ("Té sin azúcar",                  "Unsweetened tea",                  1,  0.0,  0.3, 0.0,   0.0),
    ("Té verde",                       "Green tea",                        1,  0.2,  0.2, 0.0,   0.0),
    ("Bebida cola (regular)",          "Regular cola drink",              42,  0.0, 10.6, 0.0,   0.0),
    ("Bebida cola light / zero",       "Diet cola drink",                  1,  0.1,  0.1, 0.0,   0.0),
    ("Jugo de tomate",                 "Tomato juice",                    17,  0.9,  4.2, 0.1,   0.4),
    ("Agua mineral con gas",           "Sparkling mineral water",          0,  0.0,  0.0, 0.0,   0.0),

    # ── COMIDAS PREPARADAS COMUNES ────────────────────────────────────────────
    ("Arroz con pollo (casero)",       "Homemade rice with chicken",     165,  8.5, 22.0, 4.2,  0.8),
    ("Ensalada de pollo con mayonesa", "Chicken salad with mayo",        210, 15.0,  3.0, 15.0, 0.5),
    ("Hamburguesa (solo carne 100g)",  "Hamburger patty 100g",           295, 20.5,  0.0, 23.0, 0.0),
    ("Pizza margarita (por porción)",  "Margherita pizza slice",         266, 11.0, 33.0, 10.0, 2.0),
    ("Sopa de pollo casera",           "Homemade chicken soup",           35,  3.5,  3.0, 0.8,  0.5),
    ("Puré de papas con mantequilla",  "Mashed potatoes with butter",    113,  2.2, 17.0, 4.0,  1.5),
    ("Tortilla española",              "Spanish omelette",               185, 11.0,  7.0, 13.5, 0.7),
    ("Sushi (maki roll, 6 piezas)",    "Sushi maki roll 6 pieces",       140,  6.0, 27.5, 0.5,  0.5),
    ("Wrap de pollo y verduras",       "Chicken veggie wrap",            220, 14.0, 26.0, 6.5,  2.5),
    ("Tacos de pollo (1 taco)",        "Chicken taco 1 piece",           210, 12.0, 22.0, 7.5,  2.0),

    # ── SNACKS Y DULCES ──────────────────────────────────────────────────────
    ("Chocolate negro 70%",            "Dark chocolate 70%",             600,  7.8, 45.9, 42.6, 10.9),
    ("Chocolate con leche",            "Milk chocolate",                 535,  7.7, 59.4, 29.7,  3.4),
    ("Helado de vainilla",             "Vanilla ice cream",              207,  3.5, 23.6, 11.0,  0.5),
    ("Galletas de chocolate",          "Chocolate chip cookies",         488,  5.7, 66.3, 23.5,  2.3),
    ("Chips de papa",                  "Potato chips",                   547,  7.0, 52.9, 35.0,  4.4),
    ("Barra de cereal",                "Granola bar",                    387,  5.8, 67.4, 10.0,  4.0),
    ("Yogur con frutas (industrial)",  "Fruit yogurt",                   100,  3.3, 16.5, 2.1,   0.3),
    ("Proteína whey en polvo",         "Whey protein powder",            400, 80.0, 8.0,  5.0,   0.0),
    ("Proteína de soja en polvo",      "Soy protein powder",             338, 80.7, 7.1,  1.0,   3.4),

    # ── SALSAS Y CONDIMENTOS ─────────────────────────────────────────────────
    ("Salsa de tomate (sin azúcar)",   "Plain tomato sauce",              29,  1.5,  6.3, 0.3,  1.5),
    ("Ketchup",                        "Ketchup",                        112,  1.3, 26.5, 0.1,  0.3),
    ("Mostaza",                        "Mustard",                         66,  4.4,  5.8, 3.7,  3.2),
    ("Salsa de soja",                  "Soy sauce",                       53,  8.1,  4.9, 0.6,  0.8),
    ("Vinagre de manzana",             "Apple cider vinegar",             22,  0.0,  0.9, 0.0,  0.0),
    ("Aceitunas en salmuera",          "Brined olives",                  145,  1.0,  3.8, 15.3, 3.3),
    ("Hummus (comercial)",             "Commercial hummus",              166,  7.9, 14.3, 9.6,  6.0),
]

# ── Alimentos chilenos ────────────────────────────────────────────────────────
_CHILEAN_FOODS = [
    # (nombre_es, nombre_en, kcal, prot, carb, gras, fibra)
    ("Marraqueta (pan de 4 tiras)",    "Chilean bread roll",             275,  9.0, 55.0, 2.5, 2.0),
    ("Hallulla",                       "Chilean flat bread",             290,  8.5, 57.0, 3.0, 1.5),
    ("Pan de molde blanco (chileno)",  "Chilean white sandwich bread",   265,  8.0, 50.0, 3.5, 2.0),
    ("Sopaipilla frita",               "Fried pumpkin flatbread",        350,  5.0, 45.0, 17.0, 2.0),
    ("Sopaipilla al horno",            "Baked pumpkin flatbread",        240,  5.5, 42.0, 6.0, 2.5),
    ("Mote de trigo cocido",           "Cooked husked wheat",            130,  4.0, 27.0, 0.7, 2.5),
    ("Chuchoca (harina de maíz seca)", "Dried corn flour Chilean",       360,  8.0, 74.0, 3.5, 5.0),
    ("Manjar / Dulce de leche",        "Dulce de leche",                 310,  6.5, 56.0, 7.5, 0.0),
    ("Chancaca (azúcar de caña)",      "Raw cane sugar block",           380,  0.5, 95.0, 0.2, 0.0),
    ("Not Milk original",              "Plant-based milk original",       39,  0.8,  5.0, 1.5, 0.5),
    ("Not Milk avena",                 "Oat plant milk Not Milk",         42,  0.5,  6.5, 1.5, 0.5),
    ("Bebida vegetal de avena",        "Generic oat drink",               40,  1.0,  6.0, 1.2, 0.5),
    ("Humitas frescas",                "Fresh corn tamales",             170,  4.5, 28.0, 5.0, 2.0),
    ("Empanada de pino al horno",      "Baked beef empanada",            295, 11.0, 32.0, 14.0, 1.5),
    ("Empanada de queso al horno",     "Baked cheese empanada",          305, 10.0, 33.0, 15.0, 1.0),
    ("Empanada frita de queso",        "Fried cheese empanada",          380, 10.0, 35.0, 22.0, 1.0),
    ("Cazuela de vacuno (con verduras)","Beef cazuela stew",              95,  8.0,  8.0,  3.5, 1.5),
    ("Charquicán",                     "Chilean beef and vegetable stew",115,  8.0, 12.0,  4.0, 2.5),
    ("Porotos granados",               "Chilean bean stew",              135,  6.5, 22.0,  3.0, 6.0),
    ("Porotos con rienda",             "Beans with pasta",               145,  7.5, 24.0,  2.5, 5.0),
    ("Lentejas cocidas estilo chileno","Chilean lentils cooked",         116,  9.0, 20.0,  0.4, 7.9),
    ("Garbanzos con espinaca",         "Chickpeas with spinach",         150,  8.5, 21.0,  3.5, 6.5),
    ("Chirimoya pulpa",                "Cherimoya pulp",                  75,  1.5, 17.7,  0.5, 3.0),
    ("Lúcuma pulpa fresca",            "Lucuma fresh pulp",               99,  1.5, 23.4,  0.5, 2.4),
    ("Tuna / Higo chumbo",             "Prickly pear",                    41,  0.8,  9.6,  0.5, 3.6),
    ("Guinda / Cereza ácida",          "Sour cherry",                     50,  1.0, 12.2,  0.3, 1.6),
    ("Maqui fruto fresco",             "Fresh maqui berry",               40,  0.5,  8.5,  0.4, 3.5),
    ("Rosa mosqueta",                  "Rose hip",                       162,  1.6, 38.2,  0.6, 24.1),
    ("Cochayuyo seco",                 "Dried bull kelp",                160,  8.0, 30.0,  1.5, 7.0),
    ("Cochayuyo cocido",               "Cooked bull kelp",                35,  2.0,  6.5,  0.4, 2.5),
    ("Merluza a la plancha",           "Grilled hake",                   115, 23.0,  0.0,  2.5, 0.0),
    ("Reineta al horno",               "Baked bream fish",               135, 21.0,  0.0,  5.5, 0.0),
    ("Congrio colorado cocido",        "Cooked red conger eel",          145, 22.0,  0.0,  6.0, 0.0),
    ("Zapallo camote cocido",          "Cooked kabocha squash",           34,  1.1,  8.0,  0.1, 1.5),
    ("Milcao cocido",                  "Cooked potato pancake",          220,  3.5, 42.0,  4.5, 2.0),
    ("Arroz con leche casero",         "Rice pudding Chilean style",     155,  4.0, 27.5,  3.5, 0.2),
    ("Queque de naranja casero",       "Homemade orange cake",           380,  6.0, 58.0, 14.0, 1.0),
    ("Leche Colun entera",             "Whole milk Colun brand",          65,  3.1,  4.8,  3.6, 0.0),
    ("Yogur natural entero chileno",   "Chilean plain whole yogurt",      72,  4.0,  5.2,  3.8, 0.0),
    ("Papas fritas caseras",           "Homemade french fries",          312,  3.4, 38.0, 17.0, 3.5),
    ("Pebre condimento",               "Chilean cilantro salsa",          35,  1.2,  5.5,  1.0, 1.5),
    ("Tomate cherry nacional",         "Chilean cherry tomato",           18,  0.9,  3.9,  0.2, 1.2),
    ("Pan de centeno negro",           "Dark rye bread Chile",           259,  8.5, 48.0,  3.3, 6.2),
    ("Cecina de vacuno",               "Beef cold cut",                  295, 18.0,  2.5, 24.0, 0.0),
    ("Vienesa de cerdo",               "Pork frankfurter",               290, 13.0,  4.0, 25.0, 0.0),
    ("Jamón de pierna laminado",       "Sliced leg ham",                 145, 19.0,  2.5,  6.5, 0.0),
    ("Queso gauda chanco",             "Chilean gauda chanco cheese",    357, 25.0,  1.5, 28.0, 0.0),
    ("Valdiviano sopa",                "Valdiviano beef soup",            88,  7.5,  6.5,  3.5, 1.0),
    ("Mote de maíz cocido",            "Cooked hominy corn",             115,  3.1, 24.0,  0.8, 3.6),
    ("Api bebida de uva",              "Cooked grape drink api",          68,  0.2, 16.8,  0.1, 0.0),
    ("Mote con huesillos bebida",      "Wheat with dried peaches drink",  85,  2.0, 20.0,  0.2, 1.5),
]

# ── USDA nutrient IDs (para importación opcional del JSON oficial) ─────────────
_NID = {
    "calorias": 1008, "proteinas_g": 1003, "grasas_g": 1004,
    "carbohidratos_g": 1005, "fibra_g": 1079, "azucares_g": 2000,
    "sodio_mg": 1093, "calcio_mg": 1087, "hierro_mg": 1089,
    "vitamina_c_mg": 1162, "vitamina_a_mcg": 1106,
}
_SUGAR_FALLBACK = 1063

# ── Traducciones para USDA JSON opcional ─────────────────────────────────────
_TRADUCCIONES = {
    "Rice, white, long-grain, regular, cooked, unenriched": "Arroz blanco cocido (USDA)",
    "Chicken, broilers or fryers, breast, meat only, cooked, roasted": "Pechuga de pollo asada (USDA)",
    "Beef, ground, 85% lean meat / 15% fat, pan-browned": "Carne molida 85% cocida (USDA)",
    "Fish, salmon, Atlantic, farmed, cooked, dry heat": "Salmón cocido (USDA)",
    "Fish, tuna, light, canned in water, drained solids": "Atún en agua lata (USDA)",
    "Egg, whole, raw, fresh": "Huevo entero crudo (USDA)",
    "Lentils, mature seeds, cooked, boiled, without salt": "Lentejas cocidas (USDA)",
}


def _find_json(folder: str) -> Optional[str]:
    for f in os.listdir(folder):
        if f.startswith("FoodData_Central_sr_legacy") and f.endswith(".json"):
            return os.path.join(folder, f)
    return None


def _get_db_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "nutricionista.db")


def insert_builtin(conn: sqlite3.Connection):
    cur = conn.cursor()

    # Integradas
    cur.execute("DELETE FROM alimentos_db WHERE fuente = 'integrado'")
    cur.executemany("""
        INSERT INTO alimentos_db
            (nombre_es, nombre_en, calorias, proteinas_g, carbohidratos_g,
             grasas_g, fibra_g, fuente, es_personalizado)
        VALUES (?,?,?,?,?,?,?,'integrado',0)
    """, _BUILTIN_FOODS)
    print(f"  {len(_BUILTIN_FOODS)} alimentos integrados insertados.")

    # Chilenas
    cur.execute("DELETE FROM alimentos_db WHERE fuente = 'chileno'")
    cur.executemany("""
        INSERT INTO alimentos_db
            (nombre_es, nombre_en, calorias, proteinas_g, carbohidratos_g,
             grasas_g, fibra_g, fuente, es_personalizado)
        VALUES (?,?,?,?,?,?,?,'chileno',0)
    """, _CHILEAN_FOODS)
    print(f"  {len(_CHILEAN_FOODS)} alimentos chilenos insertados.")

    conn.commit()


def _extract_nutrients(food_nutrients: list) -> dict:
    nid_to_field = {v: k for k, v in _NID.items()}
    result = {k: 0.0 for k in _NID}
    for fn in food_nutrients:
        nid = fn.get("nutrient", {}).get("id")
        amount = fn.get("amount", 0) or 0
        if nid in nid_to_field:
            result[nid_to_field[nid]] = round(float(amount), 3)
        elif nid == _SUGAR_FALLBACK and result.get("azucares_g", 0) == 0:
            result["azucares_g"] = round(float(amount), 3)
    return result


def import_usda_json(json_path: str, conn: sqlite3.Connection):
    print(f"Leyendo {json_path} ...")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    foods = data.get("SRLegacyFoods", [])
    print(f"  {len(foods)} alimentos en el JSON USDA.")
    cur = conn.cursor()
    cur.execute("DELETE FROM alimentos_db WHERE fuente = 'USDA'")
    batch = []
    for food in foods:
        desc_en = food.get("description", "").strip()
        nombre_es = _TRADUCCIONES.get(desc_en, desc_en)
        n = _extract_nutrients(food.get("foodNutrients", []))
        batch.append((nombre_es, desc_en,
                      n["calorias"], n["proteinas_g"], n["carbohidratos_g"],
                      n["grasas_g"], n["fibra_g"], n["azucares_g"],
                      n["sodio_mg"], n["calcio_mg"], n["hierro_mg"],
                      n["vitamina_c_mg"], n["vitamina_a_mcg"]))
    cur.executemany("""
        INSERT INTO alimentos_db
            (nombre_es, nombre_en, calorias, proteinas_g, carbohidratos_g,
             grasas_g, fibra_g, azucares_g, sodio_mg, calcio_mg, hierro_mg,
             vitamina_c_mg, vitamina_a_mcg, fuente, es_personalizado)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'USDA',0)
    """, batch)
    conn.commit()
    print(f"  {len(batch)} alimentos USDA importados.")


if __name__ == "__main__":
    db_path = _get_db_path()
    # Always run initialize_db to ensure all tables/migrations are applied
    sys.path.insert(0, os.path.dirname(db_path))
    import database.db_manager as db_manager
    db_manager.initialize_db()
    print("Base de datos inicializada.")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    insert_builtin(conn)

    # Optional: import full USDA JSON if provided or found
    json_path = sys.argv[1] if len(sys.argv) > 1 else _find_json(os.path.dirname(db_path))
    if json_path and os.path.exists(json_path):
        import_usda_json(json_path, conn)

    conn.close()

    # Summary
    conn2 = sqlite3.connect(db_path)
    total = conn2.execute("SELECT COUNT(*) FROM alimentos_db").fetchone()[0]
    conn2.close()
    print(f"\nTotal de alimentos en la base de datos: {total}")
    print("Listo. Reinicia la app para usar el buscador.")
