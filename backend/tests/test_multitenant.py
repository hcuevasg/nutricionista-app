"""Aislamiento multi-tenant: un nutricionista no puede leer ni modificar
recursos de otro en ningún router."""
import uuid

import pytest
from tests.conftest import next_rut

PAUTA = {
    "name": "Pauta A", "date": "2026-03-01", "tipo_pauta": "omnivoro",
    "sexo": "F", "edad": 30, "peso": 60.0, "fa_key": "moderada",
    "tmb": 1300, "get_kcal": 2000, "kcal_objetivo": 2000,
    "prot_g_kg": 1.5, "prot_g": 90, "prot_kcal": 360, "prot_pct": 18,
    "lip_pct": 30, "lip_g": 67, "lip_kcal": 600,
    "cho_g": 260, "cho_kcal": 1040, "cho_pct": 52,
    "porciones_json": "{}", "distribucion_json": "{}",
}


NOTA = {"fecha": "2026-03-01", "motivo": "Control", "plan": "Seguir pauta"}
LAB = {"fecha": "2026-03-01", "resultados": [{"analito": "glicemia", "valor": 90}]}

# Cuerpo válido para cada operación con body: así una respuesta 422 nunca tapa un acceso indebido
BODIES = {
    ("PUT", "/patients/{patient_id}"): {"name": "hack", "sex": "F"},
    ("POST", "/patients/{patient_id}/consent"): {"accepted": True},
    ("POST", "/anthropometrics"): {"date": "2026-03-02", "weight_kg": 60},
    ("PUT", "/anthropometrics/{patient_id}/{eval_id}"): {"date": "2026-03-02"},
    ("POST", "/pautas"): PAUTA,
    ("PUT", "/pautas/{patient_id}/{pauta_id}"): PAUTA,
    ("PATCH", "/pautas/{patient_id}/{pauta_id}/menu"): {"menu_json": "{}"},
    ("POST", "/antecedentes/{patient_id}"): {"motivo_consulta": "hack"},
    ("PUT", "/recetas/{receta_id}"): {"nombre": "hack"},
    ("POST", "/appointments"): {"scheduled_at": "2026-12-02T10:00:00"},
    ("PUT", "/appointments/{appt_id}"): {"scheduled_at": "2026-12-02T10:00:00"},
    ("POST", "/portal/tokens"): {},
    ("POST", "/notas/{patient_id}"): NOTA,
    ("PUT", "/notas/{patient_id}/{nota_id}"): NOTA,
    ("POST", "/laboratorio/{patient_id}"): LAB,
}
PATH_IDS = {"patient_id": "patient", "eval_id": "eval", "pauta_id": "pauta", "receta_id": "receta",
            "appt_id": "appt", "token_id": "token_id", "plantilla_id": "plantilla", "nota_id": "nota",
            "examen_id": "examen"}
# Crean un recurso ligado a un paciente indicado en el body o la query
PATIENT_REF = {("POST", "/anthropometrics"), ("POST", "/pautas"), ("POST", "/appointments"), ("POST", "/portal/tokens")}


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

    pid = post("/patients", {"name": "Paciente A", "rut": next_rut(), "sex": "F", "height_cm": 160, "weight_kg": 60})["id"]
    ids = {
        "patient": pid,
        "eval": post(f"/anthropometrics?patient_id={pid}",
                     {"date": "2026-03-01", "isak_level": "ISAK 1", "weight_kg": 60, "height_cm": 160})["id"],
        "pauta": post(f"/pautas?patient_id={pid}", PAUTA)["id"],
        "receta": post("/recetas/", {"nombre": "Receta A"})["id"],
        "appt": post("/appointments", {"patient_id": pid, "scheduled_at": "2026-12-01T10:00:00"})["id"],
        "token_id": post("/portal/tokens", {"patient_id": pid})["id"],
    }
    post(f"/antecedentes/{pid}", {"motivo_consulta": "privado"})
    ids["plantilla"] = post("/plantillas-pauta", {
        "nombre": "Plantilla A", "tipo_pauta": "omnivoro", "fa_key": "moderada", "prot_pct": 20, "lip_pct": 30,
        "porciones_json": "{}", "distribucion_json": "{}"})["id"]
    ids["nota"] = post(f"/notas/{pid}", NOTA)["id"]
    ids["examen"] = post(f"/laboratorio/{pid}", LAB)[0]["id"]
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
    other = client.post("/patients", json={"rut": next_rut(), "name": "Otro", "sex": "F"}, headers=a).json()["id"]
    client.post("/portal/tokens", json={"patient_id": other}, headers=a)
    links = client.get("/portal/tokens", params={"patient_id": pid}, headers=a).json()
    assert [l["patient_id"] for l in links] == [pid]
    token = links[0]["token"]
    assert client.get(f"/portal/{token}").status_code == 200
    assert client.delete(f"/portal/tokens/{links[0]['id']}", headers=a).status_code == 200
    assert client.get("/portal/tokens", params={"patient_id": pid}, headers=a).json() == []
    assert client.get(f"/portal/{token}").status_code == 404


