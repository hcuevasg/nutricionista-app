"""Patient portal — share token based read-only access."""
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/portal", tags=["portal"])


def _get_patient_by_token(token: str, db: Session) -> models.Patient:
    record = db.query(models.PatientShareToken).filter(
        models.PatientShareToken.token == token,
        models.PatientShareToken.revoked == False,
        models.PatientShareToken.expires_at > datetime.now(timezone.utc),
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Token no válido o expirado")
    return record.patient


# ── Nutritionist endpoints (require JWT) ──────────────────────────────────────

@router.post("/tokens", response_model=schemas.ShareTokenResponse, status_code=201)
async def create_share_token(
    request: schemas.ShareTokenCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == request.patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    token_str = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(days=request.days_valid)
    record = models.PatientShareToken(
        token=token_str,
        patient_id=patient.id,
        nutritionist_id=current_user.id,
        expires_at=expires,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.ShareTokenResponse(
        id=record.id,
        token=record.token,
        patient_id=record.patient_id,
        patient_name=patient.name,
        expires_at=record.expires_at,
        revoked=record.revoked,
        created_at=record.created_at,
    )


@router.get("/tokens", response_model=List[schemas.ShareTokenResponse])
async def list_share_tokens(
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    records = db.query(models.PatientShareToken).filter(
        models.PatientShareToken.nutritionist_id == current_user.id,
        models.PatientShareToken.revoked == False,
        models.PatientShareToken.expires_at > datetime.now(timezone.utc),
    ).all()
    return [
        schemas.ShareTokenResponse(
            id=r.id, token=r.token, patient_id=r.patient_id,
            patient_name=r.patient.name if r.patient else "—",
            expires_at=r.expires_at, revoked=r.revoked, created_at=r.created_at,
        ) for r in records
    ]


@router.delete("/tokens/{token_id}")
async def revoke_share_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    record = db.query(models.PatientShareToken).filter(
        models.PatientShareToken.id == token_id,
        models.PatientShareToken.nutritionist_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Token no encontrado")
    record.revoked = True
    db.commit()
    return {"message": "Token revocado"}


# ── Public patient-facing endpoints ───────────────────────────────────────────

@router.get("/{token}", response_model=schemas.PortalInfo)
async def portal_info(token: str, db: Session = Depends(get_db)):
    patient = _get_patient_by_token(token, db)
    nutritionist = db.query(models.Nutritionist).filter(
        models.Nutritionist.id == patient.nutritionist_id
    ).first()
    return schemas.PortalInfo(
        patient_name=patient.name,
        nutritionist_name=nutritionist.name if nutritionist else None,
        clinic_name=nutritionist.clinic_name if nutritionist else None,
    )


@router.get("/{token}/pautas", response_model=List[schemas.PautaResponse])
async def portal_pautas(token: str, db: Session = Depends(get_db)):
    patient = _get_patient_by_token(token, db)
    # Prefer active pauta, fallback to most recent
    active = db.query(models.Pauta).filter(
        models.Pauta.patient_id == patient.id,
        models.Pauta.is_active == True,
    ).first()
    if active:
        return [active]
    pautas = db.query(models.Pauta).filter(
        models.Pauta.patient_id == patient.id
    ).order_by(models.Pauta.date.desc()).limit(1).all()
    return pautas


@router.get("/{token}/evaluations", response_model=List[schemas.PortalEvaluationSummary])
async def portal_evaluations(token: str, db: Session = Depends(get_db)):
    patient = _get_patient_by_token(token, db)
    evals = db.query(models.Anthropometric).filter(
        models.Anthropometric.patient_id == patient.id
    ).order_by(models.Anthropometric.date.asc()).all()
    return [
        schemas.PortalEvaluationSummary(
            id=e.id, date=e.date,
            weight_kg=e.weight_kg, fat_mass_pct=e.fat_mass_pct, lean_mass_kg=e.lean_mass_kg,
        ) for e in evals
    ]
