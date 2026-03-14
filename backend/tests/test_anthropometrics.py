"""Tests for anthropometrics endpoints."""

PATIENT = {"name": "Test ISAK", "birth_date": "1985-01-01", "sex": "M"}

ISAK1 = {
    "date": "2026-03-01",
    "isak_level": "ISAK 1",
    "weight_kg": 80.0,
    "height_cm": 175.0,
    "waist_cm": 88.0,
    "triceps_mm": 12.0,
    "subscapular_mm": 14.0,
    "biceps_mm": 8.0,
    "iliac_crest_mm": 18.0,
    "fat_mass_pct": 18.5,
    "fat_mass_kg": 14.8,
    "lean_mass_kg": 65.2,
    "body_density": 1.062,
    "sum_6_skinfolds": 72.0,
}


def _create_patient(auth_client):
    return auth_client.post("/patients", json=PATIENT).json()


def test_create_anthropometric(auth_client):
    p = _create_patient(auth_client)
    resp = auth_client.post(f"/anthropometrics?patient_id={p['id']}", json=ISAK1)
    assert resp.status_code == 200
    data = resp.json()
    assert data["isak_level"] == "ISAK 1"
    assert data["weight_kg"] == 80.0


def test_list_anthropometrics(auth_client):
    p = _create_patient(auth_client)
    auth_client.post(f"/anthropometrics?patient_id={p['id']}", json=ISAK1)
    resp = auth_client.get(f"/anthropometrics/{p['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_update_anthropometric(auth_client):
    p = _create_patient(auth_client)
    ev = auth_client.post(f"/anthropometrics?patient_id={p['id']}", json=ISAK1).json()
    updated = {**ISAK1, "weight_kg": 79.0}
    resp = auth_client.put(f"/anthropometrics/{p['id']}/{ev['id']}", json=updated)
    assert resp.status_code == 200
    assert resp.json()["weight_kg"] == 79.0


def test_delete_anthropometric(auth_client):
    p = _create_patient(auth_client)
    ev = auth_client.post(f"/anthropometrics?patient_id={p['id']}", json=ISAK1).json()
    resp = auth_client.delete(f"/anthropometrics/{p['id']}/{ev['id']}")
    assert resp.status_code == 200
    resp2 = auth_client.get(f"/anthropometrics/{p['id']}/{ev['id']}")
    assert resp2.status_code == 404
