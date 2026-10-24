"""RUT del paciente: módulo 11, obligatorio al crear, único por cuenta y buscable."""
import pytest

import rut
from tests.test_plantillas import _register


@pytest.mark.parametrize("value,expected", [
    ("12.345.678-5", "12345678-5"), ("12345678-5", "12345678-5"), ("123456785", "12345678-5"),
    ("5.126.663-3", "5126663-3"), (" 7.775.315-k ", "7775315-K"), ("012.345.678-5", "12345678-5"),
])
def test_normalize_valid(value, expected):
    assert rut.normalize(value) == expected


@pytest.mark.parametrize("value", ["12.345.678-6", "12345678-K", "1-9", "abc", "", "123.456.789-0"])
def test_normalize_invalid(value):
    assert rut.normalize(value) is None


def test_compute_dv_special_cases():
    assert rut.compute_dv("7775315") == "K"
    assert rut.format_rut("12345678-5") == "12.345.678-5"


def test_patient_rut_rules(client):
    a, b = _register(client, "rut_a"), _register(client, "rut_b")
    base = {"name": "Con RUT", "sex": "F"}
    assert client.post("/patients", json=base, headers=a).status_code == 422                       # obligatorio
    assert client.post("/patients", json={**base, "rut": "12.345.678-6"}, headers=a).status_code == 422  # DV malo
    p = client.post("/patients", json={**base, "rut": "12.345.678-5"}, headers=a).json()
    assert p["rut"] == "12345678-5"
    dup = client.post("/patients", json={**base, "name": "Otra", "rut": "12345678-5"}, headers=a)
    assert dup.status_code == 400 and "12.345.678-5" in dup.json()["detail"]
    # Otra cuenta puede tener un paciente con el mismo RUT
    assert client.post("/patients", json={**base, "rut": "12345678-5"}, headers=b).status_code == 200

    other = client.post("/patients", json={**base, "name": "Segunda", "rut": "5.126.663-3"}, headers=a).json()
    # Editar: se puede cambiar, pero no a uno inválido ni a uno de otro paciente propio
    assert client.put(f"/patients/{other['id']}", json={"name": "Segunda", "sex": "F", "rut": "1-9"},
                      headers=a).status_code == 422
    assert client.put(f"/patients/{other['id']}", json={"name": "Segunda", "sex": "F", "rut": "12.345.678-5"},
                      headers=a).status_code == 400
    r = client.put(f"/patients/{other['id']}", json={"name": "Segunda", "sex": "F", "rut": "7.775.315-K"}, headers=a)
    assert r.status_code == 200 and r.json()["rut"] == "7775315-K"
    # Guardar sin cambiar el RUT propio no choca consigo mismo
    assert client.put(f"/patients/{other['id']}", json={"name": "Segunda B", "sex": "F", "rut": "7775315-K"},
                      headers=a).status_code == 200

    found = client.get("/patients", params={"q": "12.345.678"}, headers=a).json()["items"]
    assert [x["id"] for x in found] == [p["id"]]
