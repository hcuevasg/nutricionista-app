"""Notas de evolución SOAP."""
from tests.test_plantillas import _register

NOTA = {"fecha": "2026-10-20", "motivo": "Control mensual", "subjetivo": "Refiere buena adherencia",
        "objetivo": "Peso 70,5 kg", "analisis": "Baja de 1 kg", "plan": "Mantener pauta",
        "proximo_control": "2026-11-20"}


def test_notas_crud_isolation_and_order(client):
    a, b = _register(client, "nota_a"), _register(client, "nota_b")
    pid = client.post("/patients", json={"name": "Con notas", "sex": "F"}, headers=a).json()["id"]
    assert client.post(f"/notas/{pid}", json=NOTA, headers=b).status_code == 404
    n1 = client.post(f"/notas/{pid}", json=NOTA, headers=a)
    assert n1.status_code == 201
    n2 = client.post(f"/notas/{pid}", json={**NOTA, "fecha": "2026-11-20", "proximo_control": ""}, headers=a).json()
    assert n2["proximo_control"] is None
    assert [n["id"] for n in client.get(f"/notas/{pid}", headers=a).json()] == [n2["id"], n1.json()["id"]]
    assert client.get(f"/notas/{pid}", headers=b).status_code == 404

    nid = n1.json()["id"]
    upd = client.put(f"/notas/{pid}/{nid}", json={**NOTA, "plan": "Subir proteínas"}, headers=a).json()
    assert upd["plan"] == "Subir proteínas"
    assert client.delete(f"/notas/{pid}/{nid}", headers=b).status_code == 404
    assert client.delete(f"/notas/{pid}/{nid}", headers=a).status_code == 204
    assert len(client.get(f"/notas/{pid}", headers=a).json()) == 1
    assert client.post(f"/notas/{pid}", json={**NOTA, "fecha": "20-10-2026"}, headers=a).status_code == 422

    # Se incluyen en la ficha exportada
    assert len(client.get(f"/patients/{pid}/export", headers=a).json()["paciente"]["notas_evolucion"]) == 1
