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


# ── Informe PDF ISAK ────────────────────────────────────────────────────────

def test_is_male_accepts_form_and_legacy_values():
    from routers.anthropometrics import _is_male
    assert _is_male("Masculino") and _is_male("M") and _is_male("hombre")
    assert not _is_male("Femenino") and not _is_male("F") and not _is_male(None)


def test_age_at_evaluation_date():
    from routers.anthropometrics import _age_at
    assert _age_at("1990-05-10", "2026-03-14") == 35
    assert _age_at("1990-05-10", "2026-05-10") == 36
    assert _age_at(None, "2026-03-14") is None


def test_isak_pdf_with_implausible_values(auth_client):
    p = auth_client.post("/patients", json={"name": "Datos <raros> & Co", "birth_date": "1990-05-10",
                                            "sex": "Masculino"}).json()
    bad = {**ISAK1, "triceps_mm": 1.0, "hip_glute_cm": 1.0, "fat_mass_pct": -3.8,
           "fat_mass_kg": -3.0, "lean_mass_kg": 83.0}
    ev = auth_client.post(f"/anthropometrics?patient_id={p['id']}", json=bad).json()
    resp = auth_client.get(f"/anthropometrics/{p['id']}/{ev['id']}/pdf")
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")
