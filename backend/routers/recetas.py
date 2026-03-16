"""Recetas routes — gestión de recetas personalizadas del nutricionista."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/recetas", tags=["recetas"])


def _get_receta_or_404(receta_id: int, nutritionist_id: int, db: Session) -> models.Receta:
    receta = db.query(models.Receta).filter(
        models.Receta.id == receta_id,
        models.Receta.nutritionist_id == nutritionist_id
    ).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    return receta


@router.get("/", response_model=schemas.PaginatedResponse[schemas.RecetaListItem])
def list_recetas(
    q: str = "",
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    query = db.query(models.Receta).filter(
        models.Receta.nutritionist_id == current_user.id
    )
    if q:
        like = f"%{q}%"
        query = query.filter(
            models.Receta.nombre.ilike(like) |
            models.Receta.categoria.ilike(like) |
            models.Receta.descripcion.ilike(like)
        )
    total = query.count()
    recetas = query.order_by(models.Receta.nombre).offset(skip).limit(limit).all()
    return schemas.PaginatedResponse(items=recetas, total=total, skip=skip, limit=limit)


@router.post("/", response_model=schemas.RecetaResponse, status_code=201)
def create_receta(
    data: schemas.RecetaCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    receta = models.Receta(
        nutritionist_id=current_user.id,
        **data.model_dump()
    )
    db.add(receta)
    db.commit()
    db.refresh(receta)
    return receta


@router.get("/{receta_id}", response_model=schemas.RecetaResponse)
def get_receta(
    receta_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    return _get_receta_or_404(receta_id, current_user.id, db)


@router.put("/{receta_id}", response_model=schemas.RecetaResponse)
def update_receta(
    receta_id: int,
    data: schemas.RecetaUpdate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    receta = _get_receta_or_404(receta_id, current_user.id, db)

    # Update basic fields
    receta.nombre = data.nombre
    receta.descripcion = data.descripcion
    receta.categoria = data.categoria
    receta.porciones_rinde = data.porciones_rinde
    receta.notas = data.notas

    # Replace ingredientes if provided
    if data.ingredientes is not None:
        db.query(models.RecetaIngrediente).filter(
            models.RecetaIngrediente.receta_id == receta_id
        ).delete()
        for ing in data.ingredientes:
            db.add(models.RecetaIngrediente(receta_id=receta_id, **ing.model_dump()))

    # Replace equivalencias if provided
    if data.equivalencias is not None:
        db.query(models.RecetaEquivalencia).filter(
            models.RecetaEquivalencia.receta_id == receta_id
        ).delete()
        for eq in data.equivalencias:
            if eq.porciones > 0:
                db.add(models.RecetaEquivalencia(receta_id=receta_id, **eq.model_dump()))

    db.commit()
    db.refresh(receta)
    return receta


@router.delete("/{receta_id}", status_code=204)
def delete_receta(
    receta_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    receta = _get_receta_or_404(receta_id, current_user.id, db)
    db.delete(receta)
    db.commit()
