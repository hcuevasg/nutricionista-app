"""Authentication logic."""
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from os import getenv
import models
import schemas
from database import get_db

# Configuration
SECRET_KEY = getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = int(getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7"))

# HTTP Bearer
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password using bcrypt."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token."""
    to_encode = data.copy()
    # Convert "sub" to string if it's an integer (PyJWT requirement)
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: Any = Depends(security),
    db: Session = Depends(get_db)
) -> models.Nutritionist:
    """Get current authenticated user."""
    token = credentials.credentials
    payload = decode_token(token)
    user_id = int(payload.get("sub"))  # Convert back from string

    user = db.query(models.Nutritionist).filter(models.Nutritionist.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.Nutritionist]:
    """Authenticate user by username and password."""
    user = db.query(models.Nutritionist).filter(models.Nutritionist.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
