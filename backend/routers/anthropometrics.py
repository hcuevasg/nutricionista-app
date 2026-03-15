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
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib import colors
    from datetime import date as dt_date
    import math as _math

    # ── Palette ──────────────────────────────────────────────────────────────
    C_PRIMARY  = _hex("#4b7c60")
    C_PRIMARY2 = _hex("#3d6b50")
    C_TERRA    = _hex("#c06c52")
    C_SAGE     = _hex("#8da399")
    C_AMBER    = _hex("#d9a441")
    C_BG       = _hex("#F7F5F2")
    C_BGCARD   = _hex("#f0f4f1")
    C_BORDER   = _hex("#E5EAE7")
    C_MUTED    = _hex("#6b7280")
    C_DARK     = _hex("#1f2937")
    WHITE      = colors.white
    LIGHT_GREEN = _hex("#d1fae5")

    PAGE_W = A4[0] - 4*cm   # usable width (2cm margin each side)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    base = getSampleStyleSheet()
    def S(name, **kw): return ParagraphStyle(name, parent=base["Normal"], **kw)

    def fmt(v, d=1): return f"{float(v):.{d}f}" if v is not None else "—"

    # ── Header band ──────────────────────────────────────────────────────────
    prof_name = nutritionist.name or nutritionist.username
    hdr = Table([[
        Table([[Paragraph("NutriApp", S("HN", fontSize=22, textColor=WHITE, fontName="Helvetica-Bold", leading=26))],
               [Paragraph("Informe Antropométrico", S("HS", fontSize=9, textColor=LIGHT_GREEN, leading=12))]]),
        Paragraph(
            f"<b>{patient.name}</b><br/>"
            f"Evaluación: {ev.date}<br/>"
            f"Dr/a. {prof_name}",
            S("HR", fontSize=9, textColor=LIGHT_GREEN, alignment=TA_RIGHT, leading=14)
        ),
    ]], colWidths=[PAGE_W * 0.55, PAGE_W * 0.45])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_PRIMARY),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",(0,0), (-1,-1), 16),
        ("RIGHTPADDING",(0,0),(-1,-1), 16),
        ("TOPPADDING", (0,0), (-1,-1), 14),
        ("BOTTOMPADDING",(0,0),(-1,-1),14),
    ]))

    # ── Patient hero strip ───────────────────────────────────────────────────
    sex_label = "Masculino" if patient.sex == "M" else "Femenino"
    isak_badge_color = C_PRIMARY if ev.isak_level == "ISAK 2" else C_SAGE
    hero = Table([[
        Paragraph(
            f"<b>{patient.name}</b>  ·  {sex_label}",
            S("PN", fontSize=13, textColor=C_DARK, fontName="Helvetica-Bold", leading=16)
        ),
        Paragraph(
            f"<b>{ev.isak_level}</b>",
            S("PB", fontSize=9, textColor=WHITE, fontName="Helvetica-Bold",
              alignment=TA_CENTER, leading=12)
        ),
    ]], colWidths=[PAGE_W * 0.80, PAGE_W * 0.20])
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), C_BGCARD),
        ("BACKGROUND", (1,0), (1,0), isak_badge_color),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",(0,0), (-1,-1), 12),
        ("RIGHTPADDING",(0,0),(-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("GRID", (0,0), (-1,-1), 0, C_BG),
    ]))

    # ── Metric cards helper ──────────────────────────────────────────────────
    def metric_card(big_value, unit, label, accent=C_PRIMARY, note=""):
        inner = Table([
            [Paragraph(label.upper(), S("ML", fontSize=7, textColor=C_MUTED, fontName="Helvetica-Bold",
                                        leading=10, spaceBefore=2))],
            [Table([[
                Paragraph(big_value, S("MV", fontSize=26, textColor=C_DARK, fontName="Helvetica-Bold",
                                       leading=28)),
                Paragraph(unit, S("MU", fontSize=10, textColor=C_MUTED, leading=28)),
            ]], colWidths=[None, 1.2*cm])],
            [Paragraph(note, S("MN", fontSize=7, textColor=C_MUTED, leading=10, spaceAfter=2))
             if note else Spacer(1, 4)],
        ])
        inner.setStyle(TableStyle([
            ("VALIGN",  (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING",(0,0),(-1,-1), 0),
            ("TOPPADDING",  (0,0), (-1,-1), 2),
            ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ]))
        card = Table([[inner]], colWidths=[None])
        card.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,-1), WHITE),
            ("LINEBEFORE",  (0,0), (0,-1),  4, accent),
            ("LINEBELOW",   (0,-1),(-1,-1), 0.3, C_BORDER),
            ("LINEABOVE",   (0,0), (-1,0),  0.3, C_BORDER),
            ("LINEAFTER",   (-1,0),(-1,-1), 0.3, C_BORDER),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING",(0,0), (-1,-1), 8),
            ("TOPPADDING",  (0,0), (-1,-1), 8),
            ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ]))
        return card

    # ── Progress bar helper ──────────────────────────────────────────────────
    def progress_bar(label, pct, fill_color, total_w=PAGE_W):
        if pct is None or pct <= 0:
            return None
        pct_clamped = min(float(pct), 100.0)
        filled_w = total_w * 0.60 * (pct_clamped / 100.0)
        empty_w  = total_w * 0.60 - filled_w
        bar = Table([[
            Table([[""]], colWidths=[filled_w]),
            Table([[""]], colWidths=[empty_w]),
        ]], colWidths=[filled_w, empty_w], rowHeights=[8])
        bar.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,0), fill_color),
            ("BACKGROUND", (1,0), (1,0), C_BORDER),
            ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
            ("TOPPADDING", (0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
        ]))
        row = Table([[
            Paragraph(label, S("BL", fontSize=8, textColor=C_DARK, leading=10)),
            bar,
            Paragraph(f"{pct_clamped:.1f}%", S("BP", fontSize=8, textColor=fill_color,
                                                 fontName="Helvetica-Bold", alignment=TA_RIGHT, leading=10)),
        ]], colWidths=[PAGE_W * 0.25, PAGE_W * 0.60, PAGE_W * 0.15])
        row.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
            ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ]))
        return row

    # ── Styled data table helper ─────────────────────────────────────────────
    def data_table(headers, rows, col_widths=None, highlight_rows=None):
        S_TH  = S("TH2", fontSize=8,  textColor=WHITE,    fontName="Helvetica-Bold",
                  alignment=TA_CENTER, leading=11)
        S_THL = S("THL2",fontSize=8,  textColor=WHITE,    fontName="Helvetica-Bold",
                  alignment=TA_LEFT,  leading=11)
        S_TD  = S("TD2", fontSize=9,  textColor=C_DARK,   alignment=TA_CENTER, leading=13)
        S_TDL = S("TDL2",fontSize=9,  textColor=C_DARK,   alignment=TA_LEFT,   leading=13)
        S_TDH = S("TDH2",fontSize=9,  textColor=C_PRIMARY,fontName="Helvetica-Bold",
                  alignment=TA_CENTER,leading=13)

        header_row = [Paragraph(headers[0], S_THL)] + [Paragraph(h, S_TH) for h in headers[1:]]
        data = [header_row]
        for i, row in enumerate(rows):
            hl = highlight_rows and i in highlight_rows
            data.append([
                Paragraph(str(c), (S_TDH if hl else S_TDL) if j == 0 else (S_TDH if hl else S_TD))
                for j, c in enumerate(row)
            ])

        t = Table(data, colWidths=col_widths)
        row_bgs = [WHITE, C_BG]
        style_cmds = [
            ("BACKGROUND",    (0,0),  (-1,0),  C_PRIMARY),
            ("ROWBACKGROUNDS",(0,1),  (-1,-1), row_bgs),
            ("GRID",          (0,0),  (-1,-1), 0.3, C_BORDER),
            ("LEFTPADDING",   (0,0),  (-1,-1), 8),
            ("RIGHTPADDING",  (0,0),  (-1,-1), 8),
            ("TOPPADDING",    (0,0),  (-1,-1), 5),
            ("BOTTOMPADDING", (0,0),  (-1,-1), 5),
            ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
            ("ROUNDEDCORNERS",(0,0),  (-1,-1), 4),
        ]
        if highlight_rows:
            for ri in highlight_rows:
                style_cmds.append(("BACKGROUND", (0, ri+1), (-1, ri+1), _hex("#edf7f1")))
        t.setStyle(TableStyle(style_cmds))
        return t

    # ── Section label ────────────────────────────────────────────────────────
    def section_label(text, color=C_PRIMARY):
        bar = Table([[
            Table([[""]], colWidths=[3], rowHeights=[16]),
            Paragraph(text, S("SL", fontSize=10, textColor=color, fontName="Helvetica-Bold",
                               leading=14, spaceBefore=0)),
        ]], colWidths=[3, None])
        bar.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (0,0), color),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",   (0,0), (-1,-1), 0),
            ("RIGHTPADDING",  (0,0), (-1,-1), 0),
            ("TOPPADDING",    (1,0), (1,0), 0),
            ("BOTTOMPADDING", (1,0), (1,0), 0),
            ("LEFTPADDING",   (1,0), (1,0), 8),
            ("BACKGROUND",    (1,0), (1,0), C_BGCARD),
            ("TOPPADDING",    (0,0), (0,0), 0),
            ("BOTTOMPADDING", (0,0), (0,0), 0),
        ]))
        return bar

    story = []

    # ── 1. Header + hero ────────────────────────────────────────────────────
    story.append(hdr)
    story.append(Spacer(1, 0.25*cm))
    story.append(hero)
    story.append(Spacer(1, 0.5*cm))

    # ── 2. Key metric cards (2x2 grid) ──────────────────────────────────────
    bmi_val = None
    if ev.weight_kg and ev.height_cm:
        bmi_val = ev.weight_kg / ((ev.height_cm / 100) ** 2)
    bmi_note = ""
    if bmi_val is not None:
        if bmi_val < 18.5:  bmi_note = "Bajo peso"
        elif bmi_val < 25:  bmi_note = "Peso normal"
        elif bmi_val < 30:  bmi_note = "Sobrepeso"
        else:               bmi_note = "Obesidad"

    sigma4_vals = [ev.biceps_mm, ev.triceps_mm, ev.subscapular_mm, ev.iliac_crest_mm]
    sigma4_sum = sum(float(v) for v in sigma4_vals) if all(v is not None for v in sigma4_vals) else None

    cards_row1 = Table([[
        metric_card(fmt(ev.weight_kg), "kg",   "Peso corporal",    C_PRIMARY),
        Spacer(0.3*cm, 1),
        metric_card(fmt(bmi_val) if bmi_val else "—", "IMC", "Índice de masa corporal", C_TERRA, bmi_note),
        Spacer(0.3*cm, 1),
        metric_card(fmt(ev.fat_mass_pct) if ev.fat_mass_pct else "—", "%", "Masa grasa", C_AMBER),
        Spacer(0.3*cm, 1),
        metric_card(fmt(ev.lean_mass_kg) if ev.lean_mass_kg else "—", "kg", "Masa magra", C_SAGE),
    ]], colWidths=[
        PAGE_W*0.245, 0.02*PAGE_W,
        PAGE_W*0.245, 0.02*PAGE_W,
        PAGE_W*0.245, 0.02*PAGE_W,
        PAGE_W*0.245,
    ])
    cards_row1.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
    ]))
    story.append(cards_row1)
    story.append(Spacer(1, 0.5*cm))

    # ── 3. Body composition bars ─────────────────────────────────────────────
    bars = []
    lean_pct = None
    if ev.lean_mass_kg and ev.weight_kg and float(ev.weight_kg) > 0:
        lean_pct = float(ev.lean_mass_kg) / float(ev.weight_kg) * 100
    b1 = progress_bar("Masa magra",  lean_pct,         C_PRIMARY)
    b2 = progress_bar("Masa grasa",  ev.fat_mass_pct,  C_TERRA)
    if b1 or b2:
        story.append(section_label("Composición Corporal"))
        story.append(Spacer(1, 0.2*cm))
        comp_inner = []
        if b1: comp_inner.append(b1)
        if b2: comp_inner.append(b2)

        # detail row: Σ4, densidad, cintura
        detail_items = []
        if sigma4_sum is not None:
            detail_items.append(("Σ4 pliegues D&W", f"{sigma4_sum:.1f} mm"))
        if ev.body_density is not None:
            detail_items.append(("Densidad corporal", f"{fmt(ev.body_density, 4)} g/mL"))
        if ev.waist_cm is not None:
            detail_items.append(("Circ. cintura", f"{fmt(ev.waist_cm)} cm"))
        if ev.sum_6_skinfolds is not None:
            detail_items.append(("Σ6 pliegues", f"{fmt(ev.sum_6_skinfolds)} mm"))

        comp_block = [
            Table([[b] for b in comp_inner],
                  style=TableStyle([
                      ("BACKGROUND",(0,0),(-1,-1),WHITE),
                      ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
                      ("TOPPADDING",(0,0),(-1,-1),4),  ("BOTTOMPADDING",(0,0),(-1,-1),4),
                      ("GRID",(0,0),(-1,-1),0,WHITE),
                  ])),
        ]
        if detail_items:
            d_cols = min(4, len(detail_items))
            d_data = [[
                Table([[
                    Paragraph(k, S("DK", fontSize=7, textColor=C_MUTED, leading=10)),
                    Paragraph(v, S("DV", fontSize=10, textColor=C_DARK, fontName="Helvetica-Bold",
                                   leading=13)),
                ]], style=TableStyle([
                    ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                    ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
                    ("GRID",(0,0),(-1,-1),0,WHITE),
                ]))
                for k, v in detail_items
            ]]
            d_widths = [PAGE_W / d_cols] * d_cols
            d_table = Table(d_data, colWidths=d_widths)
            d_table.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1),C_BGCARD),
                ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
                ("TOPPADDING",(0,0),(-1,-1),8),  ("BOTTOMPADDING",(0,0),(-1,-1),8),
                ("LINEABOVE",(0,0),(-1,0),0.3,C_BORDER),
                ("GRID",(0,0),(-1,-1),0,WHITE),
            ]))
            comp_block.append(d_table)

        comp_outer = Table([[b] for b in comp_block])
        comp_outer.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),WHITE),
            ("BOX",(0,0),(-1,-1),0.3,C_BORDER),
            ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
            ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
        ]))
        story.append(comp_outer)
        story.append(Spacer(1, 0.5*cm))

    # ── 4. Pliegues cutáneos ─────────────────────────────────────────────────
    skinfolds = [
        ("Tríceps", ev.triceps_mm),       ("Subescapular", ev.subscapular_mm),
        ("Bíceps", ev.biceps_mm),         ("Cresta iliaca", ev.iliac_crest_mm),
        ("Supraespinal", ev.supraspinal_mm), ("Abdominal", ev.abdominal_mm),
        ("Muslo medial", ev.medial_thigh_mm), ("Pantorrilla máx.", ev.max_calf_mm),
    ]
    if ev.isak_level == "ISAK 2":
        skinfolds += [
            ("Pectoral", ev.pectoral_mm),
            ("Axilar medio", ev.axillary_mm),
            ("Muslo anterior", ev.front_thigh_mm),
        ]
    sf_rows = [(n, f"{fmt(v)} mm") for n, v in skinfolds if v is not None]
    if sf_rows:
        # 2-column layout for skinfolds
        mid = (len(sf_rows) + 1) // 2
        left_sf, right_sf = sf_rows[:mid], sf_rows[mid:]
        while len(right_sf) < len(left_sf):
            right_sf.append(("", ""))

        combined = [
            [l[0], l[1], r[0], r[1]]
            for l, r in zip(left_sf, right_sf)
        ]
        sf_table = Table(
            [[Paragraph("Pliegue", S("TH3", fontSize=8, textColor=WHITE, fontName="Helvetica-Bold", leading=11)),
              Paragraph("mm",      S("TH3C",fontSize=8, textColor=WHITE, fontName="Helvetica-Bold",
                                     alignment=TA_CENTER, leading=11)),
              Paragraph("Pliegue", S("TH3", fontSize=8, textColor=WHITE, fontName="Helvetica-Bold", leading=11)),
              Paragraph("mm",      S("TH3C",fontSize=8, textColor=WHITE, fontName="Helvetica-Bold",
                                     alignment=TA_CENTER, leading=11))]] +
            [[Paragraph(r[0], S("TD3", fontSize=9, textColor=C_DARK, leading=13)),
              Paragraph(r[1], S("TD3C",fontSize=9, textColor=C_PRIMARY, fontName="Helvetica-Bold",
                                alignment=TA_CENTER, leading=13)),
              Paragraph(r[2], S("TD3", fontSize=9, textColor=C_DARK, leading=13)),
              Paragraph(r[3], S("TD3C",fontSize=9, textColor=C_PRIMARY, fontName="Helvetica-Bold",
                                alignment=TA_CENTER, leading=13))] for r in combined],
            colWidths=[PAGE_W*0.37, PAGE_W*0.13, PAGE_W*0.37, PAGE_W*0.13],
        )
        sf_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),  (-1,0),  C_PRIMARY),
            ("ROWBACKGROUNDS",(0,1),  (-1,-1), [WHITE, C_BG]),
            ("GRID",          (0,0),  (-1,-1), 0.3, C_BORDER),
            ("LEFTPADDING",   (0,0),  (-1,-1), 8),
            ("RIGHTPADDING",  (0,0),  (-1,-1), 8),
            ("TOPPADDING",    (0,0),  (-1,-1), 5),
            ("BOTTOMPADDING", (0,0),  (-1,-1), 5),
            ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
        ]))
        story.append(KeepTogether([
            section_label("Pliegues Cutáneos (mm)"),
            Spacer(1, 0.2*cm),
            sf_table,
            Spacer(1, 0.5*cm),
        ]))

    # ── 5. Perímetros ────────────────────────────────────────────────────────
    perims = [
        ("Brazo relajado", ev.arm_relaxed_cm),   ("Brazo contraído", ev.arm_contracted_cm),
        ("Cadera/glúteo",  ev.hip_glute_cm),      ("Muslo máximo",    ev.thigh_max_cm),
        ("Muslo medio",    ev.thigh_mid_cm),       ("Pantorrilla",      ev.calf_cm),
    ]
    if ev.isak_level == "ISAK 2":
        perims += [("Cuello", ev.neck_cm), ("Tórax", ev.chest_cm), ("Tobillo mínimo", ev.ankle_min_cm)]
    p_rows = [(n, f"{fmt(v)} cm") for n, v in perims if v is not None]
    if p_rows:
        mid = (len(p_rows) + 1) // 2
        lp, rp = p_rows[:mid], p_rows[mid:]
        while len(rp) < len(lp): rp.append(("", ""))
        combined_p = [[l[0], l[1], r[0], r[1]] for l, r in zip(lp, rp)]
        p_table = Table(
            [[Paragraph("Perímetro", S("TH4", fontSize=8, textColor=WHITE, fontName="Helvetica-Bold", leading=11)),
              Paragraph("cm",        S("TH4C",fontSize=8, textColor=WHITE, fontName="Helvetica-Bold",
                                       alignment=TA_CENTER, leading=11)),
              Paragraph("Perímetro", S("TH4", fontSize=8, textColor=WHITE, fontName="Helvetica-Bold", leading=11)),
              Paragraph("cm",        S("TH4C",fontSize=8, textColor=WHITE, fontName="Helvetica-Bold",
                                       alignment=TA_CENTER, leading=11))]] +
            [[Paragraph(r[0], S("TD4", fontSize=9, textColor=C_DARK, leading=13)),
              Paragraph(r[1], S("TD4C",fontSize=9, textColor=C_SAGE, fontName="Helvetica-Bold",
                                alignment=TA_CENTER, leading=13)),
              Paragraph(r[2], S("TD4", fontSize=9, textColor=C_DARK, leading=13)),
              Paragraph(r[3], S("TD4C",fontSize=9, textColor=C_SAGE, fontName="Helvetica-Bold",
                                alignment=TA_CENTER, leading=13))] for r in combined_p],
            colWidths=[PAGE_W*0.37, PAGE_W*0.13, PAGE_W*0.37, PAGE_W*0.13],
        )
        p_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), C_SAGE),
            ("ROWBACKGROUNDS",(0,1), (-1,-1),[WHITE, C_BG]),
            ("GRID",          (0,0), (-1,-1), 0.3, C_BORDER),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("RIGHTPADDING",  (0,0), (-1,-1), 8),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(KeepTogether([
            section_label("Perímetros (cm)", C_SAGE),
            Spacer(1, 0.2*cm),
            p_table,
            Spacer(1, 0.5*cm),
        ]))

    # ── 6. Índices antropométricos ───────────────────────────────────────────
    def _idx(a, b, mult=1, decimals=2):
        if a is None or b is None or b == 0: return "—"
        return f"{(float(a) / float(b) * mult):.{decimals}f}"

    idx_basic = []
    if ev.waist_cm and ev.hip_glute_cm:
        idx_basic.append(["Cociente Cintura-Cadera", _idx(ev.waist_cm, ev.hip_glute_cm)])
    if ev.fat_mass_kg and ev.lean_mass_kg:
        idx_basic.append(["Cociente Adiposo-Muscular", _idx(ev.fat_mass_kg, ev.lean_mass_kg, decimals=3)])
    if ev.waist_cm and ev.weight_kg and ev.height_cm:
        h_m = ev.height_cm / 100
        denom = 0.109 * _math.sqrt(ev.weight_kg / h_m)
        if denom > 0:
            idx_basic.append(["Índice de Conicidad", f"{ev.waist_cm / denom:.3f}"])
    if idx_basic:
        story.append(KeepTogether([
            section_label("Índices Antropométricos", C_TERRA),
            Spacer(1, 0.2*cm),
            data_table(["Índice", "Valor"], idx_basic, [PAGE_W*0.70, PAGE_W*0.30]),
            Spacer(1, 0.5*cm),
        ]))

    # ── 7. Índices ISAK 2 ────────────────────────────────────────────────────
    if ev.isak_level == "ISAK 2":
        idx2 = []
        if ev.height_cm and ev.humerus_width_cm and ev.femur_width_cm:
            val = (ev.height_cm/100) * (ev.humerus_width_cm/100) * (ev.femur_width_cm/100) * 400
            bone_mass = 3.02 * (val ** 0.712)
            idx2.append(["Masa Ósea (Martin 1990)",    f"{bone_mass:.2f} kg"])
            if ev.lean_mass_kg:
                idx2.append(["Índice Músculo Óseo (IMO)", f"{ev.lean_mass_kg / bone_mass:.2f}"])
        if ev.acromion_radial_cm and ev.radial_styloid_cm and ev.height_cm:
            idx2.append(["I.R.E.S. Superior", f"{(ev.acromion_radial_cm + ev.radial_styloid_cm) / ev.height_cm * 100:.2f}"])
        if ev.iliospinal_height_cm and ev.height_cm:
            idx2.append(["I.R.E.S. Inferior", f"{ev.iliospinal_height_cm / ev.height_cm * 100:.2f}"])
        if ev.acromion_radial_cm and ev.radial_styloid_cm and ev.iliospinal_height_cm:
            idx2.append(["Índice Intermembral", f"{(ev.acromion_radial_cm + ev.radial_styloid_cm) / ev.iliospinal_height_cm * 100:.2f}"])
        if ev.radial_styloid_cm and ev.acromion_radial_cm:
            idx2.append(["Índice Braquial", _idx(ev.radial_styloid_cm, ev.acromion_radial_cm, 100)])
        if hasattr(ev, 'tibiale_height_cm') and ev.tibiale_height_cm and ev.trochanter_tibial_cm:
            idx2.append(["Índice Crural", _idx(ev.tibiale_height_cm, ev.trochanter_tibial_cm, 100)])
        if ev.iliospinal_height_cm and ev.height_cm:
            trunk = ev.height_cm - ev.iliospinal_height_cm
            if trunk > 0:
                idx2.append(["Índice Córmico",               f"{trunk / ev.height_cm * 100:.2f}"])
                idx2.append(["Índice Esquelético (Manouvrier)", f"{ev.iliospinal_height_cm / trunk * 100:.2f}"])
        if ev.biacromial_cm and ev.biiliocrestal_cm:
            idx2.append(["Índice Acromio-Ilíaco", _idx(ev.biacromial_cm, ev.biiliocrestal_cm, 100)])
        if hasattr(ev, 'arm_span_cm') and ev.arm_span_cm and ev.height_cm:
            idx2.append(["Envergadura Relativa", _idx(ev.arm_span_cm, ev.height_cm, 100)])
        if idx2:
            story.append(KeepTogether([
                section_label("Índices ISAK 2", C_TERRA),
                Spacer(1, 0.2*cm),
                data_table(["Índice", "Valor"], idx2, [PAGE_W*0.70, PAGE_W*0.30]),
                Spacer(1, 0.5*cm),
            ]))

    # ── 8. Somatotipo + Somatocarta ──────────────────────────────────────────
    if ev.isak_level == "ISAK 2" and ev.somatotype_endo is not None:
        soma_cards = Table([[
            metric_card(fmt(ev.somatotype_endo), "", "Endomorfia",  C_TERRA),
            Spacer(0.4*cm, 1),
            metric_card(fmt(ev.somatotype_meso), "", "Mesomorfia",  C_PRIMARY),
            Spacer(0.4*cm, 1),
            metric_card(fmt(ev.somatotype_ecto), "", "Ectomorfia",  C_SAGE),
        ]], colWidths=[
            PAGE_W*0.30, 0.05*PAGE_W,
            PAGE_W*0.30, 0.05*PAGE_W,
            PAGE_W*0.30,
        ])
        soma_cards.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
            ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
        ]))

        soma_img = _draw_somatocarta(
            [(ev.somatotype_endo, ev.somatotype_meso, ev.somatotype_ecto, ev.date)]
        )
        soma_elements = [
            section_label("Somatotipo — Heath & Carter (1990)", C_TERRA),
            Spacer(1, 0.25*cm),
            soma_cards,
            Spacer(1, 0.4*cm),
        ]
        if soma_img:
            from reportlab.platypus import Image as RLImage
            soma_elements.append(RLImage(soma_img, width=11*cm, height=9*cm))
        story.append(KeepTogether(soma_elements))
        story.append(Spacer(1, 0.5*cm))

    # ── 9. Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    footer = Table([[
        Paragraph(
            f"NutriApp  ·  Generado el {dt_date.today().strftime('%d/%m/%Y')}  ·  Dr/a. {prof_name}",
            S("FT", fontSize=7, textColor=WHITE, leading=10)
        ),
        Paragraph(
            "Documento de uso profesional y confidencial",
            S("FTR", fontSize=7, textColor=_hex("#a7f3d0"), alignment=TA_RIGHT, leading=10)
        ),
    ]], colWidths=[PAGE_W * 0.6, PAGE_W * 0.4])
    footer.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), C_PRIMARY2),
        ("LEFTPADDING",  (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING",   (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0), (-1,-1), 10),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(footer)

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
