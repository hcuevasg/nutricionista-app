"""Notas de evolución por consulta (formato SOAP)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import audit
import auth
import models
import schemas
from database import get_db
from routers.patients import _owned_patient

router = APIRouter(prefix="/notas", tags=["notas"])


def _nota(db: Session, patient_id: int, nota_id: int) -> models.NotaEvolucion:
    nota = db.query(models.NotaEvolucion).filter(
        models.NotaEvolucion.id == nota_id, models.NotaEvolucion.patient_id == patient_id
    ).first()
    if not nota:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return nota


@router.get("/{patient_id}", response_model=List[schemas.NotaEvolucionResponse])
async def list_notas(patient_id: int, db: Session = Depends(get_db),
                     current_user: models.Nutritionist = Depends(auth.get_current_user)):
    _owned_patient(db, patient_id, current_user)
    return (db.query(models.NotaEvolucion)
            .filter(models.NotaEvolucion.patient_id == patient_id)
            .order_by(models.NotaEvolucion.fecha.desc(), models.NotaEvolucion.id.desc())
            .all())


@router.post("/{patient_id}", response_model=schemas.NotaEvolucionResponse, status_code=201)
async def create_nota(patient_id: int, req: schemas.NotaEvolucionCreate, db: Session = Depends(get_db),
                      current_user: models.Nutritionist = Depends(auth.get_current_user)):
    patient = _owned_patient(db, patient_id, current_user)
    nota = models.NotaEvolucion(**req.model_dump(), patient_id=patient_id)
    db.add(nota)
    db.commit()
    db.refresh(nota)
    audit.log(db, action="create", resource="nota", nutritionist_id=current_user.id,
              resource_id=nota.id, detail=patient.name)
    return nota


@router.put("/{patient_id}/{nota_id}", response_model=schemas.NotaEvolucionResponse)
async def update_nota(patient_id: int, nota_id: int, req: schemas.NotaEvolucionCreate,
                      db: Session = Depends(get_db),
                      current_user: models.Nutritionist = Depends(auth.get_current_user)):
    patient = _owned_patient(db, patient_id, current_user)
    nota = _nota(db, patient_id, nota_id)
    for key, value in req.model_dump().items():
        setattr(nota, key, value)
    db.commit()
    db.refresh(nota)
    audit.log(db, action="update", resource="nota", nutritionist_id=current_user.id,
              resource_id=nota.id, detail=patient.name)
    return nota


@router.delete("/{patient_id}/{nota_id}", status_code=204)
async def delete_nota(patient_id: int, nota_id: int, db: Session = Depends(get_db),
                      current_user: models.Nutritionist = Depends(auth.get_current_user)):
    patient = _owned_patient(db, patient_id, current_user)
    db.delete(_nota(db, patient_id, nota_id))
    db.commit()
    audit.log(db, action="delete", resource="nota", nutritionist_id=current_user.id,
              resource_id=nota_id, detail=patient.name)
