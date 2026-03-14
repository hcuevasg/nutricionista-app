"""Anthropometric evaluation routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/anthropometrics", tags=["anthropometrics"])


@router.post("", response_model=schemas.AnthropometricResponse)
async def create_anthropometric(
    patient_id: int,
    request: schemas.AnthropometricCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Create ISAK evaluation for patient."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    anthropometric = models.Anthropometric(
        **request.model_dump(),
        patient_id=patient_id
    )
    db.add(anthropometric)
    db.commit()
    db.refresh(anthropometric)
    return anthropometric


@router.get("/{patient_id}", response_model=List[schemas.AnthropometricResponse])
async def list_patient_anthropometrics(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """List all ISAK evaluations for patient."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    anthropometrics = db.query(models.Anthropometric).filter(
        models.Anthropometric.patient_id == patient_id
    ).order_by(models.Anthropometric.created_at.desc()).all()

    return anthropometrics


@router.get("/{patient_id}/{eval_id}", response_model=schemas.AnthropometricResponse)
async def get_anthropometric(
    patient_id: int,
    eval_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Get specific ISAK evaluation."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    anthropometric = db.query(models.Anthropometric).filter(
        models.Anthropometric.id == eval_id,
        models.Anthropometric.patient_id == patient_id
    ).first()

    if not anthropometric:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return anthropometric


@router.put("/{patient_id}/{eval_id}", response_model=schemas.AnthropometricResponse)
async def update_anthropometric(
    patient_id: int,
    eval_id: int,
    request: schemas.AnthropometricCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Update ISAK evaluation."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    anthropometric = db.query(models.Anthropometric).filter(
        models.Anthropometric.id == eval_id,
        models.Anthropometric.patient_id == patient_id
    ).first()

    if not anthropometric:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    for key, value in request.model_dump().items():
        setattr(anthropometric, key, value)

    db.commit()
    db.refresh(anthropometric)
    return anthropometric


@router.delete("/{patient_id}/{eval_id}")
async def delete_anthropometric(
    patient_id: int,
    eval_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Delete ISAK evaluation."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    anthropometric = db.query(models.Anthropometric).filter(
        models.Anthropometric.id == eval_id,
        models.Anthropometric.patient_id == patient_id
    ).first()

    if not anthropometric:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    db.delete(anthropometric)
    db.commit()

    return {"message": "Evaluation deleted"}
