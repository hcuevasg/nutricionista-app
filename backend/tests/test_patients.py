"""Tests for patients endpoints."""

PATIENT = {
    "name": "María González",
    "birth_date": "1990-05-15",
    "sex": "F",
    "height_cm": 165.0,
    "weight_kg": 62.0,
}


def test_list_patients_empty(auth_client):
    resp = auth_client.get("/patients")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_patient(auth_client):
    resp = auth_client.post("/patients", json=PATIENT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == PATIENT["name"]
    assert "id" in data


def test_get_patient(auth_client):
    created = auth_client.post("/patients", json=PATIENT).json()
    resp = auth_client.get(f"/patients/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == PATIENT["name"]


def test_update_patient(auth_client):
    created = auth_client.post("/patients", json=PATIENT).json()
    updated = {**PATIENT, "name": "María González Actualizada"}
    resp = auth_client.put(f"/patients/{created['id']}", json=updated)
    assert resp.status_code == 200
    assert resp.json()["name"] == "María González Actualizada"


def test_delete_patient(auth_client):
    created = auth_client.post("/patients", json=PATIENT).json()
    resp = auth_client.delete(f"/patients/{created['id']}")
    assert resp.status_code == 200
    # Verify gone
    resp2 = auth_client.get(f"/patients/{created['id']}")
    assert resp2.status_code == 404


def test_patient_isolation(client):
    """Two users cannot access each other's patients."""
    # User A
    client.post("/auth/register", json={"username": "userA", "email": "a@a.com", "password": "pass1234"})
    tokenA = client.post("/auth/login", json={"username": "userA", "password": "pass1234"}).json()["access_token"]
    headersA = {"Authorization": f"Bearer {tokenA}"}

    # User B
    client.post("/auth/register", json={"username": "userB", "email": "b@b.com", "password": "pass1234"})
    tokenB = client.post("/auth/login", json={"username": "userB", "password": "pass1234"}).json()["access_token"]
    headersB = {"Authorization": f"Bearer {tokenB}"}

    # A creates a patient
    p = client.post("/patients", json=PATIENT, headers=headersA).json()
    # B tries to access it
    resp = client.get(f"/patients/{p['id']}", headers=headersB)
    assert resp.status_code == 404
