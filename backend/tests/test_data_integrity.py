"""Integridad de los datos: editar nunca borra lo que el cliente no envía."""
import asyncio

import main
from tests.test_ai import PAUTA
from tests.test_plantillas import _register
from tests.conftest import next_rut


def _patient(client, h, **extra):
    return client.post("/patients", json={"rut": next_rut(), "name": "Íntegra", "sex": "F", "phone": "+56 9 1111 2222",
                                          "notes": "Hipotiroidismo", "allergies": ["gluten"], **extra},
                       headers=h).json()["id"]


def test_editing_pauta_keeps_generated_menu(client):
    h = _register(client, "int_pauta")
    pid = _patient(client, h)
    pauta = client.post(f"/pautas?patient_id={pid}", json={**PAUTA, "menu_json": '{"desayuno": ["Avena"]}'},
                        headers=h).json()
    edit = {k: v for k, v in PAUTA.items() if k != "menu_json"}   # así edita el formulario
    r = client.put(f"/pautas/{pid}/{pauta['id']}", json={**edit, "name": "Pauta editada"}, headers=h)
    assert r.status_code == 200
    assert r.json()["name"] == "Pauta editada"
    assert r.json()["menu_json"] == '{"desayuno": ["Avena"]}'


def test_patient_partial_update_keeps_other_fields_and_null_clears(client):
    h = _register(client, "int_pac")
    pid = _patient(client, h)
    r = client.put(f"/patients/{pid}", json={"name": "Íntegra Pérez", "sex": "F"}, headers=h).json()
    assert r["phone"] == "+56 9 1111 2222" and r["notes"] == "Hipotiroidismo" and r["allergies"] == ["gluten"]
    r = client.put(f"/patients/{pid}", json={"name": "Íntegra Pérez", "sex": "F", "notes": None,
                                            "allergies": []}, headers=h).json()
    assert r["notes"] is None and r["allergies"] == [] and r["phone"] == "+56 9 1111 2222"


def test_antecedentes_partial_update_keeps_other_fields(client):
    h = _register(client, "int_ant")
    pid = _patient(client, h)
    client.post(f"/antecedentes/{pid}", json={"motivo_consulta": "Bajar de peso", "cirugias": "Apendicectomía"},
                headers=h)
    client.post(f"/antecedentes/{pid}", json={"motivo_consulta": "Mejorar energía"}, headers=h)
    a = client.get(f"/antecedentes/{pid}", headers=h).json()
    assert a["motivo_consulta"] == "Mejorar energía" and a["cirugias"] == "Apendicectomía"


def test_isak_level_change_clears_isak2_fields_sent_as_null(client):
    h = _register(client, "int_isak")
    pid = _patient(client, h)
    ev = client.post(f"/anthropometrics?patient_id={pid}", json={
        "date": "2026-10-01", "isak_level": "ISAK 2", "weight_kg": 60, "pectoral_mm": 10,
        "somatotype_endo": 3.1, "goals_text": "Meta"}, headers=h).json()
    r = client.put(f"/anthropometrics/{pid}/{ev['id']}", json={
        "date": "2026-10-01", "isak_level": "ISAK 1", "weight_kg": 61, "pectoral_mm": None,
        "somatotype_endo": None}, headers=h).json()
    assert r["isak_level"] == "ISAK 1" and r["weight_kg"] == 61
    assert r["pectoral_mm"] is None and r["somatotype_endo"] is None
    assert r["goals_text"] == "Meta"   # no se envió: se conserva


def test_receta_partial_update_keeps_description(client):
    h = _register(client, "int_rec")
    rid = client.post("/recetas/", json={"nombre": "Budín", "descripcion": "Paso a paso"}, headers=h).json()["id"]
    r = client.put(f"/recetas/{rid}", json={"nombre": "Budín de avena"}, headers=h).json()
    assert r["nombre"] == "Budín de avena" and r["descripcion"] == "Paso a paso"


def test_startup_waits_for_database(monkeypatch):
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        return calls["n"] >= 3

    monkeypatch.setattr(main, "_database_ready", flaky)
    real_sleep = asyncio.sleep
    monkeypatch.setattr(main.asyncio, "sleep", lambda s: real_sleep(0))
    assert asyncio.run(main._wait_for_database(60)) is True and calls["n"] == 3
    monkeypatch.setattr(main, "_database_ready", lambda: False)
    assert asyncio.run(main._wait_for_database(0)) is False
