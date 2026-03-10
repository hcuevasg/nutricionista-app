"""
import_usda.py — Importar base de datos nutricional USDA SR Legacy a SQLite.

USO:
  1. Descargar SR Legacy JSON desde:
     https://fdc.nal.usda.gov/download-datasets.html
     → "SR Legacy" → Download (JSON)
  2. Descomprimir el ZIP (obtienes: FoodData_Central_sr_legacy_food_json_*.json)
  3. Ejecutar:
     python import_usda.py ruta/al/archivo.json
     o simplemente:
     python import_usda.py
     (busca automáticamente cualquier FoodData_Central_sr_legacy*.json en la carpeta)
"""

import json
import os
import sys
import sqlite3

# ── Nutrient IDs in USDA FDC SR Legacy ───────────────────────────────────────
_NID = {
    "calorias":        1008,   # Energy, kcal
    "proteinas_g":     1003,   # Protein, g
    "grasas_g":        1004,   # Total lipid (fat), g
    "carbohidratos_g": 1005,   # Carbohydrate by difference, g
    "fibra_g":         1079,   # Fiber, total dietary, g
    "azucares_g":      2000,   # Sugars, total (or 1063 fallback)
    "sodio_mg":        1093,   # Sodium, mg
    "calcio_mg":       1087,   # Calcium, mg
    "hierro_mg":       1089,   # Iron, mg
    "vitamina_c_mg":   1162,   # Vitamin C, mg
    "vitamina_a_mcg":  1106,   # Vitamin A, RAE, mcg
}
_SUGAR_FALLBACK = 1063

