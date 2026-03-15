"""Meal plan routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io

import models
import schemas
import auth
from database import get_db


def _hex(h: str):
    from reportlab.lib.colors import HexColor
    return HexColor(h)


def _generate_meal_plan_pdf(patient, plan, nutritionist) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib import colors
    from datetime import date as dt_date

    C_PRIMARY = _hex("#4b7c60")
    C_TERRA   = _hex("#c06c52")
    C_BG      = _hex("#F7F5F2")
    C_BORDER  = _hex("#E5EAE7")
    C_MUTED   = _hex("#6b7280")
    WHITE     = colors.white

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    base = getSampleStyleSheet()
    def S(name, **kw): return ParagraphStyle(name, parent=base["Normal"], **kw)

    S_TH  = S("TH",  fontSize=8,  textColor=WHITE,        fontName="Helvetica-Bold", alignment=TA_CENTER, leading=12)
    S_THL = S("THL", fontSize=8,  textColor=WHITE,        fontName="Helvetica-Bold", alignment=TA_LEFT,   leading=12)
    S_TD  = S("TD",  fontSize=9,  textColor=colors.black, alignment=TA_CENTER, leading=13)
    S_TDL = S("TDL", fontSize=9,  textColor=colors.black, alignment=TA_LEFT,   leading=13)
    S_TDR = S("TDR", fontSize=9,  textColor=colors.black, alignment=TA_RIGHT,  leading=13)
    S_SEC = S("SEC", fontSize=11, textColor=C_PRIMARY,    fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4, leading=16)
    S_SUB = S("SUB", fontSize=9,  textColor=C_MUTED,      leading=13)

    def fmt(v, d=0):
        try: return f"{float(v):.{d}f}"
        except: return "—"

    story = []

    # Header
    hdr = Table([[
        Paragraph("NutriApp", S("H1", fontSize=20, textColor=WHITE, fontName="Helvetica-Bold")),
        Paragraph(
            f"Generado: {dt_date.today().strftime('%d/%m/%Y')}<br/>Profesional: {nutritionist.name or nutritionist.username}",
            S("H2", fontSize=8, textColor=_hex("#d1fae5"), alignment=TA_RIGHT)
        ),
    ]])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_PRIMARY),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 12), ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 14),  ("BOTTOMPADDING", (0,0), (-1,-1), 14),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.4*cm))

    # Title
    story.append(Paragraph("Plan Alimenticio", S("T", fontSize=18, textColor=C_PRIMARY, leading=22, fontName="Helvetica-Bold")))
    story.append(Paragraph(f"{patient.name}  ·  {plan.date}", S_SUB))
    story.append(Spacer(1, 0.3*cm))

    # Plan metadata
    meta_rows = [("Nombre del plan", plan.name)]
    if plan.goal:    meta_rows.append(("Objetivo", plan.goal))
    if plan.calories: meta_rows.append(("Calorías totales", f"{fmt(plan.calories)} kcal"))
    if plan.protein_g: meta_rows.append(("Proteínas", f"{fmt(plan.protein_g, 1)} g"))
    if plan.carbs_g:   meta_rows.append(("Carbohidratos", f"{fmt(plan.carbs_g, 1)} g"))
    if plan.fat_g:     meta_rows.append(("Grasas", f"{fmt(plan.fat_g, 1)} g"))

    meta_data = [[Paragraph(k, S("KL", fontSize=8, textColor=C_MUTED, leading=12)),
                  Paragraph(v, S_TDL)] for k, v in meta_rows]
    meta_t = Table(meta_data, colWidths=[5*cm, None])
    meta_t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, C_BG]),
        ("GRID", (0,0), (-1,-1), 0.3, C_BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),  ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("BACKGROUND", (0,0), (0,-1), C_BG),
    ]))
    story.append(meta_t)
    story.append(Spacer(1, 0.4*cm))

    # Items grouped by meal type
    MEAL_ORDER = ['Desayuno', 'Media mañana', 'Almuerzo', 'Merienda', 'Cena', 'Colación']
    items = sorted(plan.items or [], key=lambda x: MEAL_ORDER.index(x.meal_type) if x.meal_type in MEAL_ORDER else 99)

    # Group
    from itertools import groupby
    for meal_type, group_items in groupby(items, key=lambda x: x.meal_type):
        group_list = list(group_items)
        header = [Paragraph(h, S_TH if i > 0 else S_THL) for i, h in
                  enumerate(["Alimento", "Cant.", "Unidad", "Kcal", "Prot.", "Carb.", "Gras."])]
        rows = [header]
        for it in group_list:
            rows.append([
                Paragraph(it.food_name or "—", S_TDL),
                Paragraph(fmt(it.quantity, 1) if it.quantity else "—", S_TD),
                Paragraph(it.unit or "—", S_TD),
                Paragraph(fmt(it.calories, 0) if it.calories else "—", S_TD),
                Paragraph(fmt(it.protein_g, 1) if it.protein_g else "—", S_TD),
                Paragraph(fmt(it.carbs_g, 1) if it.carbs_g else "—", S_TD),
                Paragraph(fmt(it.fat_g, 1) if it.fat_g else "—", S_TD),
            ])

        t = Table(rows, colWidths=[6.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), C_PRIMARY),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, C_BG]),
            ("GRID", (0,0), (-1,-1), 0.3, C_BORDER),
            ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING", (0,0), (-1,-1), 5),  ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))

        block = [Paragraph(meal_type, S_SEC), t, Spacer(1, 0.25*cm)]
        story.append(KeepTogether(block))

    # Notes
    if plan.notes:
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("Observaciones", S_SEC))
        story.append(Paragraph(plan.notes, S("NOTE", fontSize=9, textColor=colors.black, leading=14, leftIndent=4)))

    doc.build(story)
    buf.seek(0)
    return buf.read()

router = APIRouter(prefix="/meal-plans", tags=["meal_plans"])


@router.post("", response_model=schemas.MealPlanResponse)
async def create_meal_plan(
    patient_id: int,
    request: schemas.MealPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Create meal plan for patient."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Create plan
    meal_plan = models.MealPlan(
        patient_id=patient_id,
        name=request.name,
        date=request.date,
        goal=request.goal,
        calories=request.calories,
        protein_g=request.protein_g,
        carbs_g=request.carbs_g,
        fat_g=request.fat_g,
        notes=request.notes
    )
    db.add(meal_plan)
    db.flush()

    # Add items
    for item in request.items:
        meal_item = models.MealItem(
            plan_id=meal_plan.id,
            **item.model_dump()
        )
        db.add(meal_item)

    db.commit()
    db.refresh(meal_plan)
    return meal_plan


@router.get("/{patient_id}", response_model=List[schemas.MealPlanResponse])
async def list_meal_plans(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """List all meal plans for patient."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meal_plans = db.query(models.MealPlan).filter(
        models.MealPlan.patient_id == patient_id
    ).order_by(models.MealPlan.created_at.desc()).all()

    return meal_plans


