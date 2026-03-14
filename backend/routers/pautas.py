"""Pautas de alimentación routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io
import json

import models, schemas, auth
from database import get_db

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

_NOMBRES_GRUPOS = {
    "cereales": "Cereales", "verduras_cg": "Verduras CG", "verduras_lc": "Verduras LC",
    "frutas": "Frutas", "lacteos_ag": "Lácteos AG", "lacteos_mg": "Lácteos MG",
    "lacteos_bg": "Lácteos BG", "legumbres": "Legumbres", "carnes_ag": "Carnes AG",
    "carnes_bg": "Carnes BG", "otros_proteicos": "Otros Proteicos",
    "aceite_grasas": "Aceite y Grasas", "alim_ricos_lipidos": "Ricos en Lípidos",
    "leches_vegetales": "Leches Vegetales", "lacteos_soya": "Lácteos de Soya",
    "semillas_chia": "Semillas Chía", "azucares": "Azúcares",
}

_TIEMPOS_COMIDA = [
    ("desayuno", "Desayuno"), ("colacion1", "Colación 1"), ("almuerzo", "Almuerzo"),
    ("colacion2", "Colación 2"), ("once", "Once"), ("cena", "Cena"),
]

router = APIRouter(prefix="/pautas", tags=["pautas"])


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
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Generador de menú con IA (Groq) ─────────────────────────────────────────

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

    import os
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY no configurada en el servidor")

    try:
        porciones = json.loads(pauta.porciones_json or "{}") if pauta.porciones_json else {}
        distribucion = json.loads(pauta.distribucion_json or "{}") if pauta.distribucion_json else {}
    except Exception:
        porciones = {}
        distribucion = {}

    # Construir descripción de tiempos con porciones
    tiempos_info = []
    for key, label in _TIEMPOS_COMIDA:
        grupos_t = distribucion.get(key, {})
        grupos_activos = [(g, float(p)) for g, p in grupos_t.items() if float(p or 0) > 0]
        if not grupos_activos:
            continue
        grupos_str = ", ".join(
            f"{_NOMBRES_GRUPOS.get(g, g)} {p:g}p" for g, p in grupos_activos
        )
        tiempos_info.append(f"- {label}: {grupos_str}")

    if not tiempos_info:
        raise HTTPException(status_code=400, detail="La pauta no tiene distribución por tiempos definida")

    tipo_label = TIPO_LABELS.get(pauta.tipo_pauta, pauta.tipo_pauta)
    prompt = f"""Pauta nutricional {tipo_label}, {pauta.kcal_objetivo:.0f} kcal/día para paciente chileno.

Distribución de grupos de alimentos por tiempo de comida (p = porciones):
{chr(10).join(tiempos_info)}

Genera ideas de menú concretas para cada tiempo de comida. Usa alimentos chilenos reales (pan marraqueta, cazuela, porotos, etc.) con cantidades en medidas caseras (tazas, cucharadas, unidades).

Responde ÚNICAMENTE con JSON válido, sin texto adicional, con exactamente este formato:
{{
  "desayuno": {{"opcion1": "...", "opcion2": "..."}},
  "colacion1": {{"opcion1": "...", "opcion2": "..."}},
  "almuerzo": {{"opcion1": "...", "opcion2": "..."}},
  "colacion2": {{"opcion1": "...", "opcion2": "..."}},
  "once": {{"opcion1": "...", "opcion2": "..."}},
  "cena": {{"opcion1": "...", "opcion2": "..."}}
}}

Solo incluye los tiempos que aparecen en la distribución. Cada opción debe ser una descripción en 1 línea."""

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres un nutricionista clínico experto en alimentación saludable chilena. Respondes SOLO con JSON válido, sin texto adicional."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        raw = completion.choices[0].message.content.strip()

        # Extraer JSON si viene con markdown code blocks
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        menu = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="La IA no retornó un JSON válido. Intenta de nuevo.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con Groq: {str(e)}")

    pauta.menu_json = json.dumps(menu, ensure_ascii=False)
    db.commit()
    db.refresh(pauta)
    return {"menu": menu}


# ── PDF generation ──────────────────────────────────────────────────

def _hex(h: str):
    """Convert #RRGGBB to ReportLab Color."""
    from reportlab.lib.colors import HexColor
    return HexColor(h)


