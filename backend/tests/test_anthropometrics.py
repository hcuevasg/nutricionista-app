"""Tests for anthropometrics endpoints."""
from tests.conftest import next_rut

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
    return auth_client.post("/patients", json={**PATIENT, "rut": next_rut()}).json()


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
    from pdf_isak import is_male as _is_male
    assert _is_male("Masculino") and _is_male("M") and _is_male("hombre")
    assert not _is_male("Femenino") and not _is_male("F") and not _is_male(None)


def test_age_at_evaluation_date():
    from pdf_isak import age_at as _age_at
    assert _age_at("1990-05-10", "2026-03-14") == 35
    assert _age_at("1990-05-10", "2026-05-10") == 36
    assert _age_at(None, "2026-03-14") is None


def test_isak_pdf_with_implausible_values(auth_client):
    p = auth_client.post("/patients", json={"rut": next_rut(), "name": "Datos <raros> & Co", "birth_date": "1990-05-10",
                                            "sex": "Masculino"}).json()
    bad = {**ISAK1, "triceps_mm": 1.0, "hip_glute_cm": 1.0, "fat_mass_pct": -3.8,
           "fat_mass_kg": -3.0, "lean_mass_kg": 83.0}
    ev = auth_client.post(f"/anthropometrics?patient_id={p['id']}", json=bad).json()
    resp = auth_client.get(f"/anthropometrics/{p['id']}/{ev['id']}/pdf")
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")


def test_four_components_and_somatotype_category():
    from types import SimpleNamespace as NS
    from pdf_isak import four_components, somatotype_category
    ev = NS(weight_kg=81.4, height_cm=179.2, wrist_cm=5.8, femur_width_cm=9.9,
            fat_mass_pct=12.7, lean_mass_kg=71.1)
    c = four_components(ev, male=True)
    assert abs(sum(c.values()) - 81.4) < 1e-6
    assert round(c["residual"], 1) == 19.6 and round(c["osea"], 1) == 12.5
    assert four_components(NS(**{**vars(ev), "wrist_cm": None}), True) is None
    assert somatotype_category(2.8, 5.8, 1.7) == "Mesomorfo endomórfico"
    assert somatotype_category(3.0, 3.2, 3.1) == "Central"
    assert somatotype_category(5.0, 2.0, 2.2) == "Endomorfo balanceado"


def test_isak_pdf_compares_with_previous(auth_client):
    p = auth_client.post("/patients", json={"rut": next_rut(), "name": "Comparación", "birth_date": "1997-03-02",
                                            "sex": "Masculino"}).json()
    first = auth_client.post(f"/anthropometrics?patient_id={p['id']}", json={**ISAK1, "date": "2026-04-12"}).json()
    second = auth_client.post(f"/anthropometrics?patient_id={p['id']}",
                              json={**ISAK1, "date": "2026-06-28", "weight_kg": 79.0,
                                    "goals_text": "Bajar 2 kg\nSubir masa muscular",
                                    "next_eval_date": "2026-09-15"}).json()
    assert second["goals_text"].startswith("Bajar")
    for ev_id in (first["id"], second["id"]):
        resp = auth_client.get(f"/anthropometrics/{p['id']}/{ev_id}/pdf")
        assert resp.status_code == 200 and resp.content.startswith(b"%PDF")


def test_isak1_pdf_with_bone_diameters_uses_four_components(auth_client, monkeypatch):
    import pdf_isak
    calls = []
    real = pdf_isak.four_components

    def spy(ev, male):
        c = real(ev, male)
        calls.append(c)
        return c

    monkeypatch.setattr(pdf_isak, "four_components", spy)
    p = _create_patient(auth_client)
    ev = auth_client.post(f"/anthropometrics?patient_id={p['id']}",
                          json={**ISAK1, "humerus_width_cm": 7.0, "wrist_cm": 5.8,
                                "femur_width_cm": 9.9}).json()
    assert ev["isak_level"] == "ISAK 1" and ev["wrist_cm"] == 5.8 and ev["femur_width_cm"] == 9.9
    resp = auth_client.get(f"/anthropometrics/{p['id']}/{ev['id']}/pdf")
    assert resp.status_code == 200 and resp.content.startswith(b"%PDF")
    comps = calls[0]
    assert comps is not None and set(comps) == {"muscular", "residual", "osea", "grasa"}
    assert abs(sum(comps.values()) - 80.0) < 1e-6
