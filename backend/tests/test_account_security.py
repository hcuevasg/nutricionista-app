"""Seguridad de cuentas: registro por invitación, contraseñas, bloqueo y sesiones."""
from datetime import timedelta

import bcrypt

import auth
import models
from timeutil import utcnow

PWD = "clave-segura-1"


def _reg(client, name, **extra):
    return client.post("/auth/register", json={"username": name, "email": f"{name}@example.com",
                                               "password": PWD, **extra})


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def test_registration_closed_in_production_unless_invite_code(client, monkeypatch):
    monkeypatch.setattr(auth, "is_production", lambda: True)
    monkeypatch.delenv("REGISTRATION_CODE", raising=False)
    assert _reg(client, "sec_closed").status_code == 403
    monkeypatch.setenv("REGISTRATION_CODE", "invitacion-2026")
    assert _reg(client, "sec_badcode", invite_code="otra").status_code == 403
    assert _reg(client, "sec_goodcode", invite_code="invitacion-2026").status_code == 200


def test_password_rules_and_duplicates(client):
    assert client.post("/auth/register", json={"username": "sec_weak", "email": "w@example.com",
                                               "password": "1234567"}).status_code == 400
    assert client.post("/auth/register", json={"username": "sec_same", "email": "s@example.com",
                                               "password": "sec_same"}).status_code == 400
    assert client.post("/auth/register", json={"username": "sec <script>", "email": "x@example.com",
                                               "password": PWD}).status_code == 422
    assert _reg(client, "sec_dup").status_code == 200
    assert client.post("/auth/register", json={"username": "sec_dup2", "email": "sec_dup@example.com",
                                               "password": PWD}).status_code == 400


def test_lockout_after_failed_attempts(client, db):
    _reg(client, "sec_lock")
    for _ in range(auth.MAX_FAILED_LOGINS):
        assert client.post("/auth/login", json={"username": "sec_lock", "password": "mala-clave"}).status_code == 401
    # Bloqueada aunque ahora use la contraseña correcta
    assert client.post("/auth/login", json={"username": "sec_lock", "password": PWD}).status_code == 429
    u = db.query(models.Nutritionist).filter_by(username="sec_lock").one()
    u.locked_until = utcnow() - timedelta(minutes=1)
    db.commit()
    assert client.post("/auth/login", json={"username": "sec_lock", "password": PWD}).status_code == 200


def test_password_change_and_logout_all_revoke_sessions(client):
    t1 = _reg(client, "sec_sess").json()["access_token"]
    t2 = client.post("/auth/login", json={"username": "sec_sess", "password": PWD}).json()["access_token"]
    r = client.put("/auth/password", json={"current_password": PWD, "new_password": "otra-clave-77"}, headers=_h(t1))
    assert r.status_code == 200
    t3 = r.json()["access_token"]
    assert client.get("/auth/me", headers=_h(t1)).status_code == 401
    assert client.get("/auth/me", headers=_h(t2)).status_code == 401
    assert client.get("/auth/me", headers=_h(t3)).status_code == 200
    assert client.post("/auth/logout-all", headers=_h(t3)).status_code == 204
    assert client.get("/auth/me", headers=_h(t3)).status_code == 401


def test_token_without_version_is_rejected(client):
    uid = _reg(client, "sec_oldtok").json()["user"]["id"]
    legacy = auth.create_access_token({"sub": uid})   # como los tokens emitidos antes de este cambio
    assert client.get("/auth/me", headers=_h(legacy)).status_code == 401


def test_old_bcrypt_cost_is_upgraded_on_login(client, db):
    _reg(client, "sec_rehash")
    u = db.query(models.Nutritionist).filter_by(username="sec_rehash").one()
    u.password_hash = bcrypt.hashpw(PWD.encode(), bcrypt.gensalt(rounds=10)).decode()
    db.commit()
    assert client.post("/auth/login", json={"username": "sec_rehash", "password": PWD}).status_code == 200
    db.refresh(u)
    assert u.password_hash.startswith("$2b$12$")