def test_backup_roundtrip_into_other_account(tenants):
    client, a, b, ids = tenants
    client.post("/recetas/", json={"nombre": "Receta con ingredientes"}, headers=a)
    data = client.get("/settings/backup", headers=a).json()
    assert data["version"] == 2
    pac = next(p for p in data["patients"] if p["id"] == ids["patient"])
    assert pac["antecedentes"]["motivo_consulta"] == "privado"
    assert pac["appointments"] and pac["pautas"] and pac["anthropometrics"]
    assert {r["nombre"] for r in data["recetas"]} >= {"Receta A", "Receta con ingredientes"}
    assert "patient_share_tokens" not in str(data.keys())

    counts = client.post("/settings/restore", json=data, headers=b).json()
    assert counts["pacientes"] == len(data["patients"]) and counts["recetas"] == len(data["recetas"])
    assert counts["evaluaciones"] >= 1 and counts["antecedentes"] == 1 and counts["citas"] >= 1
    b_patients = client.get("/patients", headers=b).json()["items"]
    assert "Paciente A" in [p["name"] for p in b_patients]
    # IDs nuevos: los de A siguen siendo de A
    assert ids["patient"] not in [p["id"] for p in b_patients]

    again = client.post("/settings/restore", json=data, headers=b).json()
    assert again["pacientes"] == 0 and again["pacientes_omitidos"] == len(data["patients"])
    assert again["recetas"] == 0


def test_restore_rejects_invalid_file(tenants):
    client, a, _, _ = tenants
    assert client.post("/settings/restore", json={"foo": 1}, headers=a).status_code == 400
    assert client.post("/settings/restore", json={"version": 99, "patients": []}, headers=a).status_code == 400


def test_portal_progress_summary(tenants):
    client, a, _, ids = tenants
    pid = ids["patient"]
    client.post(f"/anthropometrics?patient_id={pid}",
                json={"date": "2026-04-01", "isak_level": "ISAK 1", "weight_kg": 61, "fat_mass_pct": -2,
                      "lean_mass_kg": 63, "sum_6_skinfolds": 70, "goals_text": "vieja"}, headers=a)
    client.post(f"/anthropometrics?patient_id={pid}",
                json={"date": "2026-06-01", "isak_level": "ISAK 1", "weight_kg": 60, "fat_mass_pct": 25,
                      "lean_mass_kg": 45, "sum_6_skinfolds": 65, "goals_text": "Bajar 1 kg",
                      "next_eval_date": "2026-09-01"}, headers=a)
    token = client.post("/portal/tokens", json={"patient_id": pid}, headers=a).json()["token"]
    evs = client.get(f"/portal/{token}/evaluations").json()
    by_date = {e["date"]: e for e in evs}
    assert by_date["2026-04-01"]["fat_mass_pct"] is None  # composición inválida oculta
    assert by_date["2026-04-01"]["goals_text"] is None     # metas solo de la última
    assert by_date["2026-06-01"]["goals_text"] == "Bajar 1 kg"
    assert by_date["2026-06-01"]["sum_6_skinfolds"] == 65


def test_every_route_rejects_other_tenant(tenants):
    """Recorre todas las rutas del API: cualquier operación sobre un registro de A hecha
    por B debe responder 403/404. Cubre también las rutas que se agreguen en el futuro."""
    client, _, b, ids = tenants
    from main import app
    checked, problems = 0, []
    for path, ops in app.openapi()["paths"].items():
        if path.startswith("/portal/{token}"):
            continue  # públicas por token, se prueban aparte
        params = [seg[1:-1] for seg in path.split("/") if seg.startswith("{")]
        for method, op in ops.items():
            method = method.upper()
            key = (method, path)
            if not params and key not in PATIENT_REF:
                continue  # rutas de la propia cuenta (listados, perfil): ver test de listados
            unknown = [p for p in params if p not in PATH_IDS]
            assert not unknown, f"{method} {path}: agrega {unknown} a PATH_IDS"
            url = path
            for p in params:
                url = url.replace("{" + p + "}", str(ids[PATH_IDS[p]]))
            query = {}
            if key in {("POST", "/anthropometrics"), ("POST", "/pautas")}:
                query["patient_id"] = ids["patient"]
            if key == ("PATCH", "/appointments/{appt_id}/status"):
                query["status"] = "cancelled"
            body = None
            if "requestBody" in op:
                assert key in BODIES, f"{method} {path}: agrega un cuerpo de ejemplo a BODIES"
                body = dict(BODIES[key]) if isinstance(BODIES[key], dict) else BODIES[key]
                if key in {("POST", "/appointments"), ("POST", "/portal/tokens")}:
                    body["patient_id"] = ids["patient"]
            resp = client.request(method, url, params=query, json=body, headers=b)
            checked += 1
            if resp.status_code not in (403, 404):
                problems.append(f"{method} {url} → {resp.status_code} {resp.text[:80]}")
    assert checked >= 40, f"solo se revisaron {checked} operaciones"
    assert not problems, "Acceso entre cuentas:\n" + "\n".join(problems)


def test_cannot_link_own_appointment_to_foreign_patient(tenants):
    client, a, b, ids = tenants
    own = client.post("/appointments", json={"scheduled_at": "2026-12-03T10:00:00"}, headers=b).json()
    resp = client.put(f"/appointments/{own['id']}", json={"patient_id": ids["patient"]}, headers=b)
    assert resp.status_code == 404
    assert client.get(f"/appointments/{own['id']}", headers=b).json()["patient_name"] is None
    assert client.post("/appointments", json={"scheduled_at": "2026-12-03T10:00:00", "status": "hackeado"},
                       headers=b).status_code == 422


def test_server_fields_cannot_be_overridden(tenants):
    """Campos que controla el servidor se ignoran aunque el cliente los envíe."""
    client, a, b, ids = tenants
    created = client.post("/patients", json={"rut": next_rut(), "name": "Propio", "sex": "F", "id": ids["patient"],
                                             "nutritionist_id": 999, "consent_at": "2026-01-01T00:00:00"},
                          headers=b).json()
    assert created["id"] != ids["patient"] and created["nutritionist_id"] != 999
    assert created["consent_at"] is None
    assert client.get(f"/patients/{ids['patient']}", headers=a).json()["name"] == "Paciente A"
