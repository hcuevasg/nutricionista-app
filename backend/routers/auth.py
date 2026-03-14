"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import timedelta

import models
import schemas
import auth as auth_module
import audit
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

    access_token = auth_module.create_access_token(data={"sub": user.id})
    audit.log(db, action="login", resource="auth", nutritionist_id=user.id,
               detail=f"Login exitoso", request=req)
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