TIPO_LABELS = {
    "omnivoro": "Omnívoro",
    "ovolacto": "Ovo-lacto vegetariano",
    "vegano": "Vegano",
    "vegetariano": "Vegetariano",
    "renal": "Renal",
    "diabetico": "Diabético",
    "hipocalorico": "Hipocalórico",
}

FA_LABELS = {
    "sedentaria": "Sedentaria (×1.2)",
    "liviana": "Liviana (×1.375)",
    "moderada": "Moderada (×1.55)",
    "intensa": "Intensa (×1.725)",
}


def _generate_pauta_pdf(patient, pauta, nutritionist) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
    )
    from reportlab.lib import colors

    C_PRIMARY    = _hex("#4b7c60")
    C_TERRA      = _hex("#c06c52")
    C_SAGE       = _hex("#8da399")
    C_BG         = _hex("#F7F5F2")
    C_BORDER     = _hex("#E5EAE7")
    C_MUTED      = _hex("#6b7280")
    WHITE        = colors.white

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    base = getSampleStyleSheet()

    def style(name, **kw):
        s = ParagraphStyle(name, parent=base["Normal"], **kw)
        return s

    S_TITLE    = style("Title",    fontSize=18, textColor=C_PRIMARY, leading=22, spaceAfter=4)
    S_SUBTITLE = style("Sub",      fontSize=10, textColor=C_MUTED,   leading=14)
    S_SEC      = style("Sec",      fontSize=11, textColor=C_PRIMARY, leading=16, spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold")
    S_BODY     = style("Body",     fontSize=9,  textColor=colors.black, leading=13)
    S_SMALL    = style("Small",    fontSize=8,  textColor=C_MUTED,   leading=12)
    S_TH       = style("TH",       fontSize=8,  textColor=WHITE,     leading=12, fontName="Helvetica-Bold", alignment=TA_CENTER)
    S_TD       = style("TD",       fontSize=9,  textColor=colors.black, leading=13, alignment=TA_CENTER)
    S_TD_L     = style("TDL",      fontSize=9,  textColor=colors.black, leading=13, alignment=TA_LEFT)
    S_BOLD     = style("Bold",     fontSize=10, textColor=colors.black, leading=14, fontName="Helvetica-Bold")

    def section(title: str):
        return KeepTogether([
            Paragraph(title, S_SEC),
        ])

    def kv_table(rows: list[tuple[str, str]]) -> Table:
        data = [[Paragraph(k, S_SMALL), Paragraph(v, S_BODY)] for k, v in rows]
        t = Table(data, colWidths=[5*cm, None])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), C_BG),
            ("TEXTCOLOR",  (0, 0), (0, -1), C_MUTED),
            ("VALIGN",     (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, C_BG]),
            ("GRID",       (0, 0), (-1, -1), 0.3, C_BORDER),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ]))
        return t

    def fmt(v, d=0):
        if v is None:
            return "—"
        return f"{float(v):.{d}f}"

    story = []

    # ── Header ──────────────────────────────────────────────────────
    from datetime import date as dt_date
    header_data = [[
        Paragraph("NutriApp", style("H1", fontSize=20, textColor=WHITE, fontName="Helvetica-Bold")),
        Paragraph(
            f"Generado: {dt_date.today().strftime('%d/%m/%Y')}<br/>"
            f"Profesional: {nutritionist.name or nutritionist.username}",
            style("H2", fontSize=8, textColor=_hex("#d1fae5"), alignment=1)
        ),
    ]]
    header_t = Table(header_data, colWidths=["60%", "40%"])
    header_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_PRIMARY),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(header_t)
    story.append(Spacer(1, 0.5*cm))

    # Pauta title
    story.append(Paragraph(pauta.name, S_TITLE))
    story.append(Paragraph(
        f"{TIPO_LABELS.get(pauta.tipo_pauta, pauta.tipo_pauta)}  ·  {pauta.date}",
        S_SUBTITLE,
    ))
    story.append(Spacer(1, 0.4*cm))

    # ── Paciente ────────────────────────────────────────────────────
    story.append(section("Datos del Paciente"))
    story.append(kv_table([
        ("Nombre",  patient.name),
        ("Sexo",    "Masculino" if pauta.sexo == "M" else "Femenino"),
        ("Edad",    f"{pauta.edad} años"),
        ("Peso",    f"{fmt(pauta.peso, 1)} kg"),
    ]))
    story.append(Spacer(1, 0.3*cm))

    # ── Requerimientos energéticos ───────────────────────────────────
    story.append(section("Requerimientos Energéticos"))

    req_rows = [
        [Paragraph("Indicador", S_TH), Paragraph("Valor", S_TH), Paragraph("Método / Nota", S_TH)],
        [Paragraph("TMB", S_TD_L), Paragraph(f"{fmt(pauta.tmb, 0)} kcal/día", S_TD), Paragraph("Mifflin-St Jeor", S_TD)],
        [Paragraph("Factor de Actividad", S_TD_L), Paragraph(FA_LABELS.get(pauta.fa_key, pauta.fa_key), S_TD), Paragraph("", S_TD)],
        [Paragraph("GET (TMB × FA)", S_TD_L), Paragraph(f"{fmt(pauta.get_kcal, 0)} kcal/día", S_TD), Paragraph("", S_TD)],
    ]
    if pauta.ajuste_kcal:
        sign = "+" if pauta.ajuste_kcal > 0 else ""
        req_rows.append([
            Paragraph("Ajuste calórico", S_TD_L),
            Paragraph(f"{sign}{fmt(pauta.ajuste_kcal, 0)} kcal", S_TD),
            Paragraph("Superávit / déficit", S_TD),
        ])
    req_rows.append([
        Paragraph("Kcal Objetivo", style("TDObj", fontSize=10, textColor=C_PRIMARY, fontName="Helvetica-Bold", alignment=TA_LEFT)),
        Paragraph(f"{fmt(pauta.kcal_objetivo, 0)} kcal/día", style("TDObjV", fontSize=10, textColor=C_PRIMARY, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        Paragraph("", S_TD),
    ])

    req_t = Table(req_rows, colWidths=[6*cm, 4*cm, None])
    req_t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), C_PRIMARY),
        ("BACKGROUND",   (0, -1), (-1, -1), _hex("#e8f0eb")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -2), [WHITE, C_BG]),
        ("GRID",         (0, 0), (-1, -1), 0.3, C_BORDER),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(req_t)
    story.append(Spacer(1, 0.3*cm))

    # ── Distribución de macronutrientes ──────────────────────────────
    story.append(section("Distribución de Macronutrientes"))

    macro_header = [
        Paragraph("Macronutriente", S_TH),
        Paragraph("%", S_TH),
        Paragraph("g/día", S_TH),
        Paragraph("kcal/día", S_TH),
        Paragraph("g/kg peso", S_TH),
    ]
    macro_data = [macro_header]

    macros = [
        ("Proteínas",      pauta.prot_pct, pauta.prot_g, pauta.prot_kcal, pauta.prot_g_kg, _hex("#dbeafe")),
        ("Lípidos",        pauta.lip_pct,  pauta.lip_g,  pauta.lip_kcal,  None,            _hex("#fef9c3")),
        ("Carbohidratos",  pauta.cho_pct,  pauta.cho_g,  pauta.cho_kcal,  None,            _hex("#ffedd5")),
    ]
    for name, pct, g, kcal, gkg, bg in macros:
        macro_data.append([
            Paragraph(name, S_TD_L),
            Paragraph(f"{fmt(pct, 0)}%", S_TD),
            Paragraph(f"{fmt(g, 1)} g", S_TD),
            Paragraph(f"{fmt(kcal, 0)} kcal", S_TD),
            Paragraph(f"{fmt(gkg, 2)} g/kg" if gkg is not None else "—", S_TD),
        ])

    # Total row
    total_g = (pauta.prot_g or 0) + (pauta.lip_g or 0) + (pauta.cho_g or 0)
    total_kcal = (pauta.prot_kcal or 0) + (pauta.lip_kcal or 0) + (pauta.cho_kcal or 0)
    macro_data.append([
        Paragraph("TOTAL", style("TotL", fontSize=9, fontName="Helvetica-Bold", alignment=TA_LEFT)),
        Paragraph("100%", style("Tot",  fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        Paragraph(f"{total_g:.1f} g", style("Tot", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        Paragraph(f"{total_kcal:.0f} kcal", style("Tot", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        Paragraph("", S_TD),
    ])

    macro_t = Table(macro_data, colWidths=[5*cm, 2.5*cm, 3*cm, 3.5*cm, None])
    row_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("BACKGROUND", (0, -1), (-1, -1), C_BG),
        ("GRID",       (0, 0), (-1, -1), 0.3, C_BORDER),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]
    for i, (_, _, _, _, _, bg) in enumerate(macros, start=1):
        row_styles.append(("BACKGROUND", (0, i), (-1, i), bg))
    macro_t.setStyle(TableStyle(row_styles))
    story.append(macro_t)

    # ── Distribución por grupos y tiempos ────────────────────────────
    try:
        porciones = json.loads(pauta.porciones_json or "{}") if pauta.porciones_json else {}
        distribucion = json.loads(pauta.distribucion_json or "{}") if pauta.distribucion_json else {}
    except Exception:
        porciones = {}
        distribucion = {}

    grupos_con_porciones = [(g, float(p)) for g, p in porciones.items() if float(p or 0) > 0]

    if grupos_con_porciones:
        story.append(Spacer(1, 0.3*cm))
        story.append(section("Porciones por Grupo de Alimentos"))

        # Header
        porc_header = [
            Paragraph("Grupo", S_TH), Paragraph("kcal/p", S_TH), Paragraph("prot/p", S_TH),
            Paragraph("Porciones/día", S_TH), Paragraph("Aporte kcal", S_TH), Paragraph("Aporte prot", S_TH),
        ]
        porc_data = [porc_header]
        total_aporte = {"kcal": 0.0, "prot": 0.0}
        for g, p in grupos_con_porciones:
            m = _GRUPOS_MACROS.get(g, {})
            aporte_kcal = round(m.get("kcal", 0) * p)
            aporte_prot = round(m.get("prot", 0) * p, 1)
            total_aporte["kcal"] += aporte_kcal
            total_aporte["prot"] += aporte_prot
            porc_data.append([
                Paragraph(_NOMBRES_GRUPOS.get(g, g), S_TD_L),
                Paragraph(str(m.get("kcal", "—")), S_TD),
                Paragraph(f"{m.get('prot', '—')}g", S_TD),
                Paragraph(f"{p:g}", S_TD),
                Paragraph(f"{aporte_kcal} kcal", S_TD),
                Paragraph(f"{aporte_prot}g", S_TD),
            ])
        porc_data.append([
            Paragraph("TOTAL", style("PorcTot", fontSize=9, fontName="Helvetica-Bold", alignment=TA_LEFT)),
            Paragraph("", S_TD), Paragraph("", S_TD), Paragraph("", S_TD),
            Paragraph(f"{round(total_aporte['kcal'])} kcal", style("PorcTotV", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)),
            Paragraph(f"{round(total_aporte['prot'], 1)}g", style("PorcTotVP", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        ])
        porc_t = Table(porc_data, colWidths=[4.5*cm, 1.8*cm, 1.8*cm, 3*cm, 3.2*cm, None])
        row_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
            ("BACKGROUND", (0, -1), (-1, -1), _hex("#e8f0eb")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [WHITE, C_BG]),
            ("GRID", (0, 0), (-1, -1), 0.3, C_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        porc_t.setStyle(TableStyle(row_styles))
        story.append(porc_t)

    if distribucion and any(distribucion.values()):
        story.append(Spacer(1, 0.3*cm))
        story.append(section("Distribución por Tiempo de Comida"))

        # Compute kcal per tiempo
        total_dist_kcal = 0.0
        tiempo_kcal: dict = {}
        for key, _ in _TIEMPOS_COMIDA:
            grupos_t = distribucion.get(key, {})
            kcal_t = sum(_GRUPOS_MACROS.get(g, {}).get("kcal", 0) * float(p or 0) for g, p in grupos_t.items())
            tiempo_kcal[key] = round(kcal_t)
            total_dist_kcal += kcal_t

        dist_header = [Paragraph("Tiempo", S_TH)] + [
            Paragraph(label, S_TH) for _, label in _TIEMPOS_COMIDA
        ] + [Paragraph("TOTAL", S_TH)]

        # Row per group that appears in any tiempo
        all_groups_dist = set()
        for v in distribucion.values():
            all_groups_dist.update(k for k, p in v.items() if float(p or 0) > 0)

        dist_data = [dist_header]
        for g in sorted(all_groups_dist):
            row = [Paragraph(_NOMBRES_GRUPOS.get(g, g), S_TD_L)]
            total_g = 0.0
            for key, _ in _TIEMPOS_COMIDA:
                p = float(distribucion.get(key, {}).get(g, 0) or 0)
                total_g += p
                row.append(Paragraph(f"{p:g}" if p else "—", S_TD))
            row.append(Paragraph(f"{total_g:g}", style("DistTot", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)))
            dist_data.append(row)

        # Kcal row
        kcal_row = [Paragraph("kcal", style("DistKcal", fontSize=8, textColor=C_MUTED, alignment=TA_LEFT))]
        for key, _ in _TIEMPOS_COMIDA:
            kcal_row.append(Paragraph(str(tiempo_kcal[key]) if tiempo_kcal[key] else "—", style("DKV", fontSize=8, textColor=C_TERRA, alignment=TA_CENTER)))
        kcal_row.append(Paragraph(str(round(total_dist_kcal)), style("DKVtot", fontSize=8, fontName="Helvetica-Bold", textColor=C_TERRA, alignment=TA_CENTER)))
        dist_data.append(kcal_row)

        # %VCT row
        pct_row = [Paragraph("%VCT", style("DistPct", fontSize=8, textColor=C_MUTED, alignment=TA_LEFT))]
        for key, _ in _TIEMPOS_COMIDA:
            pct = round((tiempo_kcal[key] / total_dist_kcal) * 100) if total_dist_kcal else 0
            pct_row.append(Paragraph(f"{pct}%" if pct else "—", style("DPV", fontSize=8, textColor=C_SAGE, alignment=TA_CENTER)))
        pct_row.append(Paragraph("100%", style("DPVtot", fontSize=8, fontName="Helvetica-Bold", textColor=C_SAGE, alignment=TA_CENTER)))
        dist_data.append(pct_row)

        n_cols = len(_TIEMPOS_COMIDA) + 2  # grupo + 6 tiempos + total
        col_w = [3.5*cm] + [1.8*cm] * len(_TIEMPOS_COMIDA) + [1.8*cm]
        dist_t = Table(dist_data, colWidths=col_w)
        dist_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
            ("BACKGROUND", (0, -2), (-1, -1), C_BG),
            ("BACKGROUND", (-1, 0), (-1, -1), _hex("#e8f0eb")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -3), [WHITE, C_BG]),
            ("GRID", (0, 0), (-1, -1), 0.3, C_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(dist_t)

    # ── Notas ───────────────────────────────────────────────────────
    if pauta.notes:
        story.append(Spacer(1, 0.3*cm))
        story.append(section("Observaciones"))
        story.append(Paragraph(pauta.notes.replace("\n", "<br/>"), S_BODY))

    # ── Footer ──────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    footer_t = Table([[
        Paragraph(
            f"NutriApp — Documento generado el {dt_date.today().strftime('%d/%m/%Y')}",
            style("Foot", fontSize=7, textColor=C_MUTED)
        ),
        Paragraph(
            "Este documento es de uso profesional y confidencial.",
            style("FootR", fontSize=7, textColor=C_MUTED, alignment=1)
        ),
    ]])
    footer_t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(footer_t)

    doc.build(story)
    return buf.getvalue()
