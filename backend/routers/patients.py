"""Patient routes."""
import json as _json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
import auth
import audit
from database import get_db

router = APIRouter(prefix="/patients", tags=["patients"])


def _serialize(data: dict) -> dict:
    """Serialize list fields to JSON strings for DB storage."""
    data['allergies'] = _json.dumps(data.get('allergies') or [])
    return data


@router.get("", response_model=schemas.PaginatedResponse[schemas.PatientResponse])
async def list_patients(
    q: Optional[str] = Query(None, description="Filtrar por nombre, email o teléfono"),
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
        query = query.filter(
            models.Patient.name.ilike(like) |
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
    data = _serialize(request.model_dump())
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
