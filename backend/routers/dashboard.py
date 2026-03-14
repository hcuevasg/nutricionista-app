"""Dashboard routes — stats and recent activity."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
import auth
from database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    """Counts for stat cards."""
    patient_ids = (
        db.query(models.Patient.id)
        .filter(models.Patient.nutritionist_id == current_user.id)
        .subquery()
    )

    total_patients = db.query(func.count(models.Patient.id)).filter(
        models.Patient.nutritionist_id == current_user.id
    ).scalar()

    total_evaluations = db.query(func.count(models.Anthropometric.id)).filter(
        models.Anthropometric.patient_id.in_(patient_ids)
    ).scalar()

    total_plans = db.query(func.count(models.MealPlan.id)).filter(
        models.MealPlan.patient_id.in_(patient_ids)
    ).scalar()

    total_pautas = db.query(func.count(models.Pauta.id)).filter(
        models.Pauta.patient_id.in_(patient_ids)
    ).scalar()

    return {
        "total_patients": total_patients or 0,
        "total_evaluations": total_evaluations or 0,
        "total_plans": total_plans or 0,
        "total_pautas": total_pautas or 0,
    }


@router.get("/recent-patients")
async def get_recent_patients(
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    """Last 5 patients with their latest evaluation date."""
    patients = (
        db.query(models.Patient)
        .filter(models.Patient.nutritionist_id == current_user.id)
        .order_by(models.Patient.created_at.desc())
        .limit(5)
        .all()
    )

    result = []
    for p in patients:
        latest_eval = (
            db.query(models.Anthropometric)
            .filter(models.Anthropometric.patient_id == p.id)
            .order_by(models.Anthropometric.created_at.desc())
            .first()
        )
        latest_plan = (
            db.query(models.MealPlan)
            .filter(models.MealPlan.patient_id == p.id)
            .order_by(models.MealPlan.created_at.desc())
            .first()
        )
        result.append({
            "id": p.id,
            "name": p.name,
            "sex": p.sex,
            "birth_date": p.birth_date,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "last_evaluation": latest_eval.date if latest_eval else None,
            "last_plan": latest_plan.name if latest_plan else None,
        })

    return result
