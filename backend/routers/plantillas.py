"""Plantillas reutilizables de pautas (por nutricionista)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import get_db

router = APIRouter(prefix="/plantillas-pauta", tags=["plantillas"])


@router.get("", response_model=List[schemas.PlantillaPautaResponse])
async def list_plantillas(
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    return (db.query(models.PlantillaPauta)
            .filter(models.PlantillaPauta.nutritionist_id == current_user.id)
            .order_by(models.PlantillaPauta.nombre).all())


@router.post("", response_model=schemas.PlantillaPautaResponse, status_code=201)
async def create_plantilla(
    request: schemas.PlantillaPautaCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    if not request.nombre.strip():
        raise HTTPException(status_code=422, detail="La plantilla necesita un nombre")
    plantilla = models.PlantillaPauta(**request.model_dump(), nutritionist_id=current_user.id)
    plantilla.nombre = plantilla.nombre.strip()
    db.add(plantilla)
    db.commit()
    db.refresh(plantilla)
    return plantilla


@router.delete("/{plantilla_id}", status_code=204)
async def delete_plantilla(
    plantilla_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    plantilla = db.query(models.PlantillaPauta).filter(
        models.PlantillaPauta.id == plantilla_id,
        models.PlantillaPauta.nutritionist_id == current_user.id,
    ).first()
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    db.delete(plantilla)
    db.commit()
