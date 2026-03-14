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


@router.get("/{patient_id}/pdf/comparativo")
async def download_comparativo_pdf(
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

    evaluations = db.query(models.Anthropometric).filter(
        models.Anthropometric.patient_id == patient_id
    ).order_by(models.Anthropometric.created_at.asc()).all()

    if not evaluations:
        raise HTTPException(status_code=400, detail="No hay evaluaciones para este paciente")

    pdf_bytes = _generate_comparativo_pdf(patient, evaluations, current_user)
    filename = f"ISAK_Comparativo_{patient.name.replace(' ', '_')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
        story.append(Spacer(1, 0.4*cm))

        # Somatocarta
        soma_img = _draw_somatocarta(
            [(ev.somatotype_endo, ev.somatotype_meso, ev.somatotype_ecto, ev.date)]
        )
        if soma_img:
            from reportlab.platypus import Image as RLImage
            story.append(Paragraph("Somatocarta", S_SEC))
            story.append(RLImage(soma_img, width=12*cm, height=10*cm))

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


def _generate_comparativo_pdf(patient, evaluations, nutritionist) -> bytes:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)

    base = getSampleStyleSheet()
    def S(name, **kw): return ParagraphStyle(name, parent=base["Normal"], **kw)

    S_TH  = S("TH",  fontSize=7, textColor=WHITE,        fontName="Helvetica-Bold", alignment=TA_CENTER, leading=10)
    S_THL = S("THL", fontSize=7, textColor=WHITE,        fontName="Helvetica-Bold", alignment=TA_LEFT,   leading=10)
    S_LBL = S("LBL", fontSize=8, textColor=C_MUTED,      alignment=TA_LEFT,         leading=11)
    S_VAL = S("VAL", fontSize=8, textColor=colors.black, alignment=TA_CENTER,       leading=11)
    S_SEC = S("SEC", fontSize=10, textColor=C_PRIMARY,   fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3)
    S_SUB = S("SUB", fontSize=8, textColor=C_MUTED,      leading=12)

    def fmt(v, d=1): return f"{float(v):.{d}f}" if v is not None else "—"

    def delta(curr, prev, higher_is_better=True):
        if curr is None or prev is None:
            return ""
        diff = float(curr) - float(prev)
        if abs(diff) < 0.05:
            return ""
        sign = "▲" if diff > 0 else "▼"
        good = (diff > 0) == higher_is_better
        return f" {sign}{abs(diff):.1f}"

    n = len(evaluations)
    dates = [ev.date for ev in evaluations]

    # Column widths: label col + one col per evaluation
    label_w = 4.5 * cm
    page_w = landscape(A4)[0] - 3 * cm  # usable width
    data_w = min(3.2 * cm, (page_w - label_w) / n)
    col_widths = [label_w] + [data_w] * n

    story = []

    # Header
    hdr = Table([[
        Paragraph("NutriApp", S("H1", fontSize=18, textColor=WHITE, fontName="Helvetica-Bold")),
        Paragraph(
            f"Comparativo ISAK · {patient.name}<br/>"
            f"Generado: {dt_date.today().strftime('%d/%m/%Y')} · Profesional: {nutritionist.name or nutritionist.username}",
            S("H2", fontSize=8, textColor=_hex("#d1fae5"), alignment=1)
        ),
    ]])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),C_PRIMARY),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
        ("TOPPADDING",(0,0),(-1,-1),12),("BOTTOMPADDING",(0,0),(-1,-1),12),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(f"Historial completo: {n} evaluación{'es' if n != 1 else ''}", S_SUB))
    story.append(Spacer(1, 0.3*cm))

    def make_table(section_rows):
        header = [Paragraph("", S_THL)] + [Paragraph(d, S_TH) for d in dates]
        data = [header]
        for label, values in section_rows:
            data.append([Paragraph(label, S_LBL)] + [Paragraph(str(v), S_VAL) for v in values])

        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), C_PRIMARY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, C_BG]),
            ("GRID",(0,0),(-1,-1),0.3,C_BORDER),
            ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("BACKGROUND",(0,1),(0,-1),C_BG),
        ]))
        return t

    # ── Composición corporal ──────────────────────────────────────────────────
    story.append(KeepTogether([
        Paragraph("Composición Corporal", S_SEC),
        make_table([
            ("Peso (kg)",         [fmt(ev.weight_kg) for ev in evaluations]),
            ("Talla (cm)",        [fmt(ev.height_cm) for ev in evaluations]),
            ("IMC (kg/m²)",       [
                f"{ev.weight_kg / ((ev.height_cm/100)**2):.1f}" if ev.weight_kg and ev.height_cm else "—"
                for ev in evaluations
            ]),
            ("% Masa grasa",      [fmt(ev.fat_mass_pct) for ev in evaluations]),
            ("Masa grasa (kg)",   [fmt(ev.fat_mass_kg) for ev in evaluations]),
            ("Masa magra (kg)",   [fmt(ev.lean_mass_kg) for ev in evaluations]),
            ("Σ6 pliegues (mm)",  [fmt(ev.sum_6_skinfolds) for ev in evaluations]),
            ("Circ. cintura (cm)",[fmt(ev.waist_cm) for ev in evaluations]),
        ])
    ]))
    story.append(Spacer(1, 0.4*cm))

    # ── Pliegues cutáneos ─────────────────────────────────────────────────────
    story.append(KeepTogether([
        Paragraph("Pliegues Cutáneos (mm)", S_SEC),
        make_table([
            ("Tríceps",       [fmt(ev.triceps_mm) for ev in evaluations]),
            ("Subescapular",  [fmt(ev.subscapular_mm) for ev in evaluations]),
            ("Bíceps",        [fmt(ev.biceps_mm) for ev in evaluations]),
            ("Cresta iliaca", [fmt(ev.iliac_crest_mm) for ev in evaluations]),
            ("Supraespinal",  [fmt(ev.supraspinal_mm) for ev in evaluations]),
            ("Abdominal",     [fmt(ev.abdominal_mm) for ev in evaluations]),
            ("Muslo medial",  [fmt(ev.medial_thigh_mm) for ev in evaluations]),
            ("Pantorrilla",   [fmt(ev.max_calf_mm) for ev in evaluations]),
        ])
    ]))
    story.append(Spacer(1, 0.4*cm))

    # ── Perímetros ────────────────────────────────────────────────────────────
    story.append(KeepTogether([
        Paragraph("Perímetros (cm)", S_SEC),
        make_table([
            ("Brazo relajado",    [fmt(ev.arm_relaxed_cm) for ev in evaluations]),
            ("Brazo contraído",   [fmt(ev.arm_contracted_cm) for ev in evaluations]),
            ("Cadera/glúteo",     [fmt(ev.hip_glute_cm) for ev in evaluations]),
            ("Muslo máximo",      [fmt(ev.thigh_max_cm) for ev in evaluations]),
            ("Pantorrilla",       [fmt(ev.calf_cm) for ev in evaluations]),
        ])
    ]))
    story.append(Spacer(1, 0.4*cm))

    # ── Somatotipo (si hay datos ISAK 2) ─────────────────────────────────────
    has_soma = any(ev.somatotype_endo is not None for ev in evaluations)
    if has_soma:
        story.append(KeepTogether([
            Paragraph("Somatotipo — Heath & Carter (1990)", S_SEC),
            make_table([
                ("Endomorfia",  [fmt(ev.somatotype_endo) for ev in evaluations]),
                ("Mesomorfia",  [fmt(ev.somatotype_meso) for ev in evaluations]),
                ("Ectomorfia",  [fmt(ev.somatotype_ecto) for ev in evaluations]),
            ])
        ]))
        story.append(Spacer(1, 0.4*cm))

    # ── Variación entre primera y última ─────────────────────────────────────
    if n >= 2:
        first, last = evaluations[0], evaluations[-1]

        def chg(curr, prev, unit="", invert=False):
            if curr is None or prev is None:
                return "—"
            diff = float(curr) - float(prev)
            if abs(diff) < 0.01:
                return f"Sin cambio"
            sign = "+" if diff > 0 else ""
            good = (diff < 0) if invert else (diff > 0)
            return f"{sign}{diff:.1f}{unit}"

        story.append(KeepTogether([
            Paragraph(f"Variación: {first.date} → {last.date}", S_SEC),
            make_table([
                ("Peso",          [chg(last.weight_kg, first.weight_kg, " kg")]),
                ("% Masa grasa",  [chg(last.fat_mass_pct, first.fat_mass_pct, "%", invert=True)]),
                ("Masa grasa",    [chg(last.fat_mass_kg, first.fat_mass_kg, " kg", invert=True)]),
                ("Masa magra",    [chg(last.lean_mass_kg, first.lean_mass_kg, " kg")]),
                ("Σ6 pliegues",   [chg(last.sum_6_skinfolds, first.sum_6_skinfolds, " mm", invert=True)]),
            ])
        ]))

    # Footer
    story.append(Spacer(1, 0.8*cm))
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


