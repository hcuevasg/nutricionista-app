"""Hora UTC sin zona horaria: las columnas DateTime de la base no guardan tz."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Reemplazo de datetime.utcnow() (obsoleto desde Python 3.12), mismo resultado."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
