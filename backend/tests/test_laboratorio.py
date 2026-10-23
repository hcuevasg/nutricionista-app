"""Exámenes de laboratorio."""
from tests.test_plantillas import _register


def test_examenes_rangos_estado_y_aislamiento(client):
    a, b = _register(client, "lab_a"), _register(client, "lab_b")
    pid = client.post("/patients", json={"name": "Con exámenes", "sex": "Femenino"}, headers=a).json()["id"]
    cat = {c["key"]: c for c in client.get(f"/laboratorio/{pid}/catalogo", headers=a).json()}
    assert cat["hdl"]["ref_min"] == 50 and cat["ferritina"]["ref_max"] == 150   # rangos de mujer
    assert client.get(f"/laboratorio/{pid}/catalogo", headers=b).status_code == 404

    body = {"fecha": "2026-10-01", "resultados": [
        {"analito": "glicemia", "valor": 112},
        {"analito": "hdl", "valor": 45},
        {"analito": "vitamina_d", "valor": 18},
        {"analito": "ferritina", "valor": 80},
        # Rango propio del laboratorio
        {"analito": "tsh", "valor": 4.2, "ref_min": 0.5, "ref_max": 4.5},
    ]}
    assert client.post(f"/laboratorio/{pid}", json=body, headers=b).status_code == 404
    r = client.post(f"/laboratorio/{pid}", json=body, headers=a)
    assert r.status_code == 201
    estado = {e["analito"]: e["estado"] for e in r.json()}
    assert estado == {"glicemia": "alto", "hdl": "bajo", "vitamina_d": "bajo", "ferritina": "normal", "tsh": "normal"}
    assert next(e for e in r.json() if e["analito"] == "glicemia")["unidad"] == "mg/dL"

    assert client.post(f"/laboratorio/{pid}", json={"fecha": "2026-10-01", "resultados": []}, headers=a).status_code == 422
    assert client.post(f"/laboratorio/{pid}", json={"fecha": "2026-10-01", "resultados": [
        {"analito": "inventado", "valor": 1}]}, headers=a).status_code == 422

    lista = client.get(f"/laboratorio/{pid}", headers=a).json()
    assert len(lista) == 5
    eid = lista[0]["id"]
    assert client.delete(f"/laboratorio/{pid}/{eid}", headers=b).status_code == 404
    assert client.delete(f"/laboratorio/{pid}/{eid}", headers=a).status_code == 204
    assert len(client.get(f"/patients/{pid}/export", headers=a).json()["paciente"]["examenes_laboratorio"]) == 4
