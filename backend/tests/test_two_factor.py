"""Verificación en dos pasos (TOTP) en el login."""
import time

import pyotp


def _next(totp):
    """Código del siguiente paso de 30 s: el actual ya se usó al activar (uso único)."""
    return totp.at(time.time() + 30)


def _register(client, name):
    r = client.post("/auth/register", json={"username": name, "email": f"{name}@example.com",
                                            "password": "test1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _login(client, name):
    return client.post("/auth/login", json={"username": name, "password": "test1234"}).json()


def _enable(client, h):
    setup = client.post("/auth/2fa/setup", headers=h).json()
    assert setup["otpauth_uri"].startswith("otpauth://totp/") and "<svg" in setup["qr_svg"]
    totp = pyotp.TOTP(setup["secret"])
    assert client.post("/auth/2fa/enable", json={"code": "000000"}, headers=h).status_code == 400
    res = client.post("/auth/2fa/enable", json={"code": totp.now()}, headers=h)
    assert res.status_code == 200
    # Activar el 2FA cierra las sesiones anteriores: el token viejo deja de servir
    assert client.get("/auth/me", headers=h).status_code == 401
    h["Authorization"] = f"Bearer {res.json()['access_token']}"
    return totp, res.json()["recovery_codes"]


def test_login_requires_code_after_enabling(client):
    h = _register(client, "tfa_user")
    assert _login(client, "tfa_user")["access_token"]
    totp, codes = _enable(client, h)
    assert len(codes) == 8
    assert client.get("/auth/me", headers=h).json()["totp_enabled"] is True

    step1 = _login(client, "tfa_user")
    assert step1["requires_2fa"] and step1["access_token"] is None
    challenge = step1["challenge_token"]
    # El desafío no sirve como sesión
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {challenge}"}).status_code == 401
    bad = client.post("/auth/2fa/verify", json={"challenge_token": challenge, "code": "123456"})
    assert bad.status_code == 401
    # El código que se usó para activar ya no sirve
    assert client.post("/auth/2fa/verify", json={"challenge_token": challenge, "code": totp.now()}).status_code == 401
    ok = client.post("/auth/2fa/verify", json={"challenge_token": challenge, "code": _next(totp)}).json()
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {ok['access_token']}"}).status_code == 200
    # Ni se puede reutilizar el que se acaba de aceptar
    challenge = _login(client, "tfa_user")["challenge_token"]
    assert client.post("/auth/2fa/verify", json={"challenge_token": challenge, "code": _next(totp)}).status_code == 401


def test_recovery_code_is_single_use(client):
    h = _register(client, "tfa_rec")
    _, codes = _enable(client, h)
    challenge = _login(client, "tfa_rec")["challenge_token"]
    assert client.post("/auth/2fa/verify", json={"challenge_token": challenge, "code": codes[0]}).status_code == 200
    challenge = _login(client, "tfa_rec")["challenge_token"]
    assert client.post("/auth/2fa/verify", json={"challenge_token": challenge, "code": codes[0]}).status_code == 401


def test_disable_requires_password_and_code(client):
    h = _register(client, "tfa_off")
    totp, _ = _enable(client, h)
    assert client.post("/auth/2fa/disable", json={"password": "mala", "code": totp.now()}, headers=h).status_code == 400
    assert client.post("/auth/2fa/disable", json={"password": "test1234", "code": "000000"}, headers=h).status_code == 400
    assert client.post("/auth/2fa/disable", json={"password": "test1234", "code": _next(totp)}, headers=h).status_code == 200
    assert _login(client, "tfa_off")["access_token"]
