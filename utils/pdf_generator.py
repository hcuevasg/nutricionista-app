"""
PDF report generation using ReportLab.
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import (
    Drawing, Line, Circle, String as GString, Rect, Group
)
from reportlab.platypus import Image as RLImage
import io as _io
import utils.calculations as calc

try:
    from matplotlib.figure import Figure as _MplFigure
    _MPL_OK = True
except ImportError:
    _MPL_OK = False

try:
    from utils.image_helpers import make_circle_pil as _make_circle_pil
    _IMG_HELPERS_OK = True
except Exception:
    _IMG_HELPERS_OK = False

# ── Palette ───────────────────────────────────────────────────────────────────
PRIMARY   = colors.HexColor("#1a6b3c")
SECONDARY = colors.HexColor("#2ecc71")
LIGHT_BG  = colors.HexColor("#f0f9f4")
DARK_TEXT = colors.HexColor("#1c1c1c")
GRAY      = colors.HexColor("#6b7280")
TABLE_HDR = colors.HexColor("#1a6b3c")
TABLE_ALT = colors.HexColor("#e8f5ee")
SECTION_BG = colors.HexColor("#d1fae5")
SECTION_TXT = colors.HexColor("#065f46")
WHITE     = colors.white
RED_NEG   = colors.HexColor("#dc2626")
GREEN_POS = colors.HexColor("#16a34a")

def _rec_date(r: dict) -> str:
    """Return session date for display, falling back to system date."""
    return r.get("session_date") or r.get("date", "—") or "—"


def _patient_photo_rl(photo_path, size_cm: float = 2.5):
    """Return ReportLab Image from patient photo (circular crop), or None."""
    if not _IMG_HELPERS_OK or not photo_path:
        return None
    try:
        pil_img = _make_circle_pil(photo_path, 200)
        if pil_img is None:
            return None
        buf = _io.BytesIO()
        pil_img.save(buf, format="PNG")
        buf.seek(0)
        size = size_cm * cm
        return RLImage(buf, width=size, height=size)
    except Exception:
        return None


LEVEL_PDF_COLOR = {
    "excellent": colors.HexColor("#16a34a"),
    "good":      colors.HexColor("#16a34a"),
    "average":   colors.HexColor("#ca8a04"),
    "high":      colors.HexColor("#ea580c"),
    "very_high": colors.HexColor("#dc2626"),
    "low":       colors.HexColor("#2563eb"),
    "moderate":  colors.HexColor("#ca8a04"),
    "risk":      colors.HexColor("#dc2626"),
}


def _styles():
    base = getSampleStyleSheet()
    custom = {
        "title": ParagraphStyle(
            "ReportTitle", parent=base["Title"],
            fontSize=20, textColor=PRIMARY, spaceAfter=4,
            alignment=TA_CENTER, fontName="Helvetica-Bold"
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontSize=10, textColor=GRAY,
            alignment=TA_CENTER, spaceAfter=10, fontName="Helvetica"
        ),
        "section": ParagraphStyle(
            "Section", fontSize=12, textColor=PRIMARY, spaceBefore=12,
            spaceAfter=5, fontName="Helvetica-Bold"
        ),
        "body": ParagraphStyle(
            "Body", fontSize=9, textColor=DARK_TEXT,
            leading=13, fontName="Helvetica"
        ),
        "small": ParagraphStyle(
            "Small", fontSize=7, textColor=GRAY,
            alignment=TA_CENTER, fontName="Helvetica-Oblique"
        ),
        "footer_note": ParagraphStyle(
            "FooterNote", fontSize=8, textColor=GRAY,
            fontName="Helvetica-Oblique", spaceBefore=6
        ),
        "label": ParagraphStyle(
            "Label", fontSize=8, textColor=GRAY, fontName="Helvetica"
        ),
        "value": ParagraphStyle(
            "Value", fontSize=9, textColor=DARK_TEXT,
            fontName="Helvetica-Bold"
        ),
        "result_label": ParagraphStyle(
            "ResultLabel", fontSize=9, textColor=DARK_TEXT,
            fontName="Helvetica", leading=12
        ),
        "result_value": ParagraphStyle(
            "ResultValue", fontSize=10, textColor=PRIMARY,
            fontName="Helvetica-Bold"
        ),
    }
    return custom


def _base_table_style():
    return TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), TABLE_HDR),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [TABLE_ALT, WHITE]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#a7f3d0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ])


def _info_table(pairs: list[tuple], col_widths=None):
    S = _styles()
    data = [[Paragraph(k, S["label"]), Paragraph(str(v), S["value"])]
            for k, v in pairs]
    w = col_widths or [5 * cm, 10 * cm]
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BG, WHITE]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#d1fae5")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    return t


# ─────────────────────────────────────────────────────────────────────────────
#  ISAK COMPARATIVE REPORT
# ─────────────────────────────────────────────────────────────────────────────

def _fmt(val, suffix="", decimals=2):
    """Format a numeric value for display in cells."""
    if val is None:
        return "—"
    if suffix == "%":
        return f"{round(val, decimals)}%"
    return str(round(val, decimals)) if isinstance(val, float) else str(val)


def _cambio(first, last, decimals=2):
    """Return signed difference string or —."""
    if first is None or last is None:
        return "—"
    diff = round(last - first, decimals)
    return f"{diff:+.{decimals}f}"


def _cambio_color(text: str):
    if text.startswith("+"):
        return GREEN_POS
    if text.startswith("-"):
        return RED_NEG
    return GRAY


def generate_isak_report(patient: dict, records: list, output_path: str) -> str:
    """
    Generate ISAK-format comparative body composition report.
    records: list of anthropometric dicts ordered by date ASC.
    """
    S = _styles()
    n = len(records)

    # Column widths: variable name | sessions... | cambios
    # Landscape A4 usable ≈ 25.7 cm
    TOTAL_W = 25.0 * cm
    VAR_W   = 4.8 * cm
    CHG_W   = 2.5 * cm
    sess_w  = max(2.0 * cm, (TOTAL_W - VAR_W - CHG_W) / max(n, 1))
    col_widths = [VAR_W] + [sess_w] * n + [CHG_W]

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm
    )
    story = []

    # ── Header ───────────────────────────────────────────────────────────────
    story.append(Paragraph("INFORME COMPOSICIÓN CORPORAL", S["title"]))
    sex   = patient.get("sex", "—")
    age   = patient.get("age") or "—"
    dates = [_rec_date(r) for r in records]
    age_str = f"{age} años" if age != "—" else "edad no registrada"
    subtitle_para = Paragraph(
        f"{patient.get('name', '—')}  |  {sex}  |  {age_str}  |  "
        f"Sesiones: {len(records)}",
        S["subtitle"]
    )
    photo_rl = _patient_photo_rl(patient.get("photo_path"), size_cm=2.0)
    if photo_rl:
        hdr_tbl = Table([[subtitle_para, photo_rl]],
                        colWidths=[22.5 * cm, 2.5 * cm])
        hdr_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(hdr_tbl)
    else:
        story.append(subtitle_para)
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY,
                             spaceAfter=8))

    # ── Build comparative table ───────────────────────────────────────────────
    def _header_row(text, n_cols):
        """Full-width section separator row."""
        return [text] + [""] * n_cols

    def _data_row(label, values, first_val, last_val,
                  suffix="", decimals=2, bold_label=False):
        cells = [label] + [_fmt(v, suffix, decimals) for v in values]
        cells.append(_cambio(first_val, last_val, decimals))
        return cells

    # Table header
    date_headers = [f"Sesión {i+1}\n{d}" for i, d in enumerate(dates)]
    table_data = [["Variables medidas"] + date_headers + ["Cambios"]]

    # Helper: get raw value list from records for a given key
    def vals(key):
        return [r.get(key) for r in records]

    def first_last(key):
        v = [r.get(key) for r in records]
        nv = [x for x in v if x is not None]
        return (nv[0] if nv else None, nv[-1] if len(nv) >= 2 else None)

    # ── DATOS BÁSICOS ────────────────────────────────────────────────────────
    table_data.append(_header_row("DATOS BÁSICOS", n + 1))

    for label, key, sfx, dec in [
        ("Peso (kg)",             "weight_kg", "", 1),
        ("Talla (cm)",            "height_cm", "", 1),
        ("Circ. cintura mín. (cm)", "waist_cm", "", 1),
    ]:
        f0, f1 = first_last(key)
        table_data.append(_data_row(label, vals(key), f0, f1, sfx, dec))

    # ── PERÍMETROS ────────────────────────────────────────────────────────────
    table_data.append(_header_row("PERÍMETROS (cm)", n + 1))

    for label, key in [
        ("Brazo relajado (BR)",  "arm_relaxed_cm"),
        ("Brazo contraído (BC)", "arm_contracted_cm"),
        ('Cadera "glúteo"',      "hip_glute_cm"),
        ("Muslo máximo",         "thigh_max_cm"),
        ("Muslo medio",          "thigh_mid_cm"),
        ("Pantorrilla",          "calf_cm"),
    ]:
        f0, f1 = first_last(key)
        table_data.append(_data_row(label, vals(key), f0, f1, "", 1))

    # Diferencia BR-BC (calculated)
    dif_vals = []
    for r in records:
        br = r.get("arm_relaxed_cm")
        bc = r.get("arm_contracted_cm")
        dif_vals.append(round(bc - br, 2) if (br is not None and bc is not None) else None)
    dif_first = next((v for v in dif_vals if v is not None), None)
    dif_last  = next((v for v in reversed(dif_vals) if v is not None), None)
    dif_cells = [_fmt(v, "", 2) for v in dif_vals]
    table_data.append(
        ["Dif. BC - BR (cm)"] + dif_cells + [_cambio(dif_first, dif_last, 2)]
    )

    # ── PLIEGUES CUTÁNEOS ─────────────────────────────────────────────────────
    table_data.append(_header_row("PLIEGUES CUTÁNEOS (mm)", n + 1))

    for label, key in [
        ("Tríceps (*)",          "triceps_mm"),
        ("Subescapular (*)",     "subscapular_mm"),
        ("Bíceps",               "biceps_mm"),
        ("Cresta iliaca",        "iliac_crest_mm"),
        ("Supraespinal (*)",     "supraspinal_mm"),
        ("Abdominal (*)",        "abdominal_mm"),
        ("Muslo medial (*)",     "medial_thigh_mm"),
        ("Pantorrilla máx. (*)", "max_calf_mm"),
        ("Σ 6 pliegues (*)",     "sum_6_skinfolds"),
    ]:
        f0, f1 = first_last(key)
        table_data.append(_data_row(label, vals(key), f0, f1, "", 1))

    # ── RESULTADOS ────────────────────────────────────────────────────────────
    table_data.append(_header_row("RESULTADOS (Durnin & Womersley*)", n + 1))

    for label, key, sfx, dec in [
        ("% Masa grasa*",   "fat_mass_pct", "%", 1),
        ("Masa grasa (kg)", "fat_mass_kg",  "",  2),
        ("Masa magra (kg)", "lean_mass_kg", "",  2),
    ]:
        f0, f1 = first_last(key)
        table_data.append(_data_row(label, vals(key), f0, f1, sfx, dec))

    # ── Build ReportLab Table ─────────────────────────────────────────────────
    total_cols = 1 + n + 1  # var + sessions + cambios

    ts = _base_table_style()

    # Style section header rows
    section_rows = [i for i, row in enumerate(table_data)
                    if row and row[0] in (
                        "DATOS BÁSICOS", "PERÍMETROS (cm)",
                        "PLIEGUES CUTÁNEOS (mm)",
                        "RESULTADOS (Durnin & Womersley*)"
                    )]
    for sr in section_rows:
        ts.add("BACKGROUND", (0, sr), (-1, sr), SECTION_BG)
        ts.add("TEXTCOLOR",  (0, sr), (-1, sr), SECTION_TXT)
        ts.add("FONTNAME",   (0, sr), (-1, sr), "Helvetica-Bold")
        ts.add("SPAN",       (0, sr), (-1, sr))
        ts.add("FONTSIZE",   (0, sr), (-1, sr), 8)

    # Left-align variable name column
    ts.add("ALIGN", (0, 0), (0, -1), "LEFT")
    # Bold last column (Cambios)
    ts.add("FONTNAME", (-1, 1), (-1, -1), "Helvetica-Bold")
    ts.add("BACKGROUND", (-1, 0), (-1, 0), colors.HexColor("#064e3b"))

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(ts)
    story.append(tbl)
    story.append(Spacer(1, 14))

    # ── RESULTADOS SUMMARY ────────────────────────────────────────────────────
    if n >= 2:
        story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY,
                                 spaceAfter=6))
        story.append(Paragraph("RESULTADOS", S["section"]))

        d_first = _rec_date(records[0])
        d_last  = _rec_date(records[-1])
        story.append(Paragraph(
            f"Cambios desde <b>{d_first}</b> a <b>{d_last}</b>",
            S["body"]
        ))
        story.append(Spacer(1, 6))

        pat_sex = patient.get("sex", "")
        pat_age = patient.get("age", 30) or 30

        def _result_line_cls(label, key, suffix="", decimals=2, classify_fn=None):
            f0, f1 = first_last(key)
            chg = _cambio(f0, f1, decimals)
            v_last = _fmt(f1, suffix, decimals) if f1 is not None else "—"
            cat, level = ("—", None)
            if classify_fn and f1 is not None:
                try:
                    cat, level = classify_fn(f1)
                except Exception:
                    pass
            return [label, v_last, chg, cat, level]

        # Compute BMI for last record
        last_r = records[-1]
        first_r = records[0]
        bmi_last  = calc.bmi(last_r["weight_kg"],  last_r["height_cm"])  \
                    if last_r.get("weight_kg") and last_r.get("height_cm") else None
        bmi_first = calc.bmi(first_r["weight_kg"], first_r["height_cm"]) \
                    if first_r.get("weight_kg") and first_r.get("height_cm") else None

        rows_with_level = [
            _result_line_cls("Peso total (kg)",   "weight_kg",       "", 1),
            _result_line_cls("Masa magra (kg)",   "lean_mass_kg",    "", 2),
            _result_line_cls("Masa grasa (kg)",   "fat_mass_kg",     "", 2),
            _result_line_cls("% Masa grasa*",     "fat_mass_pct",    "%", 1,
                             lambda p: calc.classify_fat_pct(p, pat_sex, pat_age)),
            _result_line_cls("Σ 6 pliegues (mm)", "sum_6_skinfolds", "", 1),
        ]
        # Add BMI row manually
        bmi_cat, bmi_level = ("—", None)
        if bmi_last is not None:
            bmi_cat, bmi_level = calc.classify_bmi(bmi_last)
        rows_with_level.append([
            "IMC (kg/m²)",
            _fmt(bmi_last, "", 2) if bmi_last else "—",
            _cambio(bmi_first, bmi_last, 2),
            bmi_cat, bmi_level
        ])

        summary_data = [["Variable", "Última sesión", "Cambio total", "Clasificación"]]
        summary_data += [[r[0], r[1], r[2], r[3]] for r in rows_with_level]

        sum_ts = _base_table_style()
        sum_ts.add("ALIGN", (0, 0), (0, -1), "LEFT")
        sum_ts.add("ALIGN", (3, 0), (3, -1), "LEFT")

        for ri, row_data in enumerate(rows_with_level, start=1):
            chg = row_data[2]
            sum_ts.add("TEXTCOLOR", (2, ri), (2, ri), _cambio_color(chg))
            sum_ts.add("FONTNAME",  (2, ri), (2, ri), "Helvetica-Bold")
            level = row_data[4]
            if level and level in LEVEL_PDF_COLOR:
                sum_ts.add("TEXTCOLOR", (3, ri), (3, ri), LEVEL_PDF_COLOR[level])
                sum_ts.add("FONTNAME",  (3, ri), (3, ri), "Helvetica-Bold")

        sum_tbl = Table(
            summary_data,
            colWidths=[6 * cm, 4 * cm, 4 * cm, 4.5 * cm]
        )
        sum_tbl.setStyle(sum_ts)
        story.append(KeepTogether([sum_tbl]))
        story.append(Spacer(1, 14))

    # ── CLASSIFICATION TABLE (women) ──────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY,
                             spaceAfter=6))
    story.append(Paragraph(
        "CLASIFICACIÓN % MASA GRASA — MUJERES",
        S["section"]
    ))

    class_data = [
        ["Rango edad", "Excelente", "Bueno", "Promedio", "Elevado", "Muy elevado"],
        ["20-29 años", "< 15",  "16-19", "20-28", "29-31", "> 32"],
        ["30-39 años", "< 16",  "17-20", "21-29", "30-32", "> 33"],
        ["40-49 años", "< 17",  "18-21", "22-30", "31-33", "> 34"],
        ["50-59 años", "< 18",  "19-22", "23-31", "32-34", "> 35"],
        ["> 60 años",  "< 19",  "20-23", "24-32", "33-35", "> 36"],
    ]

    class_ts = _base_table_style()
    # Color code category columns
    class_ts.add("TEXTCOLOR", (1, 1), (1, -1), colors.HexColor("#065f46"))  # Excelente
    class_ts.add("TEXTCOLOR", (2, 1), (2, -1), colors.HexColor("#15803d"))  # Bueno
    class_ts.add("TEXTCOLOR", (3, 1), (3, -1), colors.HexColor("#ca8a04"))  # Promedio
    class_ts.add("TEXTCOLOR", (4, 1), (4, -1), colors.HexColor("#ea580c"))  # Elevado
    class_ts.add("TEXTCOLOR", (5, 1), (5, -1), colors.HexColor("#dc2626"))  # Muy elevado

    # Highlight row matching patient age if female
    if patient.get("sex", "").startswith("F") and patient.get("age"):
        age_val = patient["age"]
        age_row = (1 if age_val < 30 else
                   2 if age_val < 40 else
                   3 if age_val < 50 else
                   4 if age_val < 60 else 5)
        class_ts.add("BACKGROUND", (0, age_row), (-1, age_row),
                     colors.HexColor("#fef9c3"))

    class_tbl = Table(
        class_data,
        colWidths=[3 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm, 3.5 * cm]
    )
    class_tbl.setStyle(class_ts)
    story.append(KeepTogether([class_tbl]))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "*Según ecuación de Durnin & Womersley — Medición antropométrica ISAK 1  |  "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  NutriApp © 2025",
        S["small"]
    ))

    doc.build(story)
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
#  SOMATOCARTA (Heath & Carter)
# ─────────────────────────────────────────────────────────────────────────────

def _draw_somatocarta(endo: float, meso: float, ecto: float,
                      width_cm: float = 16, height_cm: float = 11) -> Drawing:
    """
    Return a ReportLab Drawing with the Heath-Carter somatocarta.
    X = Ecto - Endo  |  Y = 2×Meso - Ecto - Endo
    """
    W = width_cm * cm
    H = height_cm * cm
    ML, MR, MB, MT = 2.0 * cm, 1.0 * cm, 1.8 * cm, 0.6 * cm

    plot_w = W - ML - MR
    plot_h = H - MB - MT

    X_MIN, X_MAX = -9.0, 9.0
    Y_MIN, Y_MAX = -4.0, 13.0

    def to_px(sx, sy):
        px = ML + (sx - X_MIN) / (X_MAX - X_MIN) * plot_w
        py = MB + (sy - Y_MIN) / (Y_MAX - Y_MIN) * plot_h
        return px, py

    d = Drawing(W, H)

    # Background
    d.add(Rect(ML, MB, plot_w, plot_h,
               fillColor=colors.HexColor("#fafafa"),
               strokeColor=colors.HexColor("#d1d5db"), strokeWidth=0.5))

    # Grid lines
    for x in range(int(X_MIN), int(X_MAX) + 1):
        px1, py1 = to_px(x, Y_MIN)
        px2, py2 = to_px(x, Y_MAX)
        lc = colors.HexColor("#374151") if x == 0 else colors.HexColor("#e5e7eb")
        lw = 0.8 if x == 0 else 0.3
        d.add(Line(px1, py1, px2, py2, strokeColor=lc, strokeWidth=lw))
    for y in range(int(Y_MIN), int(Y_MAX) + 1):
        px1, py1 = to_px(X_MIN, y)
        px2, py2 = to_px(X_MAX, y)
        lc = colors.HexColor("#374151") if y == 0 else colors.HexColor("#e5e7eb")
        lw = 0.8 if y == 0 else 0.3
        d.add(Line(px1, py1, px2, py2, strokeColor=lc, strokeWidth=lw))

    # Axis tick labels
    for x in range(int(X_MIN), int(X_MAX) + 1, 2):
        px, py = to_px(x, Y_MIN)
        d.add(GString(px - 4, py - 10, str(x),
                      fontSize=6, fontName="Helvetica",
                      fillColor=colors.HexColor("#6b7280")))
    for y in range(int(Y_MIN), int(Y_MAX) + 1, 2):
        px, py = to_px(X_MIN, y)
        d.add(GString(px - 16, py - 3, str(y),
                      fontSize=6, fontName="Helvetica",
                      fillColor=colors.HexColor("#6b7280")))

    # Zone labels at extremes
    px_endo, py_mid = to_px(X_MIN + 0.3, (Y_MIN + Y_MAX) / 2)
    d.add(GString(ML + 2, py_mid, "ENDO",
                  fontSize=7, fontName="Helvetica-Bold",
                  fillColor=colors.HexColor("#dc2626")))

    px_ecto, _ = to_px(X_MAX - 2.5, (Y_MIN + Y_MAX) / 2)
    d.add(GString(px_ecto, py_mid, "ECTO",
                  fontSize=7, fontName="Helvetica-Bold",
                  fillColor=colors.HexColor("#2563eb")))

    px_meso, py_meso = to_px(-1, Y_MAX - 1.2)
    d.add(GString(px_meso, py_meso, "MESO",
                  fontSize=7, fontName="Helvetica-Bold",
                  fillColor=colors.HexColor("#16a34a")))

    px_ctr, py_ctr = to_px(-0.5, -0.8)
    d.add(GString(px_ctr, py_ctr, "Central",
                  fontSize=6, fontName="Helvetica-Oblique",
                  fillColor=colors.HexColor("#374151")))

    # Axis labels
    px_ax_mid, _ = to_px(0, Y_MIN)
    d.add(GString(ML, MB - 13,
                  "← Endomorfo           X = Ecto − Endo           Ectomorfo →",
                  fontSize=6, fontName="Helvetica",
                  fillColor=colors.HexColor("#6b7280")))
    _, py_ax_top = to_px(X_MIN, Y_MAX)
    d.add(GString(4, MB + plot_h / 2, "Y",
                  fontSize=6, fontName="Helvetica",
                  fillColor=colors.HexColor("#6b7280")))

    # Plot somatotype point
    x_val = ecto - endo
    y_val = 2 * meso - ecto - endo
    if X_MIN <= x_val <= X_MAX and Y_MIN <= y_val <= Y_MAX:
        px, py = to_px(x_val, y_val)
        # Shadow
        d.add(Circle(px + 1, py - 1, 6,
                     fillColor=colors.HexColor("#d1d5db"), strokeColor=None))
        # Point
        d.add(Circle(px, py, 6,
                     fillColor=PRIMARY, strokeColor=colors.white, strokeWidth=1.2))
        # Label
        d.add(GString(px + 9, py - 3,
                      f"{endo:.1f} – {meso:.1f} – {ecto:.1f}",
                      fontSize=7, fontName="Helvetica-Bold",
                      fillColor=DARK_TEXT))

    # Title
    d.add(GString(ML, H - 12,
                  "SOMATOCARTA DE HEATH & CARTER (1990)",
                  fontSize=8, fontName="Helvetica-Bold",
                  fillColor=PRIMARY))
    return d


# ─────────────────────────────────────────────────────────────────────────────
#  ISAK 2 REPORT
# ─────────────────────────────────────────────────────────────────────────────

def generate_isak2_report(patient: dict, records: list, output_path: str) -> str:
    """
    Generate ISAK 2 comparative body composition report with somatocarta.
    records: list of anthropometric dicts ordered by date ASC.
    """
    S = _styles()
    n = len(records)

    TOTAL_W = 25.0 * cm
    VAR_W   = 5.2 * cm
    CHG_W   = 2.5 * cm
    sess_w  = max(1.8 * cm, (TOTAL_W - VAR_W - CHG_W) / max(n, 1))
    col_widths = [VAR_W] + [sess_w] * n + [CHG_W]

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm
    )
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("INFORME COMPOSICIÓN CORPORAL — ISAK 2", S["title"]))
    sex = patient.get("sex", "—")
    age = patient.get("age") or "—"
    dates = [_rec_date(r) for r in records]
    age_str = f"{age} años" if age != "—" else "edad no registrada"
    subtitle_para2 = Paragraph(
        f"{patient.get('name', '—')}  |  {sex}  |  {age_str}  |  "
        f"Sesiones: {len(records)}",
        S["subtitle"]
    )
    photo_rl2 = _patient_photo_rl(patient.get("photo_path"), size_cm=2.0)
    if photo_rl2:
        hdr_tbl2 = Table([[subtitle_para2, photo_rl2]],
                         colWidths=[22.5 * cm, 2.5 * cm])
        hdr_tbl2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(hdr_tbl2)
    else:
        story.append(subtitle_para2)
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY, spaceAfter=8))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def vals(key):
        return [r.get(key) for r in records]

    def first_last(key):
        v = [r.get(key) for r in records]
        nv = [x for x in v if x is not None]
        return (nv[0] if nv else None, nv[-1] if len(nv) >= 2 else None)

    def _header_row(text, n_cols):
        return [text] + [""] * n_cols

    def _data_row(label, values, first_val, last_val, suffix="", decimals=2):
        cells = [label] + [_fmt(v, suffix, decimals) for v in values]
        cells.append(_cambio(first_val, last_val, decimals))
        return cells

    # ── Table header ──────────────────────────────────────────────────────────
    date_headers = [f"Sesión {i+1}\n{d}\n{r.get('isak_level','ISAK 1')}"
                    for i, (d, r) in enumerate(zip(dates, records))]
    table_data = [["Variables medidas"] + date_headers + ["Cambios"]]

    # ── DATOS BÁSICOS ─────────────────────────────────────────────────────────
    table_data.append(_header_row("DATOS BÁSICOS", n + 1))
    for label, key, sfx, dec in [
        ("Peso (kg)",             "weight_kg", "", 1),
        ("Talla (cm)",            "height_cm", "", 1),
        ("Circ. cintura mín. (cm)", "waist_cm", "", 1),
    ]:
        f0, f1 = first_last(key)
        table_data.append(_data_row(label, vals(key), f0, f1, sfx, dec))

    # ── PERÍMETROS ────────────────────────────────────────────────────────────
    table_data.append(_header_row("PERÍMETROS (cm)", n + 1))
    for label, key in [
        ("Brazo relajado (BR)",  "arm_relaxed_cm"),
        ("Brazo contraído (BC)", "arm_contracted_cm"),
        ('Cadera "glúteo"',      "hip_glute_cm"),
        ("Muslo máximo",         "thigh_max_cm"),
        ("Muslo medio",          "thigh_mid_cm"),
        ("Pantorrilla",          "calf_cm"),
        ("Cabeza",               "head_cm"),
        ("Cuello",               "neck_cm"),
        ("Tórax mesoesternal",   "chest_cm"),
        ("Tobillo mínimo",       "ankle_min_cm"),
    ]:
        f0, f1 = first_last(key)
        table_data.append(_data_row(label, vals(key), f0, f1, "", 1))

    dif_vals = []
    for r in records:
        br = r.get("arm_relaxed_cm"); bc = r.get("arm_contracted_cm")
        dif_vals.append(round(bc - br, 2) if (br and bc) else None)
    dif_first = next((v for v in dif_vals if v is not None), None)
    dif_last  = next((v for v in reversed(dif_vals) if v is not None), None)
    table_data.append(
        ["Dif. BC - BR (cm)"] + [_fmt(v, "", 2) for v in dif_vals]
        + [_cambio(dif_first, dif_last, 2)]
    )

    # ── PLIEGUES CUTÁNEOS ─────────────────────────────────────────────────────
    table_data.append(_header_row("PLIEGUES CUTÁNEOS (mm)", n + 1))
    for label, key in [
        ("Tríceps (*)",          "triceps_mm"),
        ("Subescapular (*)",     "subscapular_mm"),
        ("Bíceps",               "biceps_mm"),
        ("Cresta iliaca",        "iliac_crest_mm"),
        ("Supraespinal (*)",     "supraspinal_mm"),
        ("Abdominal (*)",        "abdominal_mm"),
        ("Muslo medial (*)",     "medial_thigh_mm"),
        ("Pantorrilla máx. (*)", "max_calf_mm"),
        ("Pectoral",             "pectoral_mm"),
        ("Axilar medio",         "axillary_mm"),
        ("Muslo anterior",       "front_thigh_mm"),
        ("Σ 6 pliegues (*)",     "sum_6_skinfolds"),
    ]:
        f0, f1 = first_last(key)
        table_data.append(_data_row(label, vals(key), f0, f1, "", 1))

    # ── DIÁMETROS ÓSEOS ───────────────────────────────────────────────────────
    table_data.append(_header_row("DIÁMETROS ÓSEOS (cm)", n + 1))
    for label, key in [
        ("Húmero bicondíleo",   "humerus_width_cm"),
        ("Fémur bicondíleo",    "femur_width_cm"),
        ("Biacromial",          "biacromial_cm"),
        ("Biiliocrestal",       "biiliocrestal_cm"),
        ("Ant-post. tórax",     "ap_chest_cm"),
        ("Transv. tórax",       "transv_chest_cm"),
        ("Longitud pie",        "foot_length_cm"),
        ("Muñeca biestiloideo", "wrist_cm"),
        ("Tobillo bimaleolar",  "ankle_bimalleolar_cm"),
    ]:
        f0, f1 = first_last(key)
        table_data.append(_data_row(label, vals(key), f0, f1, "", 2))

    # ── LONGITUDES ────────────────────────────────────────────────────────────
    table_data.append(_header_row("LONGITUDES (cm)", n + 1))
    for label, key in [
        ("Acromio-radial",      "acromion_radial_cm"),
        ("Radio-estiloide",     "radial_styloid_cm"),
        ("Iliospinal (pierna)", "iliospinal_height_cm"),
        ("Trocánter-tibial",    "trochanter_tibial_cm"),
    ]:
        f0, f1 = first_last(key)
        table_data.append(_data_row(label, vals(key), f0, f1, "", 1))

    # ── RESULTADOS ────────────────────────────────────────────────────────────
    table_data.append(_header_row("RESULTADOS (Durnin & Womersley* + ISAK 2**)", n + 1))
    for label, key, sfx, dec in [
        ("% Masa grasa* (D&W)", "fat_mass_pct",    "%", 1),
        ("Masa grasa (kg)",     "fat_mass_kg",     "",  2),
        ("Masa magra (kg)",     "lean_mass_kg",    "",  2),
        ("Endomorfia**",        "somatotype_endo", "",  2),
        ("Mesomorfia**",        "somatotype_meso", "",  2),
        ("Ectomorfia**",        "somatotype_ecto", "",  2),
        ("Índ. cintura/talla",  "waist_height_ratio", "", 3),
        ("AMB (cm²)",           "arm_muscle_area",  "",  2),
    ]:
        f0, f1 = first_last(key)
        table_data.append(_data_row(label, vals(key), f0, f1, sfx, dec))

    # ── Build ReportLab Table ─────────────────────────────────────────────────
    ts = _base_table_style()
    section_names = {
        "DATOS BÁSICOS", "PERÍMETROS (cm)", "PLIEGUES CUTÁNEOS (mm)",
        "DIÁMETROS ÓSEOS (cm)", "LONGITUDES (cm)",
        "RESULTADOS (Durnin & Womersley* + ISAK 2**)",
    }
    section_rows = [i for i, row in enumerate(table_data)
                    if row and row[0] in section_names]
    for sr in section_rows:
        ts.add("BACKGROUND", (0, sr), (-1, sr), SECTION_BG)
        ts.add("TEXTCOLOR",  (0, sr), (-1, sr), SECTION_TXT)
        ts.add("FONTNAME",   (0, sr), (-1, sr), "Helvetica-Bold")
        ts.add("SPAN",       (0, sr), (-1, sr))
        ts.add("FONTSIZE",   (0, sr), (-1, sr), 8)

    ts.add("ALIGN",    (0, 0), (0, -1), "LEFT")
    ts.add("FONTNAME", (-1, 1), (-1, -1), "Helvetica-Bold")
    ts.add("BACKGROUND", (-1, 0), (-1, 0), colors.HexColor("#064e3b"))

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(ts)
    story.append(tbl)
    story.append(Spacer(1, 14))

    # ── RESULTADOS SUMMARY ────────────────────────────────────────────────────
    if n >= 2:
        story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=6))
        story.append(Paragraph("RESUMEN DE CAMBIOS", S["section"]))
        story.append(Paragraph(
            f"Cambios desde <b>{_rec_date(records[0])}</b> a <b>{_rec_date(records[-1])}</b>",
            S["body"]
        ))
        story.append(Spacer(1, 6))

        pat_sex2 = patient.get("sex", "")
        pat_age2 = patient.get("age", 30) or 30

        def _result_line2(label, key, suffix="", decimals=2, classify_fn=None):
            f0, f1 = first_last(key)
            chg = _cambio(f0, f1, decimals)
            v_last = _fmt(f1, suffix, decimals) if f1 is not None else "—"
            cat, level = ("—", None)
            if classify_fn and f1 is not None:
                try:
                    cat, level = classify_fn(f1)
                except Exception:
                    pass
            return [label, v_last, chg, cat, level]

        rows2 = [
            _result_line2("Peso total (kg)",    "weight_kg",         "", 1),
            _result_line2("Masa magra (kg)",    "lean_mass_kg",      "", 2),
            _result_line2("Masa grasa (kg)",    "fat_mass_kg",       "", 2),
            _result_line2("% Masa grasa*",      "fat_mass_pct",      "%", 1,
                          lambda p: calc.classify_fat_pct(p, pat_sex2, pat_age2)),
            _result_line2("Σ 6 pliegues (mm)",  "sum_6_skinfolds",   "", 1),
            _result_line2("Endomorfia**",       "somatotype_endo",   "", 2),
            _result_line2("Mesomorfia**",       "somatotype_meso",   "", 2),
            _result_line2("Ectomorfia**",       "somatotype_ecto",   "", 2),
            _result_line2("Índ. cintura/talla", "waist_height_ratio", "", 3,
                          lambda r: calc.classify_whtr(r)),
        ]
        last2 = records[-1]; first2 = records[0]
        bmi2_last  = calc.bmi(last2["weight_kg"],  last2["height_cm"])  \
                     if last2.get("weight_kg") and last2.get("height_cm") else None
        bmi2_first = calc.bmi(first2["weight_kg"], first2["height_cm"]) \
                     if first2.get("weight_kg") and first2.get("height_cm") else None
        bmi2_cat, bmi2_level = ("—", None)
        if bmi2_last:
            bmi2_cat, bmi2_level = calc.classify_bmi(bmi2_last)
        rows2.append(["IMC (kg/m²)", _fmt(bmi2_last, "", 2) if bmi2_last else "—",
                       _cambio(bmi2_first, bmi2_last, 2), bmi2_cat, bmi2_level])

        summary_data = [["Variable", "Última sesión", "Cambio total", "Clasificación"]]
        summary_data += [[r[0], r[1], r[2], r[3]] for r in rows2]

        sum_ts = _base_table_style()
        sum_ts.add("ALIGN", (0, 0), (0, -1), "LEFT")
        sum_ts.add("ALIGN", (3, 0), (3, -1), "LEFT")
        for ri, row_data in enumerate(rows2, start=1):
            sum_ts.add("TEXTCOLOR", (2, ri), (2, ri), _cambio_color(row_data[2]))
            sum_ts.add("FONTNAME",  (2, ri), (2, ri), "Helvetica-Bold")
            level = row_data[4]
            if level and level in LEVEL_PDF_COLOR:
                sum_ts.add("TEXTCOLOR", (3, ri), (3, ri), LEVEL_PDF_COLOR[level])
                sum_ts.add("FONTNAME",  (3, ri), (3, ri), "Helvetica-Bold")

        sum_tbl = Table(summary_data, colWidths=[6 * cm, 4 * cm, 4 * cm, 4.5 * cm])
        sum_tbl.setStyle(sum_ts)
        story.append(KeepTogether([sum_tbl]))
        story.append(Spacer(1, 14))

    # ── SOMATOCARTA ───────────────────────────────────────────────────────────
    # Use latest record that has somatotype data
    soma_rec = None
    for r in reversed(records):
        if r.get("somatotype_endo") is not None:
            soma_rec = r
            break

    if soma_rec:
        story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=6))
        story.append(Paragraph("SOMATOCARTA DE HEATH & CARTER", S["section"]))
        story.append(Paragraph(
            f"Somatotipo: {soma_rec['somatotype_endo']:.1f} – "
            f"{soma_rec['somatotype_meso']:.1f} – "
            f"{soma_rec['somatotype_ecto']:.1f}  "
            f"(Endo – Meso – Ecto)  |  Sesión: {_rec_date(soma_rec)}",
            S["body"]
        ))
        story.append(Spacer(1, 6))
        drawing = _draw_somatocarta(
            soma_rec["somatotype_endo"],
            soma_rec["somatotype_meso"],
            soma_rec["somatotype_ecto"],
        )
        story.append(KeepTogether([drawing]))
        story.append(Spacer(1, 14))

    # ── CLASSIFICATION TABLE ──────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=6))
    story.append(Paragraph("CLASIFICACIÓN % MASA GRASA — MUJERES", S["section"]))

    class_data = [
        ["Rango edad", "Excelente", "Bueno", "Promedio", "Elevado", "Muy elevado"],
        ["20-29 años", "< 15", "16-19", "20-28", "29-31", "> 32"],
        ["30-39 años", "< 16", "17-20", "21-29", "30-32", "> 33"],
        ["40-49 años", "< 17", "18-21", "22-30", "31-33", "> 34"],
        ["50-59 años", "< 18", "19-22", "23-31", "32-34", "> 35"],
        ["> 60 años",  "< 19", "20-23", "24-32", "33-35", "> 36"],
    ]
    class_ts = _base_table_style()
    class_ts.add("TEXTCOLOR", (1, 1), (1, -1), colors.HexColor("#065f46"))
    class_ts.add("TEXTCOLOR", (2, 1), (2, -1), colors.HexColor("#15803d"))
    class_ts.add("TEXTCOLOR", (3, 1), (3, -1), colors.HexColor("#ca8a04"))
    class_ts.add("TEXTCOLOR", (4, 1), (4, -1), colors.HexColor("#ea580c"))
    class_ts.add("TEXTCOLOR", (5, 1), (5, -1), colors.HexColor("#dc2626"))

    if patient.get("sex", "").startswith("F") and patient.get("age"):
        age_val = patient["age"]
        age_row = (1 if age_val < 30 else 2 if age_val < 40 else
                   3 if age_val < 50 else 4 if age_val < 60 else 5)
        class_ts.add("BACKGROUND", (0, age_row), (-1, age_row),
                     colors.HexColor("#fef9c3"))

    class_tbl = Table(class_data,
                      colWidths=[3 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm, 3.5 * cm])
    class_tbl.setStyle(class_ts)
    story.append(KeepTogether([class_tbl]))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "*Durnin & Womersley (1974)  |  **Heath & Carter (1990) — "
        "Medición antropométrica ISAK 2  |  "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  NutriApp © 2025",
        S["small"]
    ))

    doc.build(story)
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
#  EVOLUTION CHARTS HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _make_chart_image(dates: list, values: list, title: str, color_hex: str,
                      w_cm: float = 11.5, h_cm: float = 5.5):
    """
    Generate a matplotlib chart and return a ReportLab Image flowable.
    dates/values may contain None; pairs where value is None are skipped.
    Returns None if fewer than 2 valid data points.
    """
    if not _MPL_OK:
        return None
    paired = [(d, v) for d, v in zip(dates, values) if v is not None]
    if len(paired) < 2:
        return None

    ds, vs = zip(*paired)
    xs = list(range(len(ds)))
    # Short date label: "15/01\n'24"
    def short_date(d):
        return f"{d[8:10]}/{d[5:7]}\n'{d[2:4]}"
    x_labels = [short_date(d) for d in ds]

    fig = _MplFigure(figsize=(w_cm / 2.54, h_cm / 2.54), dpi=150)
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#fafafa")

    ax.plot(xs, vs, "o-", color=color_hex, linewidth=1.5, markersize=5,
            markerfacecolor="white", markeredgecolor=color_hex, markeredgewidth=1.5,
            zorder=3)

    y_range = max(vs) - min(vs) if max(vs) != min(vs) else 1
    for xi, val in enumerate(vs):
        ax.annotate(str(round(val, 1)), xy=(xi, val),
                    textcoords="offset points", xytext=(0, 7),
                    ha="center", fontsize=6, fontweight="bold", color=color_hex)

    ax.set_xticks(xs)
    ax.set_xticklabels(x_labels, fontsize=6)
    ax.tick_params(axis="y", labelsize=6, colors="#6b7280")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["left"].set_color("#e5e7eb")
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.4, linestyle="--")
    ax.set_title(title, fontsize=8, color=color_hex, fontweight="bold", pad=4)
    y_pad = y_range * 0.18
    ax.set_ylim(min(vs) - y_pad, max(vs) + y_pad * 2.2)
    fig.tight_layout(pad=0.5)

    buf = _io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    fig.clf()

    return RLImage(buf, width=w_cm * cm, height=h_cm * cm)


def generate_evolution_report(patient: dict, records: list, output_path: str) -> str:
    """
    Generate a standalone PDF with 7 evolution charts (one per key variable).
    """
    if not _MPL_OK:
        raise RuntimeError(
            "matplotlib no está instalado. Ejecuta: pip install matplotlib"
        )
    S = _styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm
    )
    story = []

    sex = patient.get("sex", "—")
    age = patient.get("age") or "—"
    age_str = f"{age} años" if age != "—" else "edad no registrada"
    n = len(records)

    story.append(Paragraph("CURVAS DE EVOLUCIÓN", S["title"]))
    story.append(Paragraph(
        f"{patient.get('name', '—')}  |  {sex}  |  {age_str}  |  {n} sesiones",
        S["subtitle"]
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY, spaceAfter=10))

    dates = [_rec_date(r) for r in records]
    bmi_vals = [
        calc.bmi(r["weight_kg"], r["height_cm"])
        if r.get("weight_kg") and r.get("height_cm") else None
        for r in records
    ]

    charts = [
        ("Peso (kg)",          [r.get("weight_kg")       for r in records], "#1a6b3c"),
        ("% Masa grasa",       [r.get("fat_mass_pct")    for r in records], "#0d6efd"),
        ("Masa grasa (kg)",    [r.get("fat_mass_kg")     for r in records], "#dc2626"),
        ("Masa magra (kg)",    [r.get("lean_mass_kg")    for r in records], "#16a34a"),
        ("Σ 6 pliegues (mm)",  [r.get("sum_6_skinfolds") for r in records], "#7c3aed"),
        ("Cintura (cm)",       [r.get("waist_cm")         for r in records], "#ca8a04"),
        ("IMC (kg/m²)",        bmi_vals,                                     "#0891b2"),
    ]

    # Lay out 2 charts per row using a ReportLab Table
    pair_buf = []
    for title, values, color in charts:
        img = _make_chart_image(dates, values, title, color)
        pair_buf.append(img if img else Spacer(11.5 * cm, 5.5 * cm))
        if len(pair_buf) == 2:
            row_tbl = Table([pair_buf],
                            colWidths=[11.5 * cm, 11.5 * cm],
                            hAlign="LEFT")
            row_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING",  (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(row_tbl)
            story.append(Spacer(1, 8))
            pair_buf = []

    if pair_buf:
        pair_buf.append(Spacer(11.5 * cm, 5.5 * cm))
        row_tbl = Table([pair_buf], colWidths=[11.5 * cm, 11.5 * cm], hAlign="LEFT")
        row_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(row_tbl)

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Reporte de evolución — NutriApp © 2025  |  "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        S["small"]
    ))

    doc.build(story)
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
#  EXISTING REPORTS (kept intact)
# ─────────────────────────────────────────────────────────────────────────────

def generate_patient_report(patient: dict, anthropometrics: list,
                             meal_plans: list, meal_items_map: dict,
                             output_path: str) -> str:
    S = _styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    story = []

    story.append(Paragraph("NutriApp — Reporte del Paciente", S["title"]))
    story.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
        S["subtitle"]
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY, spaceAfter=8))

    story.append(Paragraph("Datos del Paciente", S["section"]))
    pairs = [
        ("Nombre completo", patient.get("name", "—")),
        ("Edad",            f"{patient.get('age') or '—'} años"),
        ("Sexo",            patient.get("sex", "—")),
        ("Teléfono",        patient.get("phone") or "—"),
        ("Correo",          patient.get("email") or "—"),
        ("Ocupación",       patient.get("occupation") or "—"),
        ("Notas",           patient.get("notes") or "—"),
        ("Registro",        patient.get("created_at", "—")),
    ]
    photo_rl = _patient_photo_rl(patient.get("photo_path"), size_cm=2.5)
    if photo_rl:
        info_tbl = _info_table(pairs, col_widths=[4.5 * cm, 9 * cm])
        combined = Table(
            [[info_tbl, photo_rl]],
            colWidths=[14 * cm, 3 * cm]
        )
        combined.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(combined)
    else:
        story.append(_info_table(pairs))
    story.append(Spacer(1, 10))

    if anthropometrics:
        story.append(Paragraph("Historial Antropométrico (ISAK)", S["section"]))
        hdrs = ["Fecha", "Peso", "Talla", "Cintura", "Σ6 Plieg.", "% Grasa*",
                "Masa Grasa", "Masa Magra"]
        rows = [hdrs]
        for a in anthropometrics:
            rows.append([
                _rec_date(a),
                f"{a.get('weight_kg', '—')} kg",
                f"{a.get('height_cm', '—')} cm",
                f"{a.get('waist_cm', '—')} cm",
                f"{a.get('sum_6_skinfolds', '—')} mm" if a.get("sum_6_skinfolds") else "—",
                f"{a.get('fat_mass_pct', '—')}%" if a.get("fat_mass_pct") else "—",
                f"{a.get('fat_mass_kg', '—')} kg" if a.get("fat_mass_kg") else "—",
                f"{a.get('lean_mass_kg', '—')} kg" if a.get("lean_mass_kg") else "—",
            ])
        t = Table(rows, colWidths=[2.2*cm, 1.8*cm, 1.8*cm, 1.8*cm,
                                    2.0*cm, 2.0*cm, 2.2*cm, 2.2*cm])
        t.setStyle(_base_table_style())
        story.append(KeepTogether([t]))
        story.append(Paragraph(
            "*Según ecuación de Durnin & Womersley — Medición antropométrica ISAK 1",
            S["footer_note"]
        ))
        story.append(Spacer(1, 10))

    if meal_plans:
        story.append(Paragraph("Planes Alimenticios", S["section"]))
        for plan in meal_plans:
            mid = plan["id"]
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                f"<b>{plan['name']}</b>  —  {plan['date']}", S["body"]
            ))
            meta = []
            if plan.get("calories"):  meta.append(f"Calorías: {plan['calories']} kcal")
            if plan.get("protein_g"): meta.append(f"Proteínas: {plan['protein_g']} g")
            if plan.get("carbs_g"):   meta.append(f"HC: {plan['carbs_g']} g")
            if plan.get("fat_g"):     meta.append(f"Grasas: {plan['fat_g']} g")
            if meta:
                story.append(Paragraph("  |  ".join(meta), S["label"]))

            items = meal_items_map.get(mid, [])
            if items:
                ihdrs = ["Tiempo", "Alimento", "Cant.", "Unid.",
                         "kcal", "Prot.", "HC", "Gras."]
                irows = [ihdrs] + [
                    [it.get("meal_type","—"), it.get("food_name","—"),
                     str(it.get("quantity","—")), it.get("unit","—"),
                     str(it.get("calories","—")), str(it.get("protein_g","—")),
                     str(it.get("carbs_g","—")), str(it.get("fat_g","—"))]
                    for it in items
                ]
                t2 = Table(irows, colWidths=[2*cm,4*cm,1.4*cm,1.4*cm,
                                              1.4*cm,1.4*cm,1.4*cm,1.4*cm])
                t2.setStyle(_base_table_style())
                story.append(KeepTogether([Spacer(1, 4), t2]))
            story.append(Spacer(1, 8))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Este reporte es de uso profesional exclusivo. NutriApp © 2025",
        S["small"]
    ))
    doc.build(story)
    return output_path


def generate_meal_plan_report(patient: dict, plan: dict,
                               items: list, output_path: str) -> str:
    S = _styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    story = []

    story.append(Paragraph("Plan Alimenticio", S["title"]))
    story.append(Paragraph(patient.get("name", ""), S["subtitle"]))
    story.append(Paragraph(
        f"Plan: {plan.get('name', '—')}  |  Fecha: {plan.get('date', '—')}",
        S["subtitle"]
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY, spaceAfter=8))

    story.append(Paragraph("Resumen del Plan", S["section"]))
    pairs = [
        ("Objetivo",        plan.get("goal") or "—"),
        ("Calorías totales", f"{plan.get('calories', '—')} kcal"),
        ("Proteínas",       f"{plan.get('protein_g', '—')} g"),
        ("Carbohidratos",   f"{plan.get('carbs_g', '—')} g"),
        ("Grasas",          f"{plan.get('fat_g', '—')} g"),
        ("Notas",           plan.get("notes") or "—"),
    ]
    story.append(_info_table(pairs))
    story.append(Spacer(1, 10))

    if items:
        story.append(Paragraph("Detalle de Alimentos", S["section"]))
        from collections import defaultdict
        by_meal = defaultdict(list)
        for it in items:
            by_meal[it["meal_type"]].append(it)

        meal_order = ["Desayuno","Media mañana","Almuerzo",
                      "Merienda","Cena","Colación"]
        sorted_meals = sorted(
            by_meal.keys(),
            key=lambda x: meal_order.index(x) if x in meal_order else 99
        )

        for meal_type in sorted_meals:
            meal_items = by_meal[meal_type]
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<b>{meal_type}</b>", S["body"]))
            hdrs = ["Alimento","Cantidad","Unidad","kcal","Prot.","HC","Gras."]
            rows = [hdrs]
            totals = [0.0] * 4
            for it in meal_items:
                rows.append([
                    it.get("food_name","—"), str(it.get("quantity","—")),
                    it.get("unit","—"),
                    str(it.get("calories") or "—"),
                    str(it.get("protein_g") or "—"),
                    str(it.get("carbs_g") or "—"),
                    str(it.get("fat_g") or "—"),
                ])
                for j, k in enumerate(["calories","protein_g","carbs_g","fat_g"]):
                    totals[j] += it.get(k) or 0
            rows.append([
                "TOTAL","","",
                f"{round(totals[0],1)}", f"{round(totals[1],1)}",
                f"{round(totals[2],1)}", f"{round(totals[3],1)}"
            ])
            t = Table(rows, colWidths=[4*cm,1.8*cm,1.8*cm,1.6*cm,
                                        1.8*cm,1.8*cm,1.8*cm])
            ts2 = _base_table_style()
            ts2.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
            ts2.add("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d1fae5"))
            t.setStyle(ts2)
            story.append(KeepTogether([Spacer(1, 3), t]))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Este plan es de uso exclusivo del paciente. NutriApp © 2025",
        S["small"]
    ))
    doc.build(story)
    return output_path
