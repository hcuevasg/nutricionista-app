"""Exámenes de laboratorio del paciente con rangos de referencia."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import audit
import auth
import lab_catalog
import models
import schemas
from database import get_db
from routers.patients import _owned_patient

router = APIRouter(prefix="/laboratorio", tags=["laboratorio"])


def _response(e: models.ExamenLaboratorio) -> schemas.ExamenResponse:
    nombre, grupo, _, _, _ = lab_catalog.CATALOG.get(e.analito, (e.analito, "Otros", None, None, None))
    return schemas.ExamenResponse(
        id=e.id, fecha=e.fecha, analito=e.analito, nombre=nombre, grupo=grupo, valor=e.valor,
        unidad=e.unidad, ref_min=e.ref_min, ref_max=e.ref_max, notas=e.notas,
        estado=lab_catalog.status(e.valor, e.ref_min, e.ref_max),
    )


@router.get("/{patient_id}/catalogo")
async def catalogo(patient_id: int, db: Session = Depends(get_db),
                   current_user: models.Nutritionist = Depends(auth.get_current_user)):
    """Analitos disponibles con el rango de referencia según el sexo del paciente."""
    patient = _owned_patient(db, patient_id, current_user)
    return lab_catalog.as_list(patient.sex)


@router.get("/{patient_id}", response_model=List[schemas.ExamenResponse])
async def list_examenes(patient_id: int, db: Session = Depends(get_db),
                        current_user: models.Nutritionist = Depends(auth.get_current_user)):
    _owned_patient(db, patient_id, current_user)
    rows = (db.query(models.ExamenLaboratorio)
            .filter(models.ExamenLaboratorio.patient_id == patient_id)
            .order_by(models.ExamenLaboratorio.fecha.desc(), models.ExamenLaboratorio.id)
            .all())
    return [_response(e) for e in rows]


@router.post("/{patient_id}", response_model=List[schemas.ExamenResponse], status_code=201)
async def create_examenes(patient_id: int, req: schemas.ExamenesCreate, db: Session = Depends(get_db),
                          current_user: models.Nutritionist = Depends(auth.get_current_user)):
    """Registra los resultados de una toma de muestra (varios analitos, una fecha)."""
    patient = _owned_patient(db, patient_id, current_user)
    if not req.resultados:
        raise HTTPException(status_code=422, detail="Ingresa al menos un resultado")
    created = []
    for r in req.resultados:
        if r.analito not in lab_catalog.CATALOG:
            raise HTTPException(status_code=422, detail=f"Examen desconocido: {r.analito}")
        default_min, default_max = lab_catalog.reference(r.analito, patient.sex)
        fields = r.model_fields_set
        e = models.ExamenLaboratorio(
            patient_id=patient_id, fecha=req.fecha, analito=r.analito, valor=r.valor,
            unidad=lab_catalog.CATALOG[r.analito][2], notas=r.notas,
            ref_min=r.ref_min if "ref_min" in fields else default_min,
            ref_max=r.ref_max if "ref_max" in fields else default_max,
        )
        db.add(e)
        created.append(e)
    db.commit()
    audit.log(db, action="create", resource="laboratorio", nutritionist_id=current_user.id,
              resource_id=patient_id, detail=f"{patient.name}: {len(created)} resultados del {req.fecha}")
    return [_response(e) for e in created]


@router.delete("/{patient_id}/{examen_id}", status_code=204)
async def delete_examen(patient_id: int, examen_id: int, db: Session = Depends(get_db),
                        current_user: models.Nutritionist = Depends(auth.get_current_user)):
    patient = _owned_patient(db, patient_id, current_user)
    e = db.query(models.ExamenLaboratorio).filter(
        models.ExamenLaboratorio.id == examen_id, models.ExamenLaboratorio.patient_id == patient_id
    ).first()
    if not e:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    db.delete(e)
    db.commit()
    audit.log(db, action="delete", resource="laboratorio", nutritionist_id=current_user.id,
              resource_id=examen_id, detail=patient.name)