# ── Traducciones de los 300 alimentos más comunes ─────────────────────────────
_TRADUCCIONES = {
    # Cereales y granos
    "Rice, white, long-grain, regular, raw, unenriched": "Arroz blanco crudo",
    "Rice, white, long-grain, regular, cooked, unenriched": "Arroz blanco cocido",
    "Rice, brown, long-grain, raw": "Arroz integral crudo",
    "Rice, brown, long-grain, cooked": "Arroz integral cocido",
    "Wheat flour, white, all-purpose, unenriched": "Harina de trigo blanca",
    "Wheat flour, whole-grain": "Harina de trigo integral",
    "Oats": "Avena cruda",
    "Oatmeal, instant, fortified, plain": "Avena instantánea",
    "Bread, white, commercially prepared": "Pan blanco",
    "Bread, whole-wheat, commercially prepared": "Pan integral",
    "Pasta, dry, unenriched": "Pasta seca",
    "Pasta, cooked, unenriched, without added salt": "Pasta cocida",
    "Cornmeal, whole-grain, yellow": "Harina de maíz integral",
    "Quinoa, cooked": "Quinoa cocida",
    "Quinoa, uncooked": "Quinoa cruda",
    "Barley, pearled, raw": "Cebada perlada cruda",
    "Barley, pearled, cooked": "Cebada perlada cocida",

    # Carnes rojas
    "Beef, ground, 85% lean meat / 15% fat, raw": "Carne molida 85% magra cruda",
    "Beef, ground, 85% lean meat / 15% fat, pan-browned": "Carne molida cocida",
    "Beef, loin, tenderloin steak, separable lean and fat, trimmed to 1/8\" fat, all grades, raw":
        "Filete de vacuno crudo",
    "Beef, chuck, arm pot roast, separable lean and fat, trimmed to 1/4\" fat, all grades, raw":
        "Paleta de vacuno cruda",
    "Pork, fresh, loin, whole, separable lean and fat, raw": "Lomo de cerdo crudo",
    "Pork, fresh, loin, whole, separable lean and fat, cooked, roasted": "Lomo de cerdo asado",
    "Pork, cured, ham, whole, separable lean and fat, roasted": "Jamón de cerdo asado",
    "Lamb, domestic, composite of trimmed retail cuts, separable lean and fat, raw":
        "Cordero crudo",

    # Aves
    "Chicken, broilers or fryers, breast, meat only, raw": "Pechuga de pollo cruda",
    "Chicken, broilers or fryers, breast, meat only, cooked, roasted": "Pechuga de pollo asada",
    "Chicken, broilers or fryers, thigh, meat only, raw": "Muslo de pollo crudo",
    "Chicken, broilers or fryers, thigh, meat only, cooked, roasted": "Muslo de pollo asado",
    "Chicken, broilers or fryers, whole, meat and skin, raw": "Pollo entero crudo",
    "Turkey, all classes, breast, meat only, raw": "Pechuga de pavo cruda",
    "Turkey, all classes, breast, meat only, cooked, roasted": "Pechuga de pavo cocida",

    # Pescados y mariscos
    "Fish, salmon, Atlantic, farmed, raw": "Salmón del Atlántico crudo",
    "Fish, salmon, Atlantic, farmed, cooked, dry heat": "Salmón cocido",
    "Fish, tuna, light, canned in water, drained solids": "Atún en agua (lata)",
    "Fish, tuna, light, canned in oil, drained solids": "Atún en aceite (lata)",
    "Fish, cod, Atlantic, raw": "Bacalao crudo",
    "Fish, tilapia, raw": "Tilapia cruda",
    "Fish, tilapia, cooked, dry heat": "Tilapia cocida",
    "Shrimp, mixed species, raw": "Camarones crudos",
    "Shrimp, mixed species, cooked, moist heat": "Camarones cocidos",

    # Lácteos
    "Milk, whole, 3.25% milkfat, without added vitamin A and vitamin D": "Leche entera",
    "Milk, reduced fat, fluid, 2% milkfat, without added vitamin A and vitamin D": "Leche semidescremada 2%",
    "Milk, nonfat, fluid, without added vitamin A and vitamin D (fat free or skim)": "Leche descremada",
    "Cheese, cheddar": "Queso cheddar",
    "Cheese, mozzarella, whole milk": "Queso mozzarella",
    "Yogurt, plain, whole milk": "Yogur natural entero",
    "Yogurt, plain, low fat": "Yogur natural bajo en grasa",
    "Butter, without salt": "Mantequilla sin sal",
    "Cream, fluid, heavy whipping": "Crema de leche",
    "Cream cheese": "Queso crema",
    "Egg, whole, raw, fresh": "Huevo entero crudo",
    "Egg, whole, cooked, hard-boiled": "Huevo duro",
    "Egg, white, raw, fresh": "Clara de huevo cruda",
    "Egg yolk, raw, fresh": "Yema de huevo cruda",

    # Legumbres
    "Lentils, raw": "Lentejas crudas",
    "Lentils, mature seeds, cooked, boiled, without salt": "Lentejas cocidas",
    "Chickpeas (garbanzo beans, bengal gram), mature seeds, raw": "Garbanzos crudos",
    "Chickpeas (garbanzo beans, bengal gram), mature seeds, cooked, boiled, without salt":
        "Garbanzos cocidos",
    "Beans, black, mature seeds, raw": "Porotos negros crudos",
    "Beans, black, mature seeds, cooked, boiled, without salt": "Porotos negros cocidos",
    "Beans, kidney, red, mature seeds, raw": "Porotos rojos crudos",
    "Beans, kidney, red, mature seeds, cooked, boiled, without salt": "Porotos rojos cocidos",
    "Peas, green, raw": "Arvejas frescas",
    "Peas, green, frozen, unprepared": "Arvejas congeladas",
    "Soybeans, mature seeds, raw": "Soja cruda",

    # Frutas
    "Apples, raw, with skin": "Manzana con cáscara",
    "Bananas, raw": "Plátano / Banana",
    "Oranges, raw, all commercial varieties": "Naranja",
    "Strawberries, raw": "Frutillas / Fresas",
    "Grapes, red or green (European type), raw": "Uvas",
    "Watermelon, raw": "Sandía",
    "Pineapple, raw, all varieties": "Piña / Ananá",
    "Mango, raw": "Mango",
    "Avocado, raw, all commercial varieties": "Palta / Aguacate",
    "Blueberries, raw": "Arándanos",
    "Pears, raw": "Pera",
    "Peaches, raw": "Durazno / Melocotón",
    "Plums, raw": "Ciruela fresca",
    "Kiwifruit, ZESPRI SunGold, raw": "Kiwi dorado",
    "Kiwifruit, green, raw": "Kiwi verde",
    "Lemon, raw, without peel": "Limón sin cáscara",
    "Lime, raw": "Lima",
    "Cherries, sweet, raw": "Cerezas dulces",
    "Raspberries, raw": "Frambuesas",

    # Verduras
    "Tomatoes, red, ripe, raw, year round average": "Tomate",
    "Spinach, raw": "Espinaca cruda",
    "Broccoli, raw": "Brócoli crudo",
    "Broccoli, cooked, boiled, drained, without salt": "Brócoli cocido",
    "Carrots, raw": "Zanahoria",
    "Carrots, cooked, boiled, drained, without salt": "Zanahoria cocida",
    "Lettuce, iceberg (includes crisphead types), raw": "Lechuga iceberg",
    "Lettuce, romaine or cos, raw": "Lechuga romana",
    "Onions, raw": "Cebolla",
    "Garlic, raw": "Ajo",
    "Potatoes, flesh and skin, raw": "Papa con cáscara cruda",
    "Potatoes, boiled, cooked in skin, flesh, without salt": "Papa cocida con cáscara",
    "Sweet potato, raw, unprepared": "Camote / Batata crudo",
    "Sweet potato, cooked, boiled, without skin": "Camote cocido sin cáscara",
    "Corn, sweet, yellow, raw": "Choclo amarillo",
    "Corn, sweet, yellow, frozen, kernels cut off cob, unprepared": "Choclo congelado",
    "Cucumber, with peel, raw": "Pepino con cáscara",
    "Zucchini, baby, raw": "Zucchini / Zapallito crudo",
    "Squash, winter, all varieties, raw": "Zapallo crudo",
    "Bell peppers, red, raw": "Pimentón rojo",
    "Bell peppers, green, raw": "Pimentón verde",
    "Mushrooms, white, raw": "Champiñones blancos",
    "Celery, raw": "Apio",
    "Cabbage, raw": "Repollo crudo",
    "Cauliflower, raw": "Coliflor cruda",
    "Eggplant, raw": "Berenjena",
    "Beets, raw": "Betarraga / Remolacha cruda",

    # Aceites y grasas
    "Oil, olive, salad or cooking": "Aceite de oliva",
    "Oil, canola": "Aceite de canola",
    "Oil, sunflower, linoleic (less than 60%)": "Aceite de girasol",
    "Oil, coconut": "Aceite de coco",

    # Frutos secos y semillas
    "Nuts, almonds": "Almendras",
    "Nuts, walnuts, english": "Nueces",
    "Nuts, cashew nuts, raw": "Cajú / Castañas de cajú",
    "Nuts, peanuts, all types, raw": "Maní / Cacahuates",
    "Peanut butter, smooth style, without salt": "Mantequilla de maní",
    "Seeds, chia seeds, dried": "Semillas de chía",
    "Seeds, flaxseed": "Semillas de linaza",
    "Seeds, sunflower seed kernels, dried": "Semillas de girasol",
    "Seeds, sesame seeds, whole, dried": "Semillas de sésamo",

    # Azúcares
    "Sugars, granulated": "Azúcar granulada",
    "Honey": "Miel",

    # Bebidas
    "Coffee, brewed from grounds, prepared with tap water": "Café preparado",
    "Tea, black, brewed": "Té negro",
    "Beverages, water, tap, drinking": "Agua",
}


