"""Consentimiento del paciente y exportación de la ficha."""
from tests.test_plantillas import _register


def test_consent_register_and_revoke(client):
    a, b = _register(client, "cons_a"), _register(client, "cons_b")
    pid = client.post("/patients", json={"name": "Consentida", "sex": "F"}, headers=a).json()["id"]
    assert client.get(f"/patients/{pid}", headers=a).json()["consent_at"] is None
    assert client.post(f"/patients/{pid}/consent", json={"accepted": True}, headers=b).status_code == 404
    r = client.post(f"/patients/{pid}/consent", json={"accepted": True}, headers=a).json()
    assert r["consent_at"] and r["consent_version"] and r["consent_source"] == "profesional"
    # Editar la ficha no borra el consentimiento
    client.put(f"/patients/{pid}", json={"name": "Consentida", "sex": "F", "notes": "x"}, headers=a)
    assert client.get(f"/patients/{pid}", headers=a).json()["consent_at"]
    r = client.post(f"/patients/{pid}/consent", json={"accepted": False}, headers=a).json()
    assert r["consent_at"] is None and r["consent_version"] is None


def test_export_patient_record(client):
    a, b = _register(client, "exp_a"), _register(client, "exp_b")
    pid = client.post("/patients", json={"name": "Exportable", "sex": "M"}, headers=a).json()["id"]
    client.post(f"/patients/{pid}/antecedentes", json={"diagnosticos": "HTA"}, headers=a)
    assert client.get(f"/patients/{pid}/export", headers=b).status_code == 404
    r = client.get(f"/patients/{pid}/export", headers=a)
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    data = r.json()
    assert data["paciente"]["name"] == "Exportable"
    assert {"anthropometrics", "pautas", "antecedentes", "appointments"} <= data["paciente"].keys()
    logs = client.get("/settings/audit-logs", headers=a).json()
    entries = logs["logs"] if isinstance(logs, dict) else logs
    assert any(e["action"] == "export" and e["resource"] == "patient" for e in entries)


def test_patient_accepts_consent_from_portal(client):
    a = _register(client, "cons_portal")
    pid = client.post("/patients", json={"name": "Desde portal", "sex": "F"}, headers=a).json()["id"]
    token = client.post("/portal/tokens", json={"patient_id": pid, "days_valid": 30}, headers=a).json()["token"]
    info = client.get(f"/portal/{token}").json()
    assert info["consent_at"] is None and info["current_consent_version"]
    assert client.post(f"/portal/{token}/consent", json={"accepted": False}).status_code == 400
    assert client.post("/portal/token-falso/consent", json={"accepted": True}).status_code == 404
    info = client.post(f"/portal/{token}/consent", json={"accepted": True},
                       headers={"x-forwarded-for": "1.1.1.1, 200.1.2.3"}).json()
    assert info["consent_at"] and info["consent_version"] == info["current_consent_version"]
    p = client.get(f"/patients/{pid}", headers=a).json()
    assert p["consent_source"] == "portal"
    from tests.conftest import TestingSessionLocal
    import models
    with TestingSessionLocal() as s:
        assert s.get(models.Patient, pid).consent_ip == "200.1.2.3"
    logs = client.get("/settings/audit-logs", headers=a).json()["logs"]
    assert any(e["action"] == "consent" and "portal" in (e["detail"] or "") for e in logs)
