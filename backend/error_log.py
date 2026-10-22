"""Registro interno de errores (backend y frontend).

Se guarda en la propia base de datos para revisarlo desde Configuración, sin
servicios externos. Nunca se guardan cuerpos de request ni query strings, y se
quitan los parámetros SQL de los mensajes de SQLAlchemy: pueden traer datos de
pacientes.
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

import models
from database import SessionLocal

logger = logging.getLogger(__name__)

RETENTION_DAYS = 90
_SQL_PARAMS = re.compile(r"\[parameters: .*?\]", re.DOTALL)


def _clean(text: Optional[str], limit: int) -> Optional[str]:
    if not text:
        return None
    text = _SQL_PARAMS.sub("[parameters: omitidos]", str(text))
    return text[:limit]


def record(source: str, *, nutritionist_id: Optional[int] = None, method: Optional[str] = None,
           path: Optional[str] = None, error_type: Optional[str] = None, message: Optional[str] = None,
           stack: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[int]:
    """Guarda un error en una sesión propia (la del request puede estar rota). Devuelve su id."""
    db = SessionLocal()
    try:
        entry = models.ErrorLog(
            source=source, nutritionist_id=nutritionist_id, method=method, path=_clean(path, 500),
            error_type=_clean(error_type, 120), message=_clean(message, 2000), stack=_clean(stack, 8000),
            user_agent=_clean(user_agent, 300),
        )
        db.add(entry)
        db.query(models.ErrorLog).filter(
            models.ErrorLog.created_at < datetime.utcnow() - timedelta(days=RETENTION_DAYS)
        ).delete(synchronize_session=False)
        db.commit()
        return entry.id
    except Exception:
        logger.exception("No se pudo guardar el error en error_logs")
        db.rollback()
        return None
    finally:
        db.close()
