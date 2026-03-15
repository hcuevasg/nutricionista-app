"""Antecedentes clínicos del paciente."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/antecedentes", tags=["antecedentes"])


@router.get("/{patient_id}", response_model=schemas.AntecedentesResponse)
async def get_antecedentes(
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
    ant = db.query(models.Antecedentes).filter(
        models.Antecedentes.patient_id == patient_id
    ).first()
    if not ant:
        raise HTTPException(status_code=404, detail="Antecedentes not found")
    return ant


@router.post("/{patient_id}", response_model=schemas.AntecedentesResponse)
async def create_or_update_antecedentes(
    patient_id: int,
    request: schemas.AntecedentesCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    ant = db.query(models.Antecedentes).filter(
        models.Antecedentes.patient_id == patient_id
    ).first()
    if ant:
        for key, value in request.model_dump(exclude_unset=False).items():
            setattr(ant, key, value)
    else:
        ant = models.Antecedentes(**request.model_dump(), patient_id=patient_id)
        db.add(ant)
    db.commit()
    db.refresh(ant)
    return ant
