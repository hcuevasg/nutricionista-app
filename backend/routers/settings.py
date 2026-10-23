"""Settings routes: audit logs + backup."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

import backup
import models
import auth
from database import get_db
from http_utils import attachment
from timeutil import utcnow

router = APIRouter(prefix="/settings", tags=["settings"])


# ── Audit logs ────────────────────────────────────────────────────────────────

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    logs = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.nutritionist_id == current_user.id)
        .order_by(models.AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.nutritionist_id == current_user.id)
        .count()
    )
    return {
        "total": total,
        "logs": [
            {
                "id": l.id,
                "action": l.action,
                "resource": l.resource,
                "resource_id": l.resource_id,
                "detail": l.detail,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }


# ── Backup ────────────────────────────────────────────────────────────────────

@router.get("/backup")
async def download_backup(
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    """Exporta todos los datos de la cuenta como JSON (versión 2)."""
    data = backup.export_data(db, current_user)
    import audit
    audit.log(db, action="export", resource="backup", nutritionist_id=current_user.id,
              detail=f"{len(data['patients'])} pacientes, {len(data['recetas'])} recetas exportados")
    filename = f"nutriapp_backup_{utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    return JSONResponse(content=data, headers=attachment(filename))


@router.post("/restore")
async def restore_backup(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    """Importa un backup: crea registros nuevos y omite pacientes/recetas que ya existen."""
    try:
        counts = backup.restore_data(db, current_user, data)
    except backup.BackupError as e:
        raise HTTPException(status_code=400, detail=str(e))
    import audit
    audit.log(db, action="import", resource="backup", nutritionist_id=current_user.id,
              detail=f"{counts['pacientes']} pacientes y {counts['recetas']} recetas restaurados")
    return counts
