"""Anthropometric evaluation routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io

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


@router.get("/{patient_id}/{eval_id}/pdf")
async def download_isak_pdf(
    patient_id: int,
    eval_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    ev = db.query(models.Anthropometric).filter(
        models.Anthropometric.id == eval_id,
        models.Anthropometric.patient_id == patient_id
    ).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    pdf_bytes = _generate_isak_pdf(patient, ev, current_user)
    filename = f"ISAK_{patient.name.replace(' ', '_')}_{ev.date}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _hex(h):
    from reportlab.lib.colors import HexColor
    return HexColor(h)


def _generate_isak_pdf(patient, ev, nutritionist) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib import colors
    from datetime import date as dt_date

    C_PRIMARY = _hex("#4b7c60")
    C_TERRA   = _hex("#c06c52")
    C_SAGE    = _hex("#8da399")
    C_BG      = _hex("#F7F5F2")
    C_BORDER  = _hex("#E5EAE7")
    C_MUTED   = _hex("#6b7280")
    WHITE     = colors.white

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    base = getSampleStyleSheet()
    def S(name, **kw): return ParagraphStyle(name, parent=base["Normal"], **kw)

    S_TH  = S("TH", fontSize=8,  textColor=WHITE,        fontName="Helvetica-Bold", alignment=TA_CENTER, leading=12)
    S_TD  = S("TD", fontSize=9,  textColor=colors.black, alignment=TA_CENTER, leading=13)
    S_TDL = S("TDL",fontSize=9,  textColor=colors.black, alignment=TA_LEFT,   leading=13)
    S_SEC = S("SEC",fontSize=11, textColor=C_PRIMARY,    fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=4, leading=16)
    S_SUB = S("SUB",fontSize=9,  textColor=C_MUTED,      leading=13)

    def fmt(v, d=1): return f"{float(v):.{d}f}" if v is not None else "—"

    def kv(rows, col1=5*cm):
        data = [[Paragraph(k, S("KL", fontSize=8, textColor=C_MUTED, leading=12)),
                 Paragraph(v, S_TD)] for k, v in rows]
        t = Table(data, colWidths=[col1, None])
        t.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0,0),(-1,-1), [WHITE, C_BG]),
            ("GRID", (0,0),(-1,-1), 0.3, C_BORDER),
            ("LEFTPADDING",(0,0),(-1,-1),6), ("RIGHTPADDING",(0,0),(-1,-1),6),
            ("TOPPADDING",(0,0),(-1,-1),5),  ("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("BACKGROUND",(0,0),(0,-1),C_BG),
        ]))
        return t

    def section_table(headers, rows, col_widths=None):
        header_row = [Paragraph(h, S_TH) for h in headers]
        data = [header_row] + [[Paragraph(str(c), S_TDL if i == 0 else S_TD) for i, c in enumerate(r)] for r in rows]
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), C_PRIMARY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,C_BG]),
            ("GRID",(0,0),(-1,-1),0.3,C_BORDER),
            ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
            ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ]))
        return t

    story = []

    # Header
    hdr = Table([[
        Paragraph("NutriApp", S("H1", fontSize=20, textColor=WHITE, fontName="Helvetica-Bold")),
        Paragraph(f"Generado: {dt_date.today().strftime('%d/%m/%Y')}<br/>Profesional: {nutritionist.name or nutritionist.username}",
                  S("H2", fontSize=8, textColor=_hex("#d1fae5"), alignment=1)),
    ]])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),C_PRIMARY),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
        ("TOPPADDING",(0,0),(-1,-1),14),("BOTTOMPADDING",(0,0),(-1,-1),14),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.4*cm))

    # Title
    story.append(Paragraph(f"Evaluación {ev.isak_level}", S("T", fontSize=18, textColor=C_PRIMARY, leading=22)))
    story.append(Paragraph(f"{patient.name}  ·  {ev.date}", S_SUB))
    story.append(Spacer(1, 0.4*cm))

    # Paciente + medidas básicas
    story.append(Paragraph("Datos del Paciente", S_SEC))
    story.append(kv([
        ("Nombre",   patient.name),
        ("Sexo",     "Masculino" if patient.sex == "M" else "Femenino"),
        ("Nivel ISAK", ev.isak_level),
        ("Fecha evaluación", ev.date),
    ]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Medidas Básicas", S_SEC))
    story.append(kv([
        ("Peso",     f"{fmt(ev.weight_kg)} kg"),
        ("Talla",    f"{fmt(ev.height_cm)} cm"),
        ("Circ. cintura", f"{fmt(ev.waist_cm)} cm"),
    ]))
    story.append(Spacer(1, 0.3*cm))

    # Resultados composición corporal
    story.append(Paragraph("Composición Corporal — Durnin & Womersley (1974)", S_SEC))
    cc_rows = [
        ["Σ4 pliegues D&W", "—" if ev.body_density is None else "calculado"],
        ["Densidad corporal", f"{fmt(ev.body_density, 4)} g/mL"],
        ["% Masa grasa", f"{fmt(ev.fat_mass_pct)} %"],
        ["Masa grasa", f"{fmt(ev.fat_mass_kg)} kg"],
        ["Masa magra", f"{fmt(ev.lean_mass_kg)} kg"],
    ]
    if ev.sum_6_skinfolds is not None:
        cc_rows.append(["Σ6 pliegues", f"{fmt(ev.sum_6_skinfolds)} mm"])
    if ev.weight_kg and ev.height_cm:
        bmi = ev.weight_kg / ((ev.height_cm / 100) ** 2)
        cc_rows.append(["IMC", f"{bmi:.1f} kg/m²"])
    story.append(section_table(["Indicador", "Valor"], cc_rows, [8*cm, None]))
    story.append(Spacer(1, 0.3*cm))

    # Pliegues cutáneos
    skinfolds = [
        ("Tríceps", ev.triceps_mm), ("Subescapular", ev.subscapular_mm),
        ("Bíceps", ev.biceps_mm),   ("Cresta iliaca", ev.iliac_crest_mm),
        ("Supraespinal", ev.supraspinal_mm), ("Abdominal", ev.abdominal_mm),
        ("Muslo medial", ev.medial_thigh_mm), ("Pantorrilla máx.", ev.max_calf_mm),
    ]
    if ev.isak_level == "ISAK 2":
        skinfolds += [("Pectoral", ev.pectoral_mm), ("Axilar medio", ev.axillary_mm),
                      ("Muslo anterior", ev.front_thigh_mm)]
    sf_rows = [(n, f"{fmt(v)} mm") for n, v in skinfolds if v is not None]
    if sf_rows:
        story.append(Paragraph("Pliegues Cutáneos (mm)", S_SEC))
        story.append(section_table(["Pliegue", "Valor"], sf_rows, [8*cm, None]))
        story.append(Spacer(1, 0.3*cm))

    # Perímetros
    perims = [
        ("Brazo relajado", ev.arm_relaxed_cm), ("Brazo contraído", ev.arm_contracted_cm),
        ("Cadera", ev.hip_glute_cm), ("Muslo máximo", ev.thigh_max_cm),
        ("Muslo medio", ev.thigh_mid_cm), ("Pantorrilla", ev.calf_cm),
    ]
    if ev.isak_level == "ISAK 2":
        perims += [("Cuello", ev.neck_cm), ("Tórax", ev.chest_cm),
                   ("Tobillo mínimo", ev.ankle_min_cm)]
    p_rows = [(n, f"{fmt(v)} cm") for n, v in perims if v is not None]
    if p_rows:
        story.append(Paragraph("Perímetros (cm)", S_SEC))
        story.append(section_table(["Perímetro", "Valor"], p_rows, [8*cm, None]))
        story.append(Spacer(1, 0.3*cm))

    # Somatotipo ISAK 2
    if ev.isak_level == "ISAK 2" and ev.somatotype_endo is not None:
        story.append(Paragraph("Somatotipo — Heath & Carter (1990)", S_SEC))
        soma_rows = [
            ["Endomorfia", f"{fmt(ev.somatotype_endo)}"],
            ["Mesomorfia", f"{fmt(ev.somatotype_meso)}"],
            ["Ectomorfia", f"{fmt(ev.somatotype_ecto)}"],
        ]
        story.append(section_table(["Componente", "Valor"], soma_rows, [8*cm, None]))

    # Footer
    story.append(Spacer(1, 1*cm))
    ft = Table([[
        Paragraph(f"NutriApp — {dt_date.today().strftime('%d/%m/%Y')}",
                  S("F", fontSize=7, textColor=C_MUTED)),
        Paragraph("Documento profesional y confidencial.",
                  S("FR", fontSize=7, textColor=C_MUTED, alignment=1)),
    ]])
    ft.setStyle(TableStyle([("LINEABOVE",(0,0),(-1,0),0.5,C_BORDER),("TOPPADDING",(0,0),(-1,-1),8)]))
    story.append(ft)

    doc.build(story)
    return buf.getvalue()
