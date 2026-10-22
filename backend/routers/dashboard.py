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

    total_pautas = db.query(func.count(models.Pauta.id)).filter(
        models.Pauta.patient_id.in_(patient_ids)
    ).scalar()

    return {
        "total_patients": total_patients or 0,
        "total_evaluations": total_evaluations or 0,
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
        result.append({
            "id": p.id,
            "name": p.name,
            "sex": p.sex,
            "birth_date": p.birth_date,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "last_evaluation": latest_eval.date if latest_eval else None,
        })

    return result


@router.get("/alerts")
async def get_alerts(
    weeks: int = 8,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    """Pacientes que necesitan seguimiento, ordenados por prioridad.

    - evaluacion_vencida: pasó la fecha de próxima evaluación registrada
    - evaluacion_proxima: la próxima evaluación es en los próximos 14 días
    - sin_control: última evaluación hace más de `weeks` semanas y sin cita futura
    - sin_evaluacion: paciente creado hace más de 2 semanas sin evaluaciones
    - sin_pauta: tiene evaluaciones pero ninguna pauta activa
    """
    from datetime import date, datetime, timedelta

    today = date.today()
    now = datetime.utcnow()
    patients = db.query(models.Patient).filter(models.Patient.nutritionist_id == current_user.id).all()
    ids = [p.id for p in patients]
    if not ids:
        return []

    def parse(d):
        try:
            return date.fromisoformat(str(d)[:10])
        except (TypeError, ValueError):
            return None

    last_eval = {}
    for ev in (db.query(models.Anthropometric).filter(models.Anthropometric.patient_id.in_(ids))
               .order_by(models.Anthropometric.date.asc()).all()):
        last_eval[ev.patient_id] = ev  # queda la más reciente
    future_appt = {a.patient_id for a in db.query(models.Appointment).filter(
        models.Appointment.nutritionist_id == current_user.id,
        models.Appointment.patient_id.in_(ids),
        models.Appointment.scheduled_at >= now,
        models.Appointment.status == "scheduled",
    ).all()}
    active_pauta = {p.patient_id for p in db.query(models.Pauta).filter(
        models.Pauta.patient_id.in_(ids), models.Pauta.is_active == True  # noqa: E712
    ).all()}

    priority = {"evaluacion_vencida": 0, "sin_control": 1, "evaluacion_proxima": 2,
                "sin_evaluacion": 3, "sin_pauta": 4}
    alerts = []

    def add(p, tipo, detalle, fecha=None):
        alerts.append({"patient_id": p.id, "patient_name": p.name, "tipo": tipo,
                       "detalle": detalle, "fecha": fecha.isoformat() if fecha else None})

    for p in patients:
        ev = last_eval.get(p.id)
        if ev is None:
            created = p.created_at.date() if p.created_at else today
            if (today - created).days > 14:
                add(p, "sin_evaluacion", "Sin evaluación antropométrica inicial")
            continue
        nxt = parse(getattr(ev, "next_eval_date", None))
        last = parse(ev.date)
        if nxt and nxt < today and p.id not in future_appt:
            add(p, "evaluacion_vencida", f"Próxima evaluación era el {nxt.strftime('%d-%m-%Y')}", nxt)
        elif nxt and today <= nxt <= today + timedelta(days=14):
            add(p, "evaluacion_proxima", f"Próxima evaluación el {nxt.strftime('%d-%m-%Y')}", nxt)
        elif last and (today - last).days > weeks * 7 and p.id not in future_appt:
            add(p, "sin_control", f"Último control hace {(today - last).days // 7} semanas", last)
        if p.id not in active_pauta:
            add(p, "sin_pauta", "Sin pauta activa")

    alerts.sort(key=lambda a: (priority[a["tipo"]], a["fecha"] or ""))
    return alerts