def _draw_somatocarta(points: list) -> "io.BytesIO | None":
    """
    Draw a somatochart and return a BytesIO PNG.
    points: list of (endo, meso, ecto, label)
    Coordinates: X = ecto - endo, Y = 2*meso - (endo + ecto)
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np

        fig, ax = plt.subplots(figsize=(5, 4.2), dpi=120)
        ax.set_facecolor("#F7F5F2")
        fig.patch.set_facecolor("#F7F5F2")

        # Grid
        ax.axhline(0, color="#8da399", linewidth=0.8, linestyle="--")
        ax.axvline(0, color="#8da399", linewidth=0.8, linestyle="--")
        ax.grid(color="#E5EAE7", linewidth=0.5)

        # Region labels
        ax.text(-7.5,  0.3, "Endomorfo\nMesomorfo", fontsize=7, color="#6b7280", va="bottom")
        ax.text( 4.5,  0.3, "Ectomorfo\nMesomorfo", fontsize=7, color="#6b7280", va="bottom")
        ax.text(-7.5, -0.5, "Endomorfo\nEctomorfo",  fontsize=7, color="#6b7280", va="top")
        ax.text( 4.5, -0.5, "Ectomorfo\nMesomorfo",  fontsize=7, color="#6b7280", va="top")
        ax.text(-0.5,  7.5, "Mesomorfo",              fontsize=7, color="#6b7280", ha="center")

        # Plot points
        for endo, meso, ecto, label in points:
            x = float(ecto) - float(endo)
            y = 2 * float(meso) - (float(endo) + float(ecto))
            ax.scatter(x, y, s=80, color="#4b7c60", zorder=5, edgecolors="white", linewidths=1.5)
            ax.annotate(label, (x, y), textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=8, color="#3d6b50")

        ax.set_xlim(-8, 8)
        ax.set_ylim(-8, 8)
        ax.set_xlabel("← Endomorfo  |  Ectomorfo →", fontsize=8, color="#6b7280")
        ax.set_ylabel("← Ectomorfo  |  Mesomorfo →", fontsize=8, color="#6b7280")
        ax.set_title("Somatocarta — Heath & Carter (1990)", fontsize=9, color="#4b7c60", pad=8)
        ax.tick_params(labelsize=7)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception:
        return None