def _find_json(folder: str) -> Optional[str]:
    for f in os.listdir(folder):
        if f.startswith("FoodData_Central_sr_legacy") and f.endswith(".json"):
            return os.path.join(folder, f)
    return None


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


def import_usda(json_path: str, db_path: str):
    print(f"Leyendo {json_path} ...")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    foods = data.get("SRLegacyFoods", [])
    print(f"  {len(foods)} alimentos encontrados en el JSON.")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Clear existing USDA data (re-import safe)
    cur.execute("DELETE FROM alimentos_db WHERE fuente = 'USDA'")
    conn.commit()

    batch = []
    for food in foods:
        desc_en = food.get("description", "").strip()
        nombre_es = _TRADUCCIONES.get(desc_en, "")
        nutrients = _extract_nutrients(food.get("foodNutrients", []))
        batch.append((
            nombre_es or desc_en,  # nombre_es (fallback to English if no translation)
            desc_en,               # nombre_en
            nutrients["calorias"],
            nutrients["proteinas_g"],
            nutrients["carbohidratos_g"],
            nutrients["grasas_g"],
            nutrients["fibra_g"],
            nutrients["azucares_g"],
            nutrients["sodio_mg"],
            nutrients["calcio_mg"],
            nutrients["hierro_mg"],
            nutrients["vitamina_c_mg"],
            nutrients["vitamina_a_mcg"],
            "USDA",
            0,
        ))

    cur.executemany("""
        INSERT INTO alimentos_db
            (nombre_es, nombre_en, calorias, proteinas_g, carbohidratos_g,
             grasas_g, fibra_g, azucares_g, sodio_mg, calcio_mg, hierro_mg,
             vitamina_c_mg, vitamina_a_mcg, fuente, es_personalizado)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, batch)
    conn.commit()
    print(f"  {len(batch)} alimentos USDA importados.")

    _insert_chilean_foods(cur)
    conn.commit()
    conn.close()
    print("Importación completada.")


def _insert_chilean_foods(cur):
    """Inserta alimentos chilenos comunes no presentes en USDA."""
    chilean = [
        # (nombre_es, nombre_en, kcal, prot, carb, gras, fibra, azucar, sodio)
        ("Marraqueta (pan)", "Chilean bread roll", 275, 9.0, 55.0, 2.5, 2.0, 1.5, 490),
        ("Hallulla", "Chilean flat bread", 290, 8.5, 57.0, 3.0, 1.5, 1.0, 520),
        ("Pan de molde blanco", "White sandwich bread", 265, 8.0, 50.0, 3.5, 2.0, 4.0, 480),
        ("Sopaipilla frita", "Fried pumpkin flatbread", 350, 5.0, 45.0, 17.0, 2.0, 1.0, 320),
        ("Sopaipilla al horno", "Baked pumpkin flatbread", 240, 5.5, 42.0, 6.0, 2.5, 1.0, 280),
        ("Mote de trigo cocido", "Cooked husked wheat", 130, 4.0, 27.0, 0.7, 2.5, 0.5, 5),
        ("Chuchoca (harina de maíz seca)", "Dried corn flour", 360, 8.0, 74.0, 3.5, 5.0, 1.0, 10),
        ("Manjar / Dulce de leche", "Dulce de leche", 310, 6.5, 56.0, 7.5, 0.0, 52.0, 85),
        ("Chancaca (azúcar de caña cruda)", "Raw cane sugar block", 380, 0.5, 95.0, 0.2, 0.0, 90.0, 10),
        ("Not Milk original (bebida vegetal)", "Plant-based milk original", 39, 0.8, 5.0, 1.5, 0.5, 4.5, 80),
        ("Not Milk avena", "Oat-based plant milk", 42, 0.5, 6.5, 1.5, 0.5, 3.5, 75),
        ("Bebida vegetal de avena genérica", "Generic oat drink", 40, 1.0, 6.0, 1.2, 0.5, 3.0, 60),
        ("Humitas frescas", "Fresh corn tamales", 170, 4.5, 28.0, 5.0, 2.0, 2.0, 280),
        ("Empanada de pino al horno", "Baked beef empanada", 295, 11.0, 32.0, 14.0, 1.5, 1.5, 480),
        ("Empanada de queso al horno", "Baked cheese empanada", 305, 10.0, 33.0, 15.0, 1.0, 1.5, 520),
        ("Empanada frita de queso", "Fried cheese empanada", 380, 10.0, 35.0, 22.0, 1.0, 1.5, 450),
        ("Cazuela de vacuno (sin hueso)", "Beef cazuela stew", 95, 8.0, 8.0, 3.5, 1.5, 1.0, 310),
        ("Charquicán", "Chilean beef and vegetable stew", 115, 8.0, 12.0, 4.0, 2.5, 1.5, 370),
        ("Porotos granados", "Chilean bean stew", 135, 6.5, 22.0, 3.0, 6.0, 2.0, 290),
        ("Porotos con rienda", "Beans with pasta", 145, 7.5, 24.0, 2.5, 5.0, 1.5, 310),
        ("Lentejas cocidas (estilo chileno)", "Cooked lentils Chilean style", 116, 9.0, 20.0, 0.4, 7.9, 1.8, 240),
        ("Garbanzos cocidos", "Cooked chickpeas", 164, 8.9, 27.4, 2.6, 7.6, 4.8, 240),
        ("Chirimoya (pulpa)", "Cherimoya pulp", 75, 1.5, 17.7, 0.5, 3.0, 12.5, 7),
        ("Lúcuma (pulpa fresca)", "Lucuma fresh pulp", 99, 1.5, 23.4, 0.5, 2.4, 10.0, 12),
        ("Tuna / Higo chumbo (pulpa)", "Prickly pear pulp", 41, 0.8, 9.6, 0.5, 3.6, 7.0, 5),
        ("Guinda / Cereza ácida", "Sour cherry", 50, 1.0, 12.2, 0.3, 1.6, 8.5, 3),
        ("Maqui (fruto fresco)", "Maqui berry fresh", 40, 0.5, 8.5, 0.4, 3.5, 4.0, 2),
        ("Rosa mosqueta (fruto)", "Rose hip", 162, 1.6, 38.2, 0.6, 24.1, 0.0, 4),
        ("Cochayuyo seco", "Dried bull kelp seaweed", 160, 8.0, 30.0, 1.5, 7.0, 0.0, 2100),
        ("Cochayuyo cocido", "Cooked bull kelp seaweed", 35, 2.0, 6.5, 0.4, 2.5, 0.0, 450),
        ("Merluza a la plancha", "Grilled hake", 115, 23.0, 0.0, 2.5, 0.0, 0.0, 120),
        ("Reineta al horno", "Baked bream fish", 135, 21.0, 0.0, 5.5, 0.0, 0.0, 110),
        ("Congrio colorado cocido", "Cooked red conger eel", 145, 22.0, 0.0, 6.0, 0.0, 0.0, 115),
        ("Zapallo camote cocido", "Cooked kabocha squash", 34, 1.1, 8.0, 0.1, 1.5, 3.5, 2),
        ("Milcao (cocido)", "Cooked potato pancake", 220, 3.5, 42.0, 4.5, 2.0, 0.5, 180),
        ("Arroz con leche (casero)", "Rice pudding Chilean style", 155, 4.0, 27.5, 3.5, 0.2, 14.0, 55),
        ("Queque de naranja (casero)", "Homemade orange cake", 380, 6.0, 58.0, 14.0, 1.0, 35.0, 180),
        ("Api (bebida de uva cocida)", "Cooked grape drink", 68, 0.2, 16.8, 0.1, 0.0, 15.0, 5),
        ("Leche Colun entera", "Whole milk Colun", 65, 3.1, 4.8, 3.6, 0.0, 4.8, 44),
        ("Yogur natural entero (chileno)", "Chilean plain whole yogurt", 72, 4.0, 5.2, 3.8, 0.0, 5.0, 46),
        ("Papas fritas caseras", "Homemade french fries", 312, 3.4, 38.0, 17.0, 3.5, 0.5, 290),
        ("Valdiviano (sopa)", "Valdiviano beef soup", 88, 7.5, 6.5, 3.5, 1.0, 1.5, 420),
        ("Mote de maíz cocido", "Cooked hominy corn", 115, 3.1, 24.0, 0.8, 3.6, 0.8, 5),
        ("Pebre (condimento)", "Chilean cilantro salsa", 35, 1.2, 5.5, 1.0, 1.5, 2.5, 280),
        ("Tomate cherry nacional", "Chilean cherry tomato", 18, 0.9, 3.9, 0.2, 1.2, 2.6, 5),
        ("Pan de centeno (negro)", "Dark rye bread", 259, 8.5, 48.0, 3.3, 6.2, 3.5, 600),
        ("Avena en hojuelas (cruda)", "Raw rolled oats", 389, 16.9, 66.3, 6.9, 10.6, 0.0, 2),
        ("Cecina de vacuno (longaniza)", "Beef cold cut", 295, 18.0, 2.5, 24.0, 0.0, 1.0, 780),
        ("Vienesa de cerdo", "Pork frankfurter", 290, 13.0, 4.0, 25.0, 0.0, 1.5, 920),
        ("Jamón de pierna (laminado)", "Sliced leg ham", 145, 19.0, 2.5, 6.5, 0.0, 1.0, 850),
        ("Queso gauda (chanco)", "Chilean gauda cheese", 357, 25.0, 1.5, 28.0, 0.0, 0.5, 620),
    ]

    cur.execute("DELETE FROM alimentos_db WHERE fuente = 'chileno'")
    cur.executemany("""
        INSERT INTO alimentos_db
            (nombre_es, nombre_en, calorias, proteinas_g, carbohidratos_g,
             grasas_g, fibra_g, azucares_g, sodio_mg, fuente, es_personalizado)
        VALUES (?,?,?,?,?,?,?,?,?,'chileno',0)
    """, chilean)
    print(f"  {len(chilean)} alimentos chilenos insertados.")


if __name__ == "__main__":
    # Locate DB
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "nutricionista.db")

    if not os.path.exists(db_path):
        print(f"ERROR: No se encontró la base de datos en {db_path}")
        print("Ejecuta la app al menos una vez para crear la BD, luego vuelve a correr este script.")
        sys.exit(1)

    # Find JSON file
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = _find_json(script_dir)
        if not json_path:
            print("No se encontró el archivo JSON de USDA SR Legacy.")
            print("Descárgalo desde: https://fdc.nal.usda.gov/download-datasets.html")
            print("Sección: 'SR Legacy' → Download JSON → descomprime y coloca el .json aquí.")
            print("\nEjecutando igualmente con solo alimentos chilenos...")
            # Insert only Chilean foods
            conn = sqlite3.connect(db_path)
            _insert_chilean_foods(conn.cursor())
            conn.commit()
            conn.close()
            print("Alimentos chilenos insertados correctamente.")
            sys.exit(0)

    if not os.path.exists(json_path):
        print(f"ERROR: No se encontró {json_path}")
        sys.exit(1)

    import_usda(json_path, db_path)


# Type hint for _find_json return (Python 3.9 compatible)
from typing import Optional  # noqa: E402 — placed here to avoid circular concerns
