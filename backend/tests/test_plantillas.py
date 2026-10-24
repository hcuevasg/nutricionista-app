"""Plantillas de pauta y duplicado de pautas."""
import json

from tests.test_ai import PAUTA
from tests.conftest import next_rut

PLANTILLA = {
    "nombre": "Hipocalórica 1800", "tipo_pauta": "hipocalorico", "fa_key": "liviana", "ajuste_kcal": -300,
    "prot_pct": 25, "lip_pct": 30, "porciones_json": json.dumps({"cereales": 4}),
    "distribucion_json": json.dumps({"desayuno": {"cereales": 2}}), "menu_json": None, "notes": "Base",
}


def _register(client, name):
    r = client.post("/auth/register", json={"username": name, "email": f"{name}@example.com",
                                            "password": "test1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_plantillas_crud_and_isolation(client):
    a, b = _register(client, "plant_a"), _register(client, "plant_b")
    created = client.post("/plantillas-pauta", json=PLANTILLA, headers=a)
    assert created.status_code == 201
    pid = created.json()["id"]
    assert [p["nombre"] for p in client.get("/plantillas-pauta", headers=a).json()] == ["Hipocalórica 1800"]
    assert client.get("/plantillas-pauta", headers=b).json() == []
    assert client.delete(f"/plantillas-pauta/{pid}", headers=b).status_code == 404
    assert client.delete(f"/plantillas-pauta/{pid}", headers=a).status_code == 204
    assert client.get("/plantillas-pauta", headers=a).json() == []
    assert client.post("/plantillas-pauta", json={**PLANTILLA, "nombre": "  "}, headers=a).status_code == 422


def test_duplicar_pauta(client):
    a, b = _register(client, "dup_a"), _register(client, "dup_b")
    pid = client.post("/patients", json={"rut": next_rut(), "name": "Dup", "sex": "F"}, headers=a).json()["id"]
    pauta = client.post(f"/pautas?patient_id={pid}", json={**PAUTA, "menu_json": '{"x": 1}'}, headers=a).json()
    client.patch(f"/pautas/{pid}/{pauta['id']}/set-active", headers=a)
    assert client.post(f"/pautas/{pid}/{pauta['id']}/duplicar", headers=b).status_code == 404
    copia = client.post(f"/pautas/{pid}/{pauta['id']}/duplicar", headers=a)
    assert copia.status_code == 201
    c = copia.json()
    assert c["id"] != pauta["id"] and c["name"].endswith("(copia)")
    assert c["distribucion_json"] == pauta["distribucion_json"] and c["menu_json"] == '{"x": 1}'
    assert c["is_active"] is False
