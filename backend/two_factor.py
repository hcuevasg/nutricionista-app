"""Verificación en dos pasos con TOTP (RFC 6238) y códigos de recuperación."""
import io
import json
import secrets
from datetime import timedelta

import bcrypt
import pyotp
import segno

import auth

ISSUER = "NutriApp"
CHALLENGE_MINUTES = 5
RECOVERY_CODES = 8


def new_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, account: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=account, issuer_name=ISSUER)


def qr_svg(uri: str) -> str:
    buf = io.BytesIO()
    segno.make(uri, error="m").save(buf, kind="svg", scale=5, border=2, dark="#1f3a2b")
    return buf.getvalue().decode()


def verify_totp(secret: str, code: str) -> bool:
    code = (code or "").replace(" ", "")
    # valid_window=1 tolera ±30 s de diferencia de reloj
    return bool(secret) and code.isdigit() and pyotp.TOTP(secret).verify(code, valid_window=1)


def generate_recovery_codes():
    """Devuelve (códigos en claro para mostrar una vez, JSON con sus hashes)."""
    codes = [f"{secrets.token_hex(2)}-{secrets.token_hex(2)}" for _ in range(RECOVERY_CODES)]
    hashes = [bcrypt.hashpw(c.encode(), bcrypt.gensalt(rounds=10)).decode() for c in codes]
    return codes, json.dumps(hashes)


def use_recovery_code(stored_json: str, code: str):
    """Si el código es válido devuelve el JSON sin ese código (un solo uso); si no, None."""
    code = (code or "").strip().lower()
    hashes = json.loads(stored_json or "[]")
    for i, h in enumerate(hashes):
        if bcrypt.checkpw(code.encode(), h.encode()):
            return json.dumps(hashes[:i] + hashes[i + 1:])
    return None


def create_challenge(user_id: int) -> str:
    return auth.create_access_token({"sub": user_id, "purpose": "2fa"},
                                    expires_delta=timedelta(minutes=CHALLENGE_MINUTES))


def read_challenge(token: str) -> int:
    payload = auth.decode_token(token)
    if payload.get("purpose") != "2fa":
        raise ValueError("token no es un desafío de verificación")
    return int(payload["sub"])
