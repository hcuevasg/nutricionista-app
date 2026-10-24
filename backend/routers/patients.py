"""Patient routes."""
import json as _json
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
import auth
import audit
import backup
import consent
from database import get_db
from http_utils import attachment
from timeutil import utcnow

router = APIRouter(prefix="/patients", tags=["patients"])


def _check_rut_free(db: Session, user: models.Nutritionist, rut_value: str, exclude_id: Optional[int] = None) -> None:
    """Un mismo RUT no puede estar en dos pacientes de la misma cuenta."""
    query = db.query(models.Patient.id).filter(
        models.Patient.nutritionist_id == user.id, models.Patient.rut == rut_value
    )
    if exclude_id is not None:
        query = query.filter(models.Patient.id != exclude_id)
    if query.first():
        import rut
        raise HTTPException(status_code=400, detail=f"Ya existe un paciente con el RUT {rut.format_rut(rut_value)}")


def _serialize(data: dict) -> dict:
    """Serialize list fields to JSON strings for DB storage."""
    if 'allergies' in data:
        data['allergies'] = _json.dumps(data.get('allergies') or [])
    return data


@router.get("", response_model=schemas.PaginatedResponse[schemas.PatientResponse])
async def list_patients(
    q: Optional[str] = Query(None, description="Filtrar por nombre, RUT, email o teléfono"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    query = db.query(models.Patient).filter(
        models.Patient.nutritionist_id == current_user.id
    )
    if q:
        like = f"%{q}%"
        # El RUT se guarda sin puntos: "12.345" también encuentra "12345678-5"
        rut_like = f"%{q.replace('.', '').strip()}%"
        query = query.filter(
            models.Patient.name.ilike(like) |
            models.Patient.rut.ilike(rut_like) |
            models.Patient.email.ilike(like) |
            models.Patient.phone.ilike(like)
        )
    total = query.count()
    patients = query.order_by(models.Patient.name).offset(skip).limit(limit).all()
    return schemas.PaginatedResponse(items=patients, total=total, skip=skip, limit=limit)


@router.post("", response_model=schemas.PatientResponse)
async def create_patient(
    request: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    if not request.rut:
        raise HTTPException(status_code=422, detail="El RUT es obligatorio")
    _check_rut_free(db, current_user, request.rut)
    data = _serialize(request.model_dump())
    patient = models.Patient(**data, nutritionist_id=current_user.id)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    audit.log(db, action="create", resource="patient", nutritionist_id=current_user.id,
               resource_id=patient.id, detail=patient.name)
    return patient


@router.get("/{patient_id}", response_model=schemas.PatientResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/{patient_id}", response_model=schemas.PatientResponse)
async def update_patient(
    patient_id: int,
    request: schemas.PatientUpdate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    # Solo los campos enviados: un campo que el cliente no manda nunca se borra
    data = _serialize(request.model_dump(exclude_unset=True))
    if data.get("rut"):
        _check_rut_free(db, current_user, data["rut"], exclude_id=patient.id)
    for key, value in data.items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    audit.log(db, action="update", resource="patient", nutritionist_id=current_user.id,
               resource_id=patient.id, detail=patient.name)
    return patient


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    name = patient.name
    db.delete(patient)
    db.commit()
    audit.log(db, action="delete", resource="patient", nutritionist_id=current_user.id,
               resource_id=patient_id, detail=name)
    return {"message": "Patient deleted"}


def _owned_patient(db: Session, patient_id: int, user: models.Nutritionist) -> models.Patient:
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("/{patient_id}/consent", response_model=schemas.PatientResponse)
async def set_consent(
    patient_id: int,
    req: schemas.PatientConsentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Registra (o revoca) el consentimiento del paciente para tratar sus datos de salud."""
    patient = _owned_patient(db, patient_id, current_user)
    consent.set_consent(patient, req.accepted, "profesional", request)
    db.commit()
    db.refresh(patient)
    audit.log(db, action="consent" if req.accepted else "consent_revoked", resource="patient",
              nutritionist_id=current_user.id, resource_id=patient.id, detail=patient.name)
    return patient


@router.get("/{patient_id}/export")
async def export_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Ficha completa del paciente en JSON (derecho de acceso y portabilidad)."""
    patient = _owned_patient(db, patient_id, current_user)
    data = {
        "exported_at": utcnow().isoformat(),
        "profesional": {"name": current_user.name, "clinic_name": current_user.clinic_name,
                        "email": current_user.email},
        "paciente": backup.export_patient(db, current_user, patient),
    }
    audit.log(db, action="export", resource="patient", nutritionist_id=current_user.id,
              resource_id=patient.id, detail=patient.name)
    filename = f"ficha_paciente_{patient.id}_{date.today().isoformat()}.json"
    return JSONResponse(data, headers=attachment(filename))
