"""Patient routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=List[schemas.PatientResponse])
async def list_patients(
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """List all patients for current user."""
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
    """Create a new patient."""
    patient = models.Patient(
        **request.dict(),
        nutritionist_id=current_user.id
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=schemas.PatientResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Get patient details."""
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
    """Update patient."""
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    for key, value in request.dict().items():
        setattr(patient, key, value)

    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Delete patient."""
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    db.delete(patient)
    db.commit()

    return {"message": "Patient deleted"}
