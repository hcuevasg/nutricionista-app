"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

import models
import schemas
import auth as auth_module
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.LoginResponse)
async def register(request: schemas.RegisterRequest, db: Session = Depends(get_db)):
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
async def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login nutritionist."""
    user = auth_module.authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create token
    access_token = auth_module.create_access_token(data={"sub": user.id})

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
