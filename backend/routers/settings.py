"""Settings routes: audit logs + backup."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

import models
import auth
from database import get_db

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
    """Export all data for current nutritionist as JSON."""
    patients = db.query(models.Patient).filter(
        models.Patient.nutritionist_id == current_user.id
    ).all()

    def row(obj, exclude=("_sa_instance_state",)):
        return {
            k: (v.isoformat() if isinstance(v, datetime) else v)
            for k, v in obj.__dict__.items()
            if k not in exclude and not k.startswith("_")
        }

    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "nutritionist": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "name": current_user.name,
        },
        "patients": [],
    }

    for p in patients:
        patient_data = row(p)

        anthropometrics = db.query(models.Anthropometric).filter(
            models.Anthropometric.patient_id == p.id
        ).all()
        patient_data["anthropometrics"] = [row(a) for a in anthropometrics]

        meal_plans = db.query(models.MealPlan).filter(
            models.MealPlan.patient_id == p.id
        ).all()
        plans_data = []
        for mp in meal_plans:
            mp_data = row(mp)
            items = db.query(models.MealItem).filter(
                models.MealItem.plan_id == mp.id
            ).all()
            mp_data["items"] = [row(i) for i in items]
            plans_data.append(mp_data)
        patient_data["meal_plans"] = plans_data

        pautas = db.query(models.Pauta).filter(
            models.Pauta.patient_id == p.id
        ).all()
        patient_data["pautas"] = [row(pa) for pa in pautas]

        data["patients"].append(patient_data)

    # Log the backup action
    import audit
    audit.log(db, action="export", resource="backup", nutritionist_id=current_user.id,
               detail=f"{len(patients)} pacientes exportados")

    filename = f"nutriapp_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
