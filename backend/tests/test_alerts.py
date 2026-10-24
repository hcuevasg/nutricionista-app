"""Alertas de seguimiento del dashboard."""
from datetime import date, datetime, timedelta

import models
from tests.test_ai import PAUTA
from timeutil import utcnow
from tests.conftest import next_rut


def _register(client, name):
    r = client.post("/auth/register", json={"username": name, "email": f"{name}@example.com",
                                            "password": "test1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _patient(client, h, name):
    return client.post("/patients", json={"rut": next_rut(), "name": name, "sex": "F"}, headers=h).json()["id"]


def _eval(client, h, pid, d, nxt=None):
    client.post(f"/anthropometrics?patient_id={pid}",
                json={"date": d.isoformat(), "isak_level": "ISAK 1", "weight_kg": 60,
                      "next_eval_date": nxt.isoformat() if nxt else None}, headers=h)


def test_alerts_cover_each_case(client, db):
    h = _register(client, "alertas")
    today = date.today()
    vencida = _patient(client, h, "Vencida")
    _eval(client, h, vencida, today - timedelta(days=60), today - timedelta(days=3))
    proxima = _patient(client, h, "Proxima")
    _eval(client, h, proxima, today - timedelta(days=20), today + timedelta(days=5))
    sin_control = _patient(client, h, "SinControl")
    _eval(client, h, sin_control, today - timedelta(weeks=12))
    con_cita = _patient(client, h, "ConCita")
    _eval(client, h, con_cita, today - timedelta(weeks=12))
    client.post("/appointments", json={"patient_id": con_cita,
                                       "scheduled_at": (utcnow() + timedelta(days=3)).isoformat()},
                headers=h)
    al_dia = _patient(client, h, "AlDia")
    _eval(client, h, al_dia, today - timedelta(days=10))
    pauta = client.post(f"/pautas?patient_id={al_dia}", json=PAUTA, headers=h).json()
    client.patch(f"/pautas/{al_dia}/{pauta['id']}/set-active", headers=h)
    nueva = _patient(client, h, "Nueva")
    db.query(models.Patient).filter(models.Patient.id == nueva).update(
        {"created_at": utcnow() - timedelta(days=30)})
    db.commit()

    alerts = client.get("/dashboard/alerts", headers=h).json()
    by = {}
    for a in alerts:
        by.setdefault(a["patient_name"], set()).add(a["tipo"])
    assert by["Vencida"] == {"evaluacion_vencida", "sin_pauta"}
    assert by["Proxima"] == {"evaluacion_proxima", "sin_pauta"}
    assert by["SinControl"] == {"sin_control", "sin_pauta"}
    assert by["ConCita"] == {"sin_pauta"}
    assert "AlDia" not in by
    assert by["Nueva"] == {"sin_evaluacion"}
    assert alerts[0]["tipo"] == "evaluacion_vencida"

    otro = _register(client, "alertas_otro")
    assert client.get("/dashboard/alerts", headers=otro).json() == []
