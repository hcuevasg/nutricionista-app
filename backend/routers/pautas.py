"""Pautas de alimentación routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io
import json

import logging

import ai_service
import models, schemas, auth
from ai_service import AIError, TIPO_LABELS, NOMBRES_GRUPOS as _NOMBRES_GRUPOS, TIEMPOS_COMIDA as _TIEMPOS_COMIDA
from database import get_db, SessionLocal
from http_utils import attachment

logger = logging.getLogger(__name__)

# ── Food group data (mirrored from frontend) ──────────────────────────────

_GRUPOS_MACROS = {
    "cereales":           {"kcal": 140, "cho": 30,  "lip": 1,   "prot": 3},
    "verduras_cg":        {"kcal": 30,  "cho": 5,   "lip": 0,   "prot": 2},
    "verduras_lc":        {"kcal": 10,  "cho": 2.5, "lip": 0,   "prot": 0},
    "frutas":             {"kcal": 65,  "cho": 15,  "lip": 0,   "prot": 1},
    "lacteos_ag":         {"kcal": 110, "cho": 9,   "lip": 6,   "prot": 5},
    "lacteos_mg":         {"kcal": 85,  "cho": 9,   "lip": 3,   "prot": 5},
    "lacteos_bg":         {"kcal": 70,  "cho": 10,  "lip": 0,   "prot": 7},
    "legumbres":          {"kcal": 170, "cho": 32,  "lip": 1,   "prot": 13},
    "carnes_ag":          {"kcal": 120, "cho": 1,   "lip": 8,   "prot": 11},
    "carnes_bg":          {"kcal": 65,  "cho": 1,   "lip": 2,   "prot": 11},
    "otros_proteicos":    {"kcal": 75,  "cho": 5,   "lip": 3,   "prot": 7},
    "aceite_grasas":      {"kcal": 180, "cho": 0,   "lip": 20,  "prot": 0},
    "alim_ricos_lipidos": {"kcal": 175, "cho": 5,   "lip": 15,  "prot": 5},
    "leches_vegetales":   {"kcal": 80,  "cho": 10,  "lip": 2,   "prot": 1},
    "lacteos_soya":       {"kcal": 80,  "cho": 9,   "lip": 4,   "prot": 6},
    "semillas_chia":      {"kcal": 37,  "cho": 2,   "lip": 2,   "prot": 1.5},
    "azucares":           {"kcal": 20,  "cho": 5,   "lip": 0,   "prot": 0},
}

router = APIRouter(prefix="/pautas", tags=["pautas"])


# ── AI Status (must be declared BEFORE /{patient_id} routes) ─────────────────

@router.get("/ai-status")
async def ai_status(
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    return {
        "configured": ai_service.is_configured(),
        "model": ai_service.model_name(),
        "provider": ai_service.PROVIDER,
    }


# ── SSE streaming menu generation ────────────────────────────────────────────

@router.get("/{patient_id}/{pauta_id}/generar-menu-stream")
async def generar_menu_stream(
    patient_id: int,
    pauta_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    """SSE endpoint for AI menu generation. El frontend lo consume con fetch +
    ReadableStream para poder enviar el JWT en el header Authorization."""
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    pauta = db.query(models.Pauta).filter(
        models.Pauta.id == pauta_id,
        models.Pauta.patient_id == patient_id
    ).first()
    if not pauta:
        raise HTTPException(status_code=404, detail="Pauta no encontrada")

    if not ai_service.is_configured():
        raise HTTPException(status_code=503, detail="IA no configurada: falta ANTHROPIC_API_KEY en el servidor")
    try:
        menu_request = ai_service.build_menu_request(pauta, patient.allergies)
    except AIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    pauta_id_val = pauta.id

    def sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def event_stream():
        total = len(menu_request.tiempos)
        yield sse("status", {"step": "generating", "msg": f"Generando menú con IA (0 de {total} tiempos)..."})
        menu = None
        try:
            async for event in ai_service.stream_menu(menu_request):
                if event["type"] == "progress":
                    yield sse("status", {"step": "generating",
                                         "msg": f"Generando menú con IA ({event['done']} de {event['total']} tiempos)..."})
                elif event["type"] == "menu":
                    menu = event["menu"]
        except AIError as e:
            yield sse("error", {"message": e.message})
            return

        # Persist menu con una sesión propia: la sesión de la request puede estar
        # cerrada mientras se transmite la respuesta.
        stream_db = SessionLocal()
        try:
            stream_db.query(models.Pauta).filter(models.Pauta.id == pauta_id_val).update(
                {"menu_json": json.dumps(menu, ensure_ascii=False)}
            )
            stream_db.commit()
        finally:
            stream_db.close()

        yield sse("result", {"menu": menu})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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


@router.put("/{patient_id}/{pauta_id}", response_model=schemas.PautaResponse)
async def update_pauta(
    patient_id: int,
    pauta_id: int,
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
    pauta = db.query(models.Pauta).filter(
        models.Pauta.id == pauta_id,
        models.Pauta.patient_id == patient_id
    ).first()
    if not pauta:
        raise HTTPException(status_code=404, detail="Pauta not found")
    # Solo los campos enviados: editar la pauta no borra el menú generado (menu_json)
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(pauta, key, value)
    db.commit()
    db.refresh(pauta)
    return pauta


@router.post("/{patient_id}/{pauta_id}/duplicar", response_model=schemas.PautaResponse, status_code=201)
async def duplicar_pauta(
    patient_id: int,
    pauta_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    """Copia una pauta del mismo paciente con fecha de hoy (queda inactiva)."""
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    pauta = db.query(models.Pauta).filter(
        models.Pauta.id == pauta_id,
        models.Pauta.patient_id == patient_id,
    ).first()
    if not pauta:
        raise HTTPException(status_code=404, detail="Pauta no encontrada")
    from datetime import date as _date
    skip = {"id", "created_at", "updated_at", "is_active"}
    data = {c.name: getattr(pauta, c.name) for c in models.Pauta.__table__.columns if c.name not in skip}
    data.update(name=f"{pauta.name} (copia)", date=_date.today().isoformat(), is_active=False)
    copia = models.Pauta(**data)
    db.add(copia)
    db.commit()
    db.refresh(copia)
    return copia


@router.patch("/{patient_id}/{pauta_id}/set-active")
async def set_active_pauta(
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
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    pauta = db.query(models.Pauta).filter(
        models.Pauta.id == pauta_id,
        models.Pauta.patient_id == patient_id,
    ).first()
    if not pauta:
        raise HTTPException(status_code=404, detail="Pauta no encontrada")
    # Desactivar todas las pautas del paciente y activar la seleccionada
    db.query(models.Pauta).filter(
        models.Pauta.patient_id == patient_id
    ).update({"is_active": False})
    pauta.is_active = True
    db.commit()
    return {"message": "Pauta activa actualizada"}


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


@router.patch("/{patient_id}/{pauta_id}/menu")
async def update_menu(
    patient_id: int,
    pauta_id: int,
    body: dict,
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
    pauta.menu_json = json.dumps(body.get("menu", {}), ensure_ascii=False)
    db.commit()
    return {"ok": True}


@router.get("/{patient_id}/{pauta_id}/pdf")
async def download_pauta_pdf(
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

    pdf_bytes = _generate_pauta_pdf(patient, pauta, current_user)
    filename = f"pauta_{patient.name.replace(' ', '_')}_{pauta.date}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers=attachment(filename),
    )


# ── Generador de menú con IA (Claude) ─────────────────────────────────────────

@router.post("/{patient_id}/{pauta_id}/generar-menu")
async def generar_menu_ia(
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

    try:
        menu = await ai_service.generate_menu(ai_service.build_menu_request(pauta, patient.allergies))
    except AIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    pauta.menu_json = json.dumps(menu, ensure_ascii=False)
    db.commit()
    db.refresh(pauta)
    return {"menu": menu}


# ── Sugerencias IA para ajuste de pauta ─────────────────────────────────────

@router.post("/{patient_id}/{pauta_id}/ai-suggest")
async def ai_suggest_pauta(
    patient_id: int,
    pauta_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    """Analiza la pauta activa + historial antropométrico y sugiere ajustes con IA."""
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    pauta = db.query(models.Pauta).filter(
        models.Pauta.id == pauta_id,
        models.Pauta.patient_id == patient_id
    ).first()
    if not pauta:
        raise HTTPException(status_code=404, detail="Pauta no encontrada")

    # Obtener últimas 5 evaluaciones antropométricas
    evals = db.query(models.Anthropometric).filter(
        models.Anthropometric.patient_id == patient_id
    ).order_by(models.Anthropometric.date.desc()).limit(5).all()

    try:
        suggestions = await ai_service.suggest_adjustments(pauta, list(reversed(evals)))
    except AIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return {"suggestions": suggestions, "evals_count": len(evals)}


# ── PDF generation ──────────────────────────────────────────────────

def _generate_pauta_pdf(patient, pauta, nutritionist) -> bytes:
    from pdf_pauta import generate_pauta_pdf
    return generate_pauta_pdf(patient, pauta, nutritionist, _GRUPOS_MACROS)