@router.get("/{patient_id}/{plan_id}", response_model=schemas.MealPlanResponse)
async def get_meal_plan(
    patient_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Get specific meal plan."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meal_plan = db.query(models.MealPlan).filter(
        models.MealPlan.id == plan_id,
        models.MealPlan.patient_id == patient_id
    ).first()

    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    return meal_plan


@router.put("/{patient_id}/{plan_id}", response_model=schemas.MealPlanResponse)
async def update_meal_plan(
    patient_id: int,
    plan_id: int,
    request: schemas.MealPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Update meal plan."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meal_plan = db.query(models.MealPlan).filter(
        models.MealPlan.id == plan_id,
        models.MealPlan.patient_id == patient_id
    ).first()

    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    # Update fields
    meal_plan.name = request.name
    meal_plan.date = request.date
    meal_plan.goal = request.goal
    meal_plan.calories = request.calories
    meal_plan.protein_g = request.protein_g
    meal_plan.carbs_g = request.carbs_g
    meal_plan.fat_g = request.fat_g
    meal_plan.notes = request.notes

    # Delete old items
    db.query(models.MealItem).filter(models.MealItem.plan_id == plan_id).delete()

    # Add new items
    for item in request.items:
        meal_item = models.MealItem(
            plan_id=plan_id,
            **item.model_dump()
        )
        db.add(meal_item)

    db.commit()
    db.refresh(meal_plan)
    return meal_plan


@router.get("/{patient_id}/{plan_id}/pdf")
async def download_meal_plan_pdf(
    patient_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user),
):
    """Download meal plan as PDF."""
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    plan = db.query(models.MealPlan).filter(
        models.MealPlan.id == plan_id,
        models.MealPlan.patient_id == patient_id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    pdf_bytes = _generate_meal_plan_pdf(patient, plan, current_user)
    filename = f"Plan_{patient.name.replace(' ', '_')}_{plan.date}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{patient_id}/{plan_id}")
async def delete_meal_plan(
    patient_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Delete meal plan."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meal_plan = db.query(models.MealPlan).filter(
        models.MealPlan.id == plan_id,
        models.MealPlan.patient_id == patient_id
    ).first()

    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    db.delete(meal_plan)
    db.commit()

    return {"message": "Meal plan deleted"}
