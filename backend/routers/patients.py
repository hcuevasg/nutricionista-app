"""Patient routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
import auth
import audit
from database import get_db

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=List[schemas.PatientResponse])
async def list_patients(
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    patients = db.query(models.Patient).filter(
        models.Patient.nutritionist_id == current_user.id
    ).all()
    return patients


@router.post("", response_model=schemas.PatientResponse)
async def create_patient(
    request: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    patient = models.Patient(**request.model_dump(), nutritionist_id=current_user.id)
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
    for key, value in request.model_dump().items():
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
