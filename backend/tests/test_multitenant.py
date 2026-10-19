"""Aislamiento multi-tenant: un nutricionista no puede leer ni modificar
recursos de otro en ningún router."""
import uuid

import pytest

PAUTA = {
    "name": "Pauta A", "date": "2026-03-01", "tipo_pauta": "omnivoro",
    "sexo": "F", "edad": 30, "peso": 60.0, "fa_key": "moderada",
    "tmb": 1300, "get_kcal": 2000, "kcal_objetivo": 2000,
    "prot_g_kg": 1.5, "prot_g": 90, "prot_kcal": 360, "prot_pct": 18,
    "lip_pct": 30, "lip_g": 67, "lip_kcal": 600,
    "cho_g": 260, "cho_kcal": 1040, "cho_pct": 52,
    "porciones_json": "{}", "distribucion_json": "{}",
}


def _register(client):
    name = f"u_{uuid.uuid4().hex[:8]}"
    resp = client.post("/auth/register", json={
        "username": name, "email": f"{name}@example.com", "password": "test1234",
    })
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def tenants(client):
    """Nutricionista A con un recurso de cada tipo, y headers de B."""
    a, b = _register(client), _register(client)

    def post(url, json):
        resp = client.post(url, json=json, headers=a)
        assert resp.status_code in (200, 201), f"{url}: {resp.status_code} {resp.text}"
        return resp.json()

    pid = post("/patients", {"name": "Paciente A", "sex": "F", "height_cm": 160, "weight_kg": 60})["id"]
    ids = {
        "patient": pid,
        "eval": post(f"/anthropometrics?patient_id={pid}",
                     {"date": "2026-03-01", "isak_level": "ISAK 1", "weight_kg": 60, "height_cm": 160})["id"],
        "pauta": post(f"/pautas?patient_id={pid}", PAUTA)["id"],
        "plan": post(f"/meal-plans?patient_id={pid}", {"name": "Plan A", "date": "2026-03-01"})["id"],
        "receta": post("/recetas/", {"nombre": "Receta A"})["id"],
        "appt": post("/appointments", {"patient_id": pid, "scheduled_at": "2026-12-01T10:00:00"})["id"],
        "token_id": post("/portal/tokens", {"patient_id": pid})["id"],
    }
    post(f"/antecedentes/{pid}", {"motivo_consulta": "privado"})
    return client, a, b, ids


def _forbidden_requests(ids):
    p = ids["patient"]
    return [
        ("GET", f"/patients/{p}", None),
        ("PUT", f"/patients/{p}", {"name": "hack", "sex": "F"}),
        ("DELETE", f"/patients/{p}", None),
        ("GET", f"/anthropometrics/{p}", None),
        ("GET", f"/anthropometrics/{p}/{ids['eval']}", None),
        ("PUT", f"/anthropometrics/{p}/{ids['eval']}", {"date": "2026-03-02"}),
        ("DELETE", f"/anthropometrics/{p}/{ids['eval']}", None),
        ("GET", f"/anthropometrics/{p}/{ids['eval']}/pdf", None),
        ("GET", f"/pautas/{p}", None),
        ("GET", f"/pautas/{p}/{ids['pauta']}", None),
        ("PUT", f"/pautas/{p}/{ids['pauta']}", PAUTA),
        ("PATCH", f"/pautas/{p}/{ids['pauta']}/set-active", None),
        ("PATCH", f"/pautas/{p}/{ids['pauta']}/menu", {"menu_json": "{}"}),
        ("DELETE", f"/pautas/{p}/{ids['pauta']}", None),
        ("GET", f"/pautas/{p}/{ids['pauta']}/generar-menu-stream", None),
        ("POST", f"/pautas/{p}/{ids['pauta']}/generar-menu", None),
        ("POST", f"/pautas/{p}/{ids['pauta']}/ai-suggest", None),
        ("GET", f"/meal-plans/{p}", None),
        ("GET", f"/meal-plans/{p}/{ids['plan']}", None),
        ("DELETE", f"/meal-plans/{p}/{ids['plan']}", None),
        ("GET", f"/antecedentes/{p}", None),
        ("POST", f"/antecedentes/{p}", {"motivo_consulta": "hack"}),
        ("GET", f"/recetas/{ids['receta']}", None),
        ("PUT", f"/recetas/{ids['receta']}", {"nombre": "hack"}),
        ("DELETE", f"/recetas/{ids['receta']}", None),
        ("GET", f"/appointments/{ids['appt']}", None),
        ("PUT", f"/appointments/{ids['appt']}", {"scheduled_at": "2026-12-02T10:00:00"}),
        ("PATCH", f"/appointments/{ids['appt']}/status", {"status": "cancelled"}),
        ("DELETE", f"/appointments/{ids['appt']}", None),
        ("POST", "/portal/tokens", {"patient_id": p}),
        ("DELETE", f"/portal/tokens/{ids['token_id']}", None),
    ]


def test_other_tenant_cannot_access_resources(tenants):
    client, a, b, ids = tenants
    leaks = []
    for method, url, body in _forbidden_requests(ids):
        resp = client.request(method, url, json=body, headers=b)
        if resp.status_code < 400:
            leaks.append(f"{method} {url} → {resp.status_code}")
    assert not leaks, "Acceso entre cuentas:\n" + "\n".join(leaks)

    # Los recursos de A siguen intactos
    assert client.get(f"/patients/{ids['patient']}", headers=a).json()["name"] == "Paciente A"
    assert client.get(f"/recetas/{ids['receta']}", headers=a).json()["nombre"] == "Receta A"
    assert client.get(f"/antecedentes/{ids['patient']}", headers=a).json()["motivo_consulta"] == "privado"


def test_other_tenant_listings_exclude_foreign_data(tenants):
    client, _, b, ids = tenants
    patients = client.get("/patients", headers=b).json()["items"]
    assert ids["patient"] not in [p["id"] for p in patients]
    recetas = client.get("/recetas/", headers=b).json()["items"]
    assert ids["receta"] not in [r["id"] for r in recetas]
    appts = client.get("/appointments", headers=b).json()
    assert ids["appt"] not in [x["id"] for x in appts]
    tokens = client.get("/portal/tokens", headers=b).json()
    assert ids["token_id"] not in [t["id"] for t in tokens]
    assert client.get("/dashboard/stats", headers=b).json().get("total_patients", 0) == 0


def test_portal_links_list_filter_and_revoke(tenants):
    client, a, b, ids = tenants
    pid = ids["patient"]
    other = client.post("/patients", json={"name": "Otro", "sex": "F"}, headers=a).json()["id"]
    client.post("/portal/tokens", json={"patient_id": other}, headers=a)
    links = client.get("/portal/tokens", params={"patient_id": pid}, headers=a).json()
    assert [l["patient_id"] for l in links] == [pid]
    token = links[0]["token"]
    assert client.get(f"/portal/{token}").status_code == 200
    assert client.delete(f"/portal/tokens/{links[0]['id']}", headers=a).status_code == 200
    assert client.get("/portal/tokens", params={"patient_id": pid}, headers=a).json() == []
    assert client.get(f"/portal/{token}").status_code == 404
