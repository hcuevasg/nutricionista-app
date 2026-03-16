"""Appointments router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date

import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _to_response(appt: models.Appointment) -> schemas.AppointmentResponse:
    return schemas.AppointmentResponse(
        id=appt.id,
        nutritionist_id=appt.nutritionist_id,
        patient_id=appt.patient_id,
        patient_name=appt.patient.name if appt.patient else None,
        scheduled_at=appt.scheduled_at,
        duration_minutes=appt.duration_minutes,
        notes=appt.notes,
        status=appt.status,
        created_at=appt.created_at,
    )


@router.get("", response_model=List[schemas.AppointmentResponse])
async def list_appointments(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    patient_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    query = db.query(models.Appointment).filter(
        models.Appointment.nutritionist_id == current_user.id
    )
    if date_from:
        query = query.filter(models.Appointment.scheduled_at >= datetime.combine(date_from, datetime.min.time()))
    else:
        # Default: from today
        query = query.filter(models.Appointment.scheduled_at >= datetime.now().replace(hour=0, minute=0, second=0))
    if date_to:
        query = query.filter(models.Appointment.scheduled_at <= datetime.combine(date_to, datetime.max.time()))
    if patient_id:
        query = query.filter(models.Appointment.patient_id == patient_id)
    if status:
        query = query.filter(models.Appointment.status == status)
    appointments = query.order_by(models.Appointment.scheduled_at.asc()).limit(limit).all()
    return [_to_response(a) for a in appointments]


@router.post("", response_model=schemas.AppointmentResponse, status_code=201)
async def create_appointment(
    request: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    if request.patient_id:
        patient = db.query(models.Patient).filter(
            models.Patient.id == request.patient_id,
            models.Patient.nutritionist_id == current_user.id
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
    appt = models.Appointment(**request.model_dump(), nutritionist_id=current_user.id)
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return _to_response(appt)


@router.get("/{appt_id}", response_model=schemas.AppointmentResponse)
async def get_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appt_id,
        models.Appointment.nutritionist_id == current_user.id
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return _to_response(appt)


@router.put("/{appt_id}", response_model=schemas.AppointmentResponse)
async def update_appointment(
    appt_id: int,
    request: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appt_id,
        models.Appointment.nutritionist_id == current_user.id
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(appt, field, value)
    appt.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appt)
    return _to_response(appt)


@router.patch("/{appt_id}/status", response_model=schemas.AppointmentResponse)
async def update_appointment_status(
    appt_id: int,
    status: str = Query(..., pattern="^(scheduled|completed|cancelled)$"),
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appt_id,
        models.Appointment.nutritionist_id == current_user.id
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    appt.status = status
    appt.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appt)
    return _to_response(appt)


@router.delete("/{appt_id}")
async def delete_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appt_id,
        models.Appointment.nutritionist_id == current_user.id
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    db.delete(appt)
    db.commit()
    return {"message": "Cita eliminada"}
