"""Menú en formato de planilla (N opciones con plato y texto) e importador de Excel."""
import json

import pytest

from tests.conftest import next_rut
from tests.test_ai import PAUTA
from tests.test_plantillas import _register

MENU_PLANILLA = {"desayuno": {"opciones": [
    {"plato": "Smoothie proteico", "lineas": [{"porcion": "1 Cereal", "texto": "40g Avena (1/2 T.)"},
                                              {"porcion": "1 Sup. Proteínas", "texto": "30g FicoNutrition"}]},
    {"plato": "Pan con palta", "lineas": [{"porcion": "1 Cereal", "texto": "50g Marraqueta (1/2 U.)"}]},
    {"plato": "Chia pudding <b>", "lineas": [{"porcion": "1 Omega 3", "texto": "15g Chía & <img src=x>"}]},
]}}


def test_pauta_with_planilla_menu_and_new_groups_renders_pdf(client):
    h = _register(client, "planilla_pdf")
    pid = client.post("/patients", json={"rut": next_rut(), "name": "Planilla", "sex": "F"}, headers=h).json()["id"]
    pauta = client.post(f"/pautas?patient_id={pid}", json={
        **PAUTA,
        "porciones_json": json.dumps({"cereales": 2, "omega_3": 1, "suplemento_proteico": 1}),
        "distribucion_json": json.dumps({"desayuno": {"cereales": 2, "omega_3": 1, "suplemento_proteico": 1}}),
        "menu_json": json.dumps(MENU_PLANILLA),
    }, headers=h).json()
    r = client.get(f"/pautas/{pid}/{pauta['id']}/pdf", headers=h)
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    # Editar el menú de planilla y que se conserve tal cual
    menu = json.loads(json.dumps(MENU_PLANILLA))
    menu["desayuno"]["opciones"][0]["plato"] = "Smoothie de frutos rojos"
    assert client.patch(f"/pautas/{pid}/{pauta['id']}/menu", json={"menu": menu}, headers=h).status_code == 200
    saved = json.loads(client.get(f"/pautas/{pid}/{pauta['id']}", headers=h).json()["menu_json"])
    assert saved["desayuno"]["opciones"][0]["plato"] == "Smoothie de frutos rojos"
    assert len(saved["desayuno"]["opciones"]) == 3


def test_importer_parses_horizontal_sheet(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts"))
    import importar_planillas as imp

    carpeta = tmp_path / "Vegetarianos" / "Horizontal vegan"
    carpeta.mkdir(parents=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "4 Comidas"
    rows = [
        [None, "DESAYUNO"],
        [None, "Porciones", "Opción 1", None, "Opción 2", None, "Opción 3"],
        [None, "1 Cereal", "SMOOTHIE", "40g Avena", "TOSTADAS", "2 Reb pan", "PORRIDGE", "1/2 T Avena"],
        [None, "1 Sup. Proteínas", None, "30g Fico", None, "30g Fico", None, "30g Fico"],
        [None, "1/4 Aeite", None, "5cc Aceite", None, "5cc Aceite", None, "5cc Aceite"],
        [None, "SNACK"],
        [None, "1,5 Cereales", "GALLETAS", "6 Galletas", "PAN", "1 Pan", "BARRA", "1 Barra"],
        [None, "ALMUERZO (Cuando comas legumbres, 2 tazas de guiso)"],
        [None, "1 1/2 Legumbre", "CURRY", "180g Garbanzos", "BOWL", "150g Lentejas", "GUISO", "1 T Porotos"],
        [None, "Verduras", None, "Brócoli", None, "Tomate", None, "Acelga"],
        [None, "CENA"],
        [None, "2 A. Proteicos", "TOFU", "100g Tofu", "SOYA", "30g Soya", "SEITÁN", "50g Seitán"],
    ]
    for r in rows:
        ws.append(r)
    wb.save(carpeta / "Vegan 1800 Kcal 90g P con Sup.xlsx")
    (tmp_path / "Gramajes plani").mkdir()
    plantillas, omitidos = imp.leer_carpeta(str(tmp_path))
    assert len(plantillas) == 1 and not omitidos
    p = plantillas[0]
    assert p["tipo_pauta"] == "vegano" and p["nombre"].startswith("Vegano · 1800 Kcal")
    dist = json.loads(p["distribucion_json"])
    assert dist["desayuno"] == {"cereales": 1.0, "suplemento_proteico": 1.0, "aceite_grasas": 0.25}
    assert dist["colacion1"] == {"cereales": 1.5}
    assert dist["almuerzo"] == {"legumbres": 1.5} and dist["cena"] == {"otros_proteicos": 2.0}
    menu = json.loads(p["menu_json"])
    assert [o["plato"] for o in menu["desayuno"]["opciones"]] == ["SMOOTHIE", "TOSTADAS", "PORRIDGE"]
    assert {"porcion": "Verduras", "texto": "Brócoli"} in menu["almuerzo"]["opciones"][0]["lineas"]
    assert p["notes"] == "Almuerzo: Cuando comas legumbres, 2 tazas de guiso"
