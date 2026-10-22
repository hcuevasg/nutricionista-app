"""Reporte de errores del frontend y consulta del registro interno."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import auth
import error_log
import models
from database import get_db

router = APIRouter(tags=["errors"])
_optional_bearer = HTTPBearer(auto_error=False)


class FrontendError(BaseModel):
    message: str = Field(max_length=2000)
    stack: Optional[str] = Field(None, max_length=8000)
    path: Optional[str] = Field(None, max_length=500)


def user_id_from_token(token: Optional[str]) -> Optional[int]:
    """Id del profesional si el token de sesión es válido; None en otro caso (nunca falla)."""
    if not token:
        return None
    try:
        payload = auth.decode_token(token)
        return None if payload.get("purpose") else int(payload["sub"])
    except Exception:
        return None


@router.post("/errors/report", status_code=204)
async def report_frontend_error(
    err: FrontendError,
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_bearer),
):
    error_log.record(
        "frontend",
        nutritionist_id=user_id_from_token(credentials.credentials if credentials else None),
        path=(err.path or "").split("?")[0], error_type="frontend", message=err.message, stack=err.stack,
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/settings/error-logs")
async def get_error_logs(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    query = db.query(models.ErrorLog).filter(models.ErrorLog.nutritionist_id == current_user.id)
    rows = query.order_by(models.ErrorLog.created_at.desc()).limit(limit).all()
    return {
        "total": query.count(),
        "errors": [
            {
                "id": e.id, "source": e.source, "method": e.method, "path": e.path,
                "error_type": e.error_type, "message": e.message, "stack": e.stack,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in rows
        ],
    }
