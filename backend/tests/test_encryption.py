"""Cifrado de columnas con datos de salud."""
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text

import crypto_fields
from database import Base
from tests.conftest import engine_test
from tests.test_plantillas import _register

KEY = Fernet.generate_key().decode()


@pytest.fixture
def encryption_on(monkeypatch):
    monkeypatch.setenv("DATA_ENCRYPTION_KEY", KEY)


def _raw(sql, **params):
    with engine_test.connect() as c:
        return c.execute(text(sql), params).scalar()


def test_health_data_is_stored_encrypted(client, encryption_on):
    h = _register(client, "enc_user")
    pid = client.post("/patients", json={"name": "Cifrada", "sex": "F", "notes": "Diabetes tipo 2",
                                         "address": "Calle Falsa 123"}, headers=h).json()["id"]
    client.post(f"/notas/{pid}", json={"fecha": "2026-10-01", "subjetivo": "Refiere ansiedad"}, headers=h)
    client.post(f"/antecedentes/{pid}", json={"enfermedades_preexistentes": "Hipotiroidismo"}, headers=h)

    raw_notes = _raw("SELECT notes FROM patients WHERE id = :i", i=pid)
    assert raw_notes.startswith(crypto_fields.PREFIX) and "Diabetes" not in raw_notes
    assert "ansiedad" not in _raw("SELECT subjetivo FROM notas_evolucion WHERE patient_id = :i", i=pid)
    assert "Hipotiroidismo" not in _raw("SELECT enfermedades_preexistentes FROM antecedentes WHERE patient_id = :i", i=pid)
    # El nombre queda legible para buscar
    assert _raw("SELECT name FROM patients WHERE id = :i", i=pid) == "Cifrada"

    p = client.get(f"/patients/{pid}", headers=h).json()
    assert p["notes"] == "Diabetes tipo 2" and p["address"] == "Calle Falsa 123"
    assert client.get(f"/notas/{pid}", headers=h).json()[0]["subjetivo"] == "Refiere ansiedad"
    assert client.get("/patients", params={"search": "Cifr"}, headers=h).json()["items"][0]["id"] == pid


def test_existing_plaintext_is_encrypted_on_startup(tmp_path, monkeypatch):
    # Base propia: encrypt_existing recorre todas las tablas y no debe tocar la de otros tests
    from sqlalchemy import create_engine
    eng = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    Base.metadata.create_all(eng)
    with eng.begin() as c:
        c.execute(text("INSERT INTO patients (id, name, notes) VALUES (1, 'Antigua', 'Texto plano')"))
    monkeypatch.setenv("DATA_ENCRYPTION_KEY", KEY)
    assert crypto_fields.encrypt_existing(eng, Base) == 1
    with eng.connect() as c:
        raw = c.execute(text("SELECT notes FROM patients WHERE id = 1")).scalar()
        assert raw.startswith(crypto_fields.PREFIX)
        from sqlalchemy import select
        patients = Base.metadata.tables["patients"]
        assert c.execute(select(patients.c.notes)).scalar() == "Texto plano"
    assert crypto_fields.encrypt_existing(eng, Base) == 0   # idempotente


def test_key_rotation(client, db, monkeypatch):
    monkeypatch.setenv("DATA_ENCRYPTION_KEY", KEY)
    h = _register(client, "enc_rot")
    pid = client.post("/patients", json={"name": "Rotada", "sex": "F", "notes": "secreto"}, headers=h).json()["id"]
    monkeypatch.setenv("DATA_ENCRYPTION_KEY", f"{Fernet.generate_key().decode()},{KEY}")
    db.expire_all()   # releer desde la base con la clave nueva primero
    assert client.get(f"/patients/{pid}", headers=h).json()["notes"] == "secreto"
    monkeypatch.setenv("DATA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    db.expire_all()   # sin la clave original ya no se puede leer (error controlado, no texto cifrado)
    assert client.get(f"/patients/{pid}", headers=h).status_code == 500
    db.rollback()
