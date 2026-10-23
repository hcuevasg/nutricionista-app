"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import timedelta

import models
import schemas
import auth as auth_module
import audit
import two_factor
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.LoginResponse)
async def register(request: schemas.RegisterRequest, req: Request, db: Session = Depends(get_db)):
    """Register a new nutritionist."""
    # Check if user exists
    existing_user = db.query(models.Nutritionist).filter(
        models.Nutritionist.username == request.username
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Create user
    user = models.Nutritionist(
        username=request.username,
        email=request.email,
        password_hash=auth_module.hash_password(request.password),
        name=request.username
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create token
    access_token = auth_module.create_access_token(data={"sub": user.id})
    audit.log(db, action="register", resource="auth", nutritionist_id=user.id,
               detail=f"Nuevo registro: {user.username}", request=req)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@router.post("/login", response_model=schemas.LoginResponse)
async def login(request: schemas.LoginRequest, req: Request, db: Session = Depends(get_db)):
    """Login nutritionist."""
    user = auth_module.authenticate_user(db, request.username, request.password)
    if not user:
        audit.log(db, action="login_failed", resource="auth",
                   detail=f"Intento fallido: {request.username}", request=req)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if user.totp_enabled:
        return {"requires_2fa": True, "challenge_token": two_factor.create_challenge(user.id)}

    return _login_ok(db, user, req, "Login exitoso")


def _login_ok(db: Session, user: models.Nutritionist, req: Request, detail: str) -> dict:
    access_token = auth_module.create_access_token(data={"sub": user.id})
    audit.log(db, action="login", resource="auth", nutritionist_id=user.id,
               detail=detail, request=req)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


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
        current_user.logo_base64 = request.logo_base64
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password")
async def change_password(
    request: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth_module.get_current_user),
):
    """Change password."""
    if not auth_module.verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 6 caracteres")
    current_user.password_hash = auth_module.hash_password(request.new_password)
    db.commit()
    return {"message": "Contraseña actualizada"}


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
    if two_factor.accept_totp(user, request.code):
        db.commit()
        return _login_ok(db, user, req, "Login exitoso (verificación en dos pasos)")
    remaining = two_factor.use_recovery_code(user.totp_recovery_codes, request.code)
    if remaining is not None:
        user.totp_recovery_codes = remaining
        db.commit()
        return _login_ok(db, user, req, "Login con código de recuperación")
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
    db.commit()
    audit.log(db, action="update", resource="auth", nutritionist_id=current_user.id,
              detail="Verificación en dos pasos activada", request=req)
    return {"recovery_codes": codes}


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
    db.commit()
    audit.log(db, action="update", resource="auth", nutritionist_id=current_user.id,
              detail="Verificación en dos pasos desactivada", request=req)
    return {"message": "Verificación en dos pasos desactivada"}
