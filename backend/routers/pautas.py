"""Pautas de alimentación routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/pautas", tags=["pautas"])


@router.post("", response_model=schemas.PautaResponse)
async def create_pauta(
    patient_id: int,
    request: schemas.PautaCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    pauta = models.Pauta(**request.model_dump(), patient_id=patient_id)
    db.add(pauta)
    db.commit()
    db.refresh(pauta)
    return pauta


@router.get("/{patient_id}", response_model=List[schemas.PautaResponse])
async def list_pautas(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db.query(models.Pauta).filter(
        models.Pauta.patient_id == patient_id
    ).order_by(models.Pauta.created_at.desc()).all()


@router.get("/{patient_id}/{pauta_id}", response_model=schemas.PautaResponse)
async def get_pauta(
    patient_id: int,
    pauta_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    pauta = db.query(models.Pauta).filter(
        models.Pauta.id == pauta_id,
        models.Pauta.patient_id == patient_id
    ).first()
    if not pauta:
        raise HTTPException(status_code=404, detail="Pauta not found")
    return pauta


@router.delete("/{patient_id}/{pauta_id}")
async def delete_pauta(
    patient_id: int,
    pauta_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    pauta = db.query(models.Pauta).filter(
        models.Pauta.id == pauta_id,
        models.Pauta.patient_id == patient_id
    ).first()
    if not pauta:
        raise HTTPException(status_code=404, detail="Pauta not found")
    db.delete(pauta)
    db.commit()
    return {"message": "Pauta deleted"}
