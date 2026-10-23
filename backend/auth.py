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
from timeutil import utcnow

# Configuration
_INSECURE_DEFAULT_KEY = "your-secret-key-change-in-production"
SECRET_KEY = getenv("SECRET_KEY", "")


def is_production() -> bool:
    """Railway o una base que no es el SQLite local de desarrollo."""
    return bool(getenv("RAILWAY_ENVIRONMENT")) or not getenv(
        "DATABASE_URL", "sqlite:///./test.db"
    ).startswith("sqlite")


if not SECRET_KEY or SECRET_KEY == _INSECURE_DEFAULT_KEY:
    # Solo se tolera en desarrollo local (SQLite); en Railway/Postgres un JWT
    # firmado con una clave conocida permitiría falsificar sesiones.
    if is_production():
        raise RuntimeError("SECRET_KEY no configurada: defínela como variable de entorno en producción")
    print("⚠️ SECRET_KEY no configurada — usando clave insegura solo para desarrollo local")
    SECRET_KEY = _INSECURE_DEFAULT_KEY
ALGORITHM = "HS256"
# Sesiones cortas: si se filtra un token, sirve pocas horas
ACCESS_TOKEN_EXPIRE_HOURS = float(getenv("ACCESS_TOKEN_EXPIRE_HOURS", "12"))
BCRYPT_ROUNDS = 12
PASSWORD_MIN = 8
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15

# HTTP Bearer
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password using bcrypt."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:  # contraseña de más de 72 bytes o hash inválido
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Hashes creados con un costo menor al actual (p. ej. $2b$10$)."""
    try:
        return int(hashed_password.split("$")[2]) < BCRYPT_ROUNDS
    except (IndexError, ValueError):
        return False


def password_problem(password: str, username: str = "") -> Optional[str]:
    """Motivo por el que la contraseña no es aceptable, o None."""
    if len(password) < PASSWORD_MIN:
        return f"La contraseña debe tener al menos {PASSWORD_MIN} caracteres"
    if len(password.encode("utf-8")) > 72:
        return "La contraseña es demasiado larga (máximo 72 caracteres)"
    if username and password.lower() == username.lower():
        return "La contraseña no puede ser igual al usuario"
    if len(set(password)) < 4:
        return "La contraseña es demasiado simple"
    return None


# Hash de referencia para que un usuario inexistente tarde lo mismo que uno real
_DUMMY_HASH = bcrypt.hashpw(b"nutriapp-dummy", bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token."""
    to_encode = data.copy()
    # Convert "sub" to string if it's an integer (PyJWT requirement)
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])

    expire = utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def session_token(user: models.Nutritionist) -> str:
    """Token de sesión. `tv` (versión) permite invalidar todas las sesiones del usuario
    al cambiar la contraseña o la verificación en dos pasos."""
    return create_access_token({"sub": user.id, "tv": user.token_version or 0})


def revoke_sessions(user: models.Nutritionist) -> None:
    """Invalida todos los tokens emitidos hasta ahora (el llamador hace commit)."""
    user.token_version = (user.token_version or 0) + 1


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
    if payload.get("purpose"):
        # Tokens con propósito (p. ej. desafío de verificación en dos pasos) no son sesión
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload.get("sub"))  # Convert back from string

    user = db.query(models.Nutritionist).filter(models.Nutritionist.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    # Tokens anteriores a un cambio de contraseña/2FA (o sin versión) ya no valen
    if payload.get("tv") != (user.token_version or 0):
        raise HTTPException(status_code=401, detail="La sesión expiró. Vuelve a iniciar sesión.")

    return user


def is_locked(user: models.Nutritionist) -> bool:
    return bool(user.locked_until and user.locked_until > utcnow())


def register_failed_login(user: models.Nutritionist) -> None:
    """Cuenta un intento fallido; al quinto bloquea la cuenta 15 minutos (el llamador hace commit)."""
    user.failed_logins = (user.failed_logins or 0) + 1
    if user.failed_logins >= MAX_FAILED_LOGINS:
        user.locked_until = utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
        user.failed_logins = 0


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.Nutritionist]:
    """Usuario si la contraseña es correcta. Siempre corre bcrypt para no revelar,
    por el tiempo de respuesta, si el usuario existe."""
    user = db.query(models.Nutritionist).filter(models.Nutritionist.username == username).first()
    if not user:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
