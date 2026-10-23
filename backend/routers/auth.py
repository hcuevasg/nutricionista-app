"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import hmac
import os
from typing import Optional

import models
import schemas
import auth as auth_module
import audit
import two_factor
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _registration_allowed(code: Optional[str]) -> bool:
    """Con REGISTRATION_CODE configurado se exige ese código de invitación; sin él,
    el registro solo está abierto en desarrollo local (en producción queda cerrado)."""
    expected = os.getenv("REGISTRATION_CODE", "")
    if expected:
        return bool(code) and hmac.compare_digest(code.strip(), expected)
    return not auth_module.is_production()


@router.post("/register", response_model=schemas.LoginResponse)
async def register(request: schemas.RegisterRequest, req: Request, db: Session = Depends(get_db)):
    """Register a new nutritionist."""
    if not _registration_allowed(request.invite_code):
        raise HTTPException(status_code=403, detail="El registro requiere un código de invitación válido")
    problem = auth_module.password_problem(request.password, request.username)
    if problem:
        raise HTTPException(status_code=400, detail=problem)
    existing_user = db.query(models.Nutritionist).filter(
        (models.Nutritionist.username == request.username) | (models.Nutritionist.email == request.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario o el correo ya están registrados")

    user = models.Nutritionist(
        username=request.username,
        email=request.email,
        password_hash=auth_module.hash_password(request.password),
        name=request.username
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit.log(db, action="register", resource="auth", nutritionist_id=user.id,
               detail=f"Nuevo registro: {user.username}", request=req)
    return _session(user)


_LOCKED = HTTPException(status_code=429, detail="Demasiados intentos fallidos. Espera 15 minutos e intenta de nuevo.")


@router.post("/login", response_model=schemas.LoginResponse)
async def login(request: schemas.LoginRequest, req: Request, db: Session = Depends(get_db)):
    """Login nutritionist."""
    account = db.query(models.Nutritionist).filter(models.Nutritionist.username == request.username).first()
    if account and auth_module.is_locked(account):
        raise _LOCKED
    user = auth_module.authenticate_user(db, request.username, request.password)
    if not user:
        if account:
            auth_module.register_failed_login(account)
            db.commit()
        audit.log(db, action="login_failed", resource="auth", nutritionist_id=account.id if account else None,
                   detail=f"Intento fallido: {request.username[:50]}", request=req)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if auth_module.needs_rehash(user.password_hash):
        user.password_hash = auth_module.hash_password(request.password)
        db.commit()

    if user.totp_enabled:
        return {"requires_2fa": True, "challenge_token": two_factor.create_challenge(user.id)}

    return _login_ok(db, user, req, "Login exitoso")


def _session(user: models.Nutritionist) -> dict:
    return {
        "access_token": auth_module.session_token(user),
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


def _login_ok(db: Session, user: models.Nutritionist, req: Request, detail: str) -> dict:
    user.failed_logins = 0
    user.locked_until = None
    db.commit()
    audit.log(db, action="login", resource="auth", nutritionist_id=user.id,
               detail=detail, request=req)
    return _session(user)


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user(current_user: models.Nutritionist = Depends(auth_module.get_current_user)):
    """Get current user."""
    return current_user


@router.put("/profile", response_model=schemas.UserResponse)
async def update_profile(
    request: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth_module.get_current_user),
):
    """Update name and/or email."""
    if request.name is not None:
        current_user.name = request.name
    if request.email is not None:
        existing = db.query(models.Nutritionist).filter(
            models.Nutritionist.email == request.email,
            models.Nutritionist.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email ya registrado")
        current_user.email = request.email
    if request.clinic_name is not None:
        current_user.clinic_name = request.clinic_name
    if request.report_tagline is not None:
        current_user.report_tagline = request.report_tagline
    if request.logo_base64 is not None:
        current_user.logo_base64 = request.logo_base64 or None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password")
async def change_password(
    request: schemas.PasswordChange,
    req: Request,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth_module.get_current_user),
):
    """Cambia la contraseña y cierra las demás sesiones; devuelve un token nuevo para esta."""
    if not auth_module.verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    problem = auth_module.password_problem(request.new_password, current_user.username)
    if problem:
        raise HTTPException(status_code=400, detail=problem)
    current_user.password_hash = auth_module.hash_password(request.new_password)
    auth_module.revoke_sessions(current_user)
    db.commit()
    audit.log(db, action="update", resource="auth", nutritionist_id=current_user.id,
              detail="Contraseña cambiada (sesiones cerradas)", request=req)
    return {"message": "Contraseña actualizada", "access_token": auth_module.session_token(current_user)}


@router.post("/logout-all", status_code=204)
async def logout_all(req: Request, db: Session = Depends(get_db),
                     current_user: models.Nutritionist = Depends(auth_module.get_current_user)):
    """Cierra la sesión en todos los dispositivos, incluido este."""
    auth_module.revoke_sessions(current_user)
    db.commit()
    audit.log(db, action="update", resource="auth", nutritionist_id=current_user.id,
              detail="Sesiones cerradas en todos los dispositivos", request=req)


# ── Verificación en dos pasos ──────────────────────────────────────────────────

@router.post("/2fa/verify", response_model=schemas.LoginResponse)
async def verify_two_factor(request: schemas.TwoFactorVerifyRequest, req: Request,
                            db: Session = Depends(get_db)):
    """Segundo paso del login: código TOTP o un código de recuperación."""
    try:
        user_id = two_factor.read_challenge(request.challenge_token)
    except (ValueError, HTTPException):
        raise HTTPException(status_code=401, detail="La verificación expiró. Vuelve a iniciar sesión.")
    user = db.query(models.Nutritionist).filter(models.Nutritionist.id == user_id).first()
    if not user or not user.totp_enabled:
        raise HTTPException(status_code=401, detail="La verificación expiró. Vuelve a iniciar sesión.")
    if auth_module.is_locked(user):
        raise _LOCKED
    if two_factor.accept_totp(user, request.code):
        db.commit()
        return _login_ok(db, user, req, "Login exitoso (verificación en dos pasos)")
    remaining = two_factor.use_recovery_code(user.totp_recovery_codes, request.code)
    if remaining is not None:
        user.totp_recovery_codes = remaining
        db.commit()
        return _login_ok(db, user, req, "Login con código de recuperación")
    auth_module.register_failed_login(user)
    db.commit()
    audit.log(db, action="login_failed", resource="auth", nutritionist_id=user.id,
              detail="Código de verificación incorrecto", request=req)
    raise HTTPException(status_code=401, detail="Código incorrecto")


@router.post("/2fa/setup")
async def setup_two_factor(db: Session = Depends(get_db),
                           current_user: models.Nutritionist = Depends(auth_module.get_current_user)):
    """Genera un secreto nuevo (aún no activo) y su código QR."""
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="La verificación en dos pasos ya está activa")
    current_user.totp_secret = two_factor.new_secret()
    db.commit()
    uri = two_factor.provisioning_uri(current_user.totp_secret, current_user.email or current_user.username)
    return {"secret": current_user.totp_secret, "otpauth_uri": uri, "qr_svg": two_factor.qr_svg(uri)}


@router.post("/2fa/enable")
async def enable_two_factor(request: schemas.TwoFactorCodeRequest, req: Request,
                            db: Session = Depends(get_db),
                            current_user: models.Nutritionist = Depends(auth_module.get_current_user)):
    """Activa la verificación tras comprobar un código; devuelve los códigos de recuperación."""
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="La verificación en dos pasos ya está activa")
    if not two_factor.accept_totp(current_user, request.code):
        raise HTTPException(status_code=400, detail="Código incorrecto. Revisa la hora del teléfono e intenta de nuevo.")
    codes, hashes = two_factor.generate_recovery_codes()
    current_user.totp_enabled = True
    current_user.totp_recovery_codes = hashes
    auth_module.revoke_sessions(current_user)
    db.commit()
    audit.log(db, action="update", resource="auth", nutritionist_id=current_user.id,
              detail="Verificación en dos pasos activada", request=req)
    return {"recovery_codes": codes, "access_token": auth_module.session_token(current_user)}


@router.post("/2fa/disable")
async def disable_two_factor(request: schemas.TwoFactorDisableRequest, req: Request,
                             db: Session = Depends(get_db),
                             current_user: models.Nutritionist = Depends(auth_module.get_current_user)):
    """Desactiva la verificación: exige contraseña y un código vigente (o de recuperación)."""
    if not auth_module.verify_password(request.password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    ok = two_factor.accept_totp(current_user, request.code) or \
        two_factor.use_recovery_code(current_user.totp_recovery_codes, request.code) is not None
    if not ok:
        raise HTTPException(status_code=400, detail="Código incorrecto")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    current_user.totp_recovery_codes = None
    current_user.totp_last_step = None
    auth_module.revoke_sessions(current_user)
    db.commit()
    audit.log(db, action="update", resource="auth", nutritionist_id=current_user.id,
              detail="Verificación en dos pasos desactivada", request=req)
    return {"message": "Verificación en dos pasos desactivada",
            "access_token": auth_module.session_token(current_user)}
