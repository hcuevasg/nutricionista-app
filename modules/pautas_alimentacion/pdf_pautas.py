"""
Generación de PDF para Pautas de Alimentación con ReportLab.
Paleta: navy (#1B3A6B) encabezados, naranja (#E87722) acentos.
"""
import os
from datetime import datetime
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.platypus import Image as RLImage
import io as _io

from modules.pautas_alimentacion.grupos_alimentos import (
    NOMBRES_GRUPOS, NOMBRES_TIPOS_PAUTA, TIEMPOS_COMIDA
)
from modules.pautas_alimentacion.tablas_equivalencias import (
    TABLAS_EQUIVALENCIAS, NOMBRES_GRUPOS_EQUIV, ABREVIATURAS
)
from modules.pautas_alimentacion.distribucion_porciones import (
    calcular_aporte_total, calcular_aporte_por_tiempo
)
from modules.pautas_alimentacion.grupos_alimentos import GRUPOS_MACROS

try:
    from utils.image_helpers import make_circle_pil as _make_circle_pil
    _IMG_OK = True
except Exception:
    _IMG_OK = False

# ── Paleta ────────────────────────────────────────────────────────────────────
NAVY        = colors.HexColor("#1B3A6B")
ORANGE      = colors.HexColor("#E87722")
NAVY_LIGHT  = colors.HexColor("#2E5BA8")
NAVY_PALE   = colors.HexColor("#E8EEF7")
ORANGE_PALE = colors.HexColor("#FEF3E8")
WHITE       = colors.white
GRAY        = colors.HexColor("#6B7280")
GRAY_LIGHT  = colors.HexColor("#F5F5F5")
DARK        = colors.HexColor("#2C2C2C")
GREEN_OK    = colors.HexColor("#2E7D32")
AMBER       = colors.HexColor("#E65100")
RED_BAD     = colors.HexColor("#C62828")
ROW_ALT     = colors.HexColor("#F5F5F5")
BORDER_CLR  = colors.HexColor("#D1D5DB")

_PAGE_W, _PAGE_H = A4
_MARGIN = 2 * cm
_CONTENT_W = _PAGE_W - 2 * _MARGIN

# ── Meses en español ──────────────────────────────────────────────────────────
_MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}


def _fecha_es(fecha_str: str) -> str:
    """Convierte 'YYYY-MM-DD' a '11 de marzo de 2026'."""
    try:
        d = datetime.strptime(fecha_str, "%Y-%m-%d")
        return f"{d.day} de {_MESES_ES[d.month]} de {d.year}"
    except Exception:
        return fecha_str


# ── Estilos ───────────────────────────────────────────────────────────────────
def _styles() -> dict:
    return {
        "title": ParagraphStyle(
            "PTitle", fontSize=22, textColor=NAVY, alignment=TA_CENTER,
            fontName="Helvetica-Bold", spaceAfter=4
        ),
        "subtitle": ParagraphStyle(
            "PSub", fontSize=11, textColor=GRAY, alignment=TA_CENTER,
            fontName="Helvetica", spaceAfter=8
        ),
        "section": ParagraphStyle(
            "PSection", fontSize=11, textColor=WHITE, fontName="Helvetica-Bold",
            spaceBefore=0, spaceAfter=0
        ),
        "body": ParagraphStyle(
            "PBody", fontSize=9, textColor=DARK, fontName="Helvetica", leading=13
        ),
        "small": ParagraphStyle(
            "PSmall", fontSize=7, textColor=GRAY, fontName="Helvetica-Oblique",
            alignment=TA_CENTER
        ),
        "center": ParagraphStyle(
            "PCenter", fontSize=9, textColor=DARK, fontName="Helvetica",
            alignment=TA_CENTER
        ),
        "bold": ParagraphStyle(
            "PBold", fontSize=9, textColor=DARK, fontName="Helvetica-Bold"
        ),
        "equiv_group": ParagraphStyle(
            "PEquivGroup", fontSize=10, textColor=NAVY, fontName="Helvetica-Bold",
            spaceBefore=0, spaceAfter=0
        ),
        "equiv_item": ParagraphStyle(
            "PEquivItem", fontSize=8, textColor=DARK, fontName="Helvetica",
            leading=13, leftIndent=12
        ),
        "section_title": ParagraphStyle(
            "PSectionTitle", fontSize=11, textColor=WHITE,
            fontName="Helvetica-Bold"
        ),
        "col_header": ParagraphStyle(
            "PColHdr", fontSize=8, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER
        ),
        "cell": ParagraphStyle(
            "PCell", fontSize=8, textColor=DARK,
            fontName="Helvetica"
        ),
        "cell_c": ParagraphStyle(
            "PCellC", fontSize=8, textColor=DARK,
            fontName="Helvetica", alignment=TA_CENTER
        ),
        "small_bold": ParagraphStyle(
            "PSmallBold", fontSize=8, textColor=NAVY,
            fontName="Helvetica-Bold"
        ),
        "patient_name": ParagraphStyle(
            "PPatName", fontSize=20, textColor=DARK, fontName="Helvetica-Bold",
            alignment=TA_CENTER, spaceAfter=4
        ),
        "patient_sub": ParagraphStyle(
            "PPatSub", fontSize=11, textColor=GRAY, fontName="Helvetica",
            alignment=TA_CENTER, spaceAfter=3
        ),
        "cover_date": ParagraphStyle(
            "PCoverDate", fontSize=10, textColor=GRAY, fontName="Helvetica",
            alignment=TA_CENTER
        ),
    }


def _section_band(title: str, styles: dict) -> Table:
    """Banda de color naranja con título de sección en blanco."""
    tbl = Table(
        [[Paragraph(title, styles["section"])]],
        colWidths=[_CONTENT_W]
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), ORANGE),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    return tbl


def _hdr_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ("GRID",          (0, 0), (-1, -1), 0.3, BORDER_CLR),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ])


def _borde_pagina(canvas, doc):
    """Rectángulo decorativo navy en todas las páginas."""
    canvas.saveState()
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(6)
    canvas.rect(15, 15, _PAGE_W - 30, _PAGE_H - 30)
    canvas.restoreState()


def _footer(canvas, doc):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    canvas.saveState()
    # Línea separadora
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(0.5)
    canvas.line(_MARGIN, 1.5 * cm, _PAGE_W - _MARGIN, 1.5 * cm)
    # Texto pie
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRAY)
    canvas.drawString(_MARGIN, 1.1 * cm,
                      f"Generado: {now}  |  NutriApp \xa9 2025")
    canvas.drawRightString(
        _PAGE_W - _MARGIN, 1.1 * cm, f"P\xe1gina {doc.page}"
    )
    _borde_pagina(canvas, doc)
    canvas.restoreState()


def _footer_first(canvas, doc):
    """Pie + borde para la portada (sin número de página)."""
    canvas.saveState()
    _borde_pagina(canvas, doc)
    canvas.restoreState()


def _patient_photo(photo_path: Optional[str], size_cm: float = 3.0):
    if not _IMG_OK or not photo_path:
        return None
    try:
        pil_img = _make_circle_pil(photo_path, 240)
        if pil_img is None:
            return None
        buf = _io.BytesIO()
        pil_img.save(buf, format="PNG")
        buf.seek(0)
        sz = size_cm * cm
        return RLImage(buf, width=sz, height=sz)
    except Exception:
        return None


def _fmt(v, dec=1, suffix=""):
    """Formatea un número con decimales; retorna '—' si None/0."""
    if v is None:
        return "\u2014"
    try:
        return f"{round(float(v), dec)}{suffix}"
    except Exception:
        return str(v)


# ── Construcción de secciones ─────────────────────────────────────────────────

def _build_portada(paciente: dict, pauta: dict, styles: dict, story: list):
    """Página 1 — Portada."""
    story.append(Spacer(1, 1.8 * cm))

    tipo_label = NOMBRES_TIPOS_PAUTA.get(pauta.get("tipo_pauta", ""), "Pauta Alimenticia")

    # Logo / nombre app
    story.append(Paragraph("NutriApp", ParagraphStyle(
        "PApp", fontSize=28, textColor=NAVY, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=2
    )))
    story.append(Paragraph("Gesti\xf3n Nutricional", ParagraphStyle(
        "PAppSub", fontSize=12, textColor=GRAY, fontName="Helvetica",
        alignment=TA_CENTER, spaceAfter=16
    )))

    # Banda navy con tipo de pauta
    banda = Table(
        [[Paragraph("Pauta de Alimentaci\xf3n", styles["section_title"]),
          Paragraph(tipo_label, ParagraphStyle(
              "PTipoOrange", fontSize=11, textColor=ORANGE,
              fontName="Helvetica-Bold", alignment=TA_RIGHT
          ))]],
        colWidths=[_CONTENT_W * 0.6, _CONTENT_W * 0.4]
    )
    banda.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(banda)
    story.append(Spacer(1, 0.8 * cm))

    # Foto o avatar
    foto = _patient_photo(paciente.get("photo_path"), 3.5)
    if foto:
        foto_tbl = Table([[foto]], colWidths=[_CONTENT_W],
                         style=TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(foto_tbl)
        story.append(Spacer(1, 0.4 * cm))

    # Nombre del paciente
    nombre = paciente.get("name", "Paciente")
    story.append(Paragraph(nombre, styles["patient_name"]))

    # Datos del paciente
    edad = paciente.get("age")
    sexo = paciente.get("sex") or ""
    talla = paciente.get("height_cm")
    peso = pauta.get("peso_calculo") or paciente.get("weight_kg")

    datos_parts = []
    if edad:
        datos_parts.append(f"{edad} a\xf1os")
    if sexo:
        datos_parts.append(sexo)
    story.append(Paragraph(" \xb7 ".join(datos_parts), styles["patient_sub"]))

    medidas_parts = []
    if talla:
        medidas_parts.append(f"{_fmt(talla)} cm")
    if peso:
        medidas_parts.append(f"{_fmt(peso)} kg")
    if medidas_parts:
        story.append(Paragraph(" \xb7 ".join(medidas_parts), styles["patient_sub"]))

    story.append(Spacer(1, 0.5 * cm))

    # Fecha
    fecha_raw = pauta.get("fecha_creacion", datetime.now().strftime("%Y-%m-%d"))
    story.append(Paragraph(f"Fecha: {_fecha_es(fecha_raw)}", styles["cover_date"]))

    if pauta.get("nombre_pauta"):
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(pauta["nombre_pauta"], styles["patient_sub"]))

    story.append(Spacer(1, 0.8 * cm))
    # Línea naranja separadora
    story.append(HRFlowable(width=_CONTENT_W, thickness=3, color=ORANGE))
    story.append(PageBreak())


def _build_requerimientos(pauta: dict, paciente: dict, styles: dict, story: list):
    """Página — Requerimientos y macronutrientes."""
    FA_LABELS = {
        "sedentaria": "Sedentaria (0 hrs/sem)",
        "liviana":    "Liviana (3 hrs/sem)",
        "moderada":   "Moderada (6 hrs/sem)",
        "intensa":    "Intensa (4 hrs/d\xeda)",
    }
    fa_str = FA_LABELS.get(pauta.get("fa_key", ""), pauta.get("fa_key", "\u2014"))

    peso  = pauta.get("peso_calculo", 0) or 0
    talla = paciente.get("height_cm")
    talla_str = f"{_fmt(talla)} cm" if talla else "\u2014"

    # IMC
    imc_str = "\u2014"
    if talla and peso:
        try:
            imc = float(peso) / ((float(talla) / 100) ** 2)
            imc_str = f"{imc:.1f} kg/m\xb2"
        except Exception:
            pass

    banda = _section_band("REQUERIMIENTOS NUTRICIONALES", styles)

    tabla_req = [
        ["Variable", "Valor"],
        ["Peso utilizado", f"{_fmt(peso)} kg"],
        ["Talla", talla_str],
        ["IMC", imc_str],
        ["TMB (Oxford 2005)", f"{_fmt(pauta.get('tmb'))} kcal/d\xeda"],
        ["Factor de Actividad",
         f"{_fmt(pauta.get('fa'), 2)} \u2014 {fa_str}"],
        ["GET (Gasto Energ\xe9tico Total)", f"{_fmt(pauta.get('get'))} kcal/d\xeda"],
        ["kcal/kg",
         f"{_fmt(pauta.get('get', 0) / peso, 1) if peso else '\u2014'} kcal/kg"],
    ]

    t = Table(tabla_req, colWidths=[_CONTENT_W * 0.58, _CONTENT_W * 0.42])
    ts = _hdr_style()
    ts.add("ALIGN", (1, 1), (1, -1), "RIGHT")
    ts.add("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold")
    ts.add("FONTSIZE", (0, 1), (0, -1), 9)
    t.setStyle(ts)

    story.append(KeepTogether([banda, Spacer(1, 0.25 * cm), t]))
    story.append(Spacer(1, 0.6 * cm))

    # Tabla macros
    get_val = pauta.get("get") or 0
    prot_pct = pauta.get("prot_pct") or 0
    lip_pct  = pauta.get("lip_pct") or 0
    cho_pct  = round(100 - prot_pct - lip_pct, 1)

    banda2 = _section_band("DISTRIBUCIÓN DE MACRONUTRIENTES", styles)

    tabla_macros = [
        ["Macronutriente", "g/d\xeda", "kcal/d\xeda", "% VCT"],
        ["Prote\xednas",
         _fmt(pauta.get("prot_total_g")),
         _fmt(pauta.get("prot_total_kcal")),
         f"{_fmt(prot_pct)} %"],
        ["L\xedpidos",
         _fmt(pauta.get("lip_total_g")),
         _fmt(pauta.get("lip_total_kcal")),
         f"{_fmt(lip_pct)} %"],
        ["Carbohidratos",
         _fmt(pauta.get("cho_total_g")),
         _fmt(pauta.get("cho_total_kcal")),
         f"{_fmt(cho_pct)} %"],
        ["TOTAL", "\u2014", _fmt(get_val), "100 %"],
    ]

    col_w = [_CONTENT_W * 0.38, _CONTENT_W * 0.2,
             _CONTENT_W * 0.25, _CONTENT_W * 0.17]
    tm = Table(tabla_macros, colWidths=col_w)
    ts2 = _hdr_style()
    ts2.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
    ts2.add("BACKGROUND", (0, -1), (-1, -1), NAVY)
    ts2.add("TEXTCOLOR", (0, -1), (-1, -1), WHITE)
    tm.setStyle(ts2)

    nota = (f"CHO/kg: {_fmt(pauta.get('cho_g_kg'), 2)} g/kg  \xb7  "
            f"PROT/kg: {_fmt(pauta.get('prot_gr_kg'), 2)} g/kg")

    story.append(KeepTogether([banda2, Spacer(1, 0.25 * cm), tm,
                               Spacer(1, 0.2 * cm),
                               Paragraph(nota, styles["small"])]))
    story.append(PageBreak())


def _build_porciones(
    pauta: dict,
    porciones: dict,
    distribucion: dict,
    styles: dict,
    story: list
):
    """Página — Porciones del día y distribución por tiempo de comida."""

    def _f(v, dec=1):
        if v is None or v == 0:
            return "\u2014"
        return str(round(float(v), dec))

    # ── Tabla porciones totales del día ──────────────────────────────────
    banda_porc = _section_band("PORCIONES DIARIAS POR GRUPO", styles)

    grupos_con_porciones = [
        (g, p) for g, p in porciones.items() if p and float(p) > 0
    ]

    if grupos_con_porciones:
        hdr = ["Grupo de Alimento", "Porciones/d\xeda", "kcal", "CHO (g)", "LIP (g)", "PROT (g)"]
        rows = [hdr]
        total_kcal = total_cho = total_lip = total_prot = 0.0

        for grupo, prc in grupos_con_porciones:
            macros = GRUPOS_MACROS.get(grupo, {})
            k = macros.get("kcal", 0) * prc
            c = macros.get("cho", 0) * prc
            l = macros.get("lip", 0) * prc
            p = macros.get("prot", 0) * prc
            total_kcal += k
            total_cho  += c
            total_lip  += l
            total_prot += p
            nombre = NOMBRES_GRUPOS.get(grupo, grupo)
            rows.append([nombre, _f(prc, 2),
                         _f(k), _f(c), _f(l), _f(p)])

        rows.append([
            "TOTAL", "\u2014",
            _f(total_kcal), _f(total_cho),
            _f(total_lip), _f(total_prot)
        ])

        # Filas de requerimiento
        req_kcal = pauta.get("get") or 0
        req_cho  = pauta.get("cho_total_g") or 0
        req_lip  = pauta.get("lip_total_g") or 0
        req_prot = pauta.get("prot_total_g") or 0
        rows.append([
            "REQUERIMIENTO", "\u2014",
            _f(req_kcal), _f(req_cho), _f(req_lip), _f(req_prot)
        ])

        # Fila adecuación
        def _adec(real, req):
            if not req:
                return "\u2014"
            return f"{round((real / req) * 100, 0):.0f}%"

        rows.append([
            "% ADECUACI\xd3N", "\u2014",
            _adec(total_kcal, req_kcal),
            _adec(total_cho, req_cho),
            _adec(total_lip, req_lip),
            _adec(total_prot, req_prot),
        ])

        col_w = [
            _CONTENT_W * 0.30, _CONTENT_W * 0.13,
            _CONTENT_W * 0.14, _CONTENT_W * 0.14,
            _CONTENT_W * 0.14, _CONTENT_W * 0.15,
        ]
        tp = Table(rows, colWidths=col_w)
        ts = _hdr_style()
        n = len(rows)
        # TOTAL row navy
        ts.add("FONTNAME",   (0, n - 3), (-1, n - 3), "Helvetica-Bold")
        ts.add("BACKGROUND", (0, n - 3), (-1, n - 3), NAVY)
        ts.add("TEXTCOLOR",  (0, n - 3), (-1, n - 3), WHITE)
        # REQUERIMIENTO row
        ts.add("FONTNAME",   (0, n - 2), (-1, n - 2), "Helvetica-Bold")
        ts.add("BACKGROUND", (0, n - 2), (-1, n - 2), GRAY_LIGHT)
        ts.add("TEXTCOLOR",  (0, n - 2), (-1, n - 2), DARK)
        # % ADECUACIÓN row
        ts.add("FONTNAME",   (0, n - 1), (-1, n - 1), "Helvetica-Bold")
        ts.add("BACKGROUND", (0, n - 1), (-1, n - 1), NAVY_PALE)
        tp.setStyle(ts)

        story.append(KeepTogether([banda_porc, Spacer(1, 0.25 * cm), tp]))
    else:
        story.append(KeepTogether([
            banda_porc, Spacer(1, 0.2 * cm),
            Paragraph("Sin porciones asignadas.", styles["body"])
        ]))

    story.append(Spacer(1, 0.7 * cm))

    # ── Tabla de distribución por tiempo de comida ────────────────────────────
    banda_dist = _section_band("DISTRIBUCIÓN POR TIEMPO DE COMIDA", styles)

    tiempos_keys   = [t[0] for t in TIEMPOS_COMIDA]
    tiempos_labels = [t[1] for t in TIEMPOS_COMIDA]

    if grupos_con_porciones and distribucion:
        hdr_dist = ["Grupo"] + tiempos_labels
        rows_dist = [hdr_dist]

        for grupo, _ in grupos_con_porciones:
            nombre = NOMBRES_GRUPOS.get(grupo, grupo)
            row = [nombre]
            for tk in tiempos_keys:
                val = (distribucion.get(tk) or {}).get(grupo, 0) or 0
                row.append(_f(val, 2) if val else "\u2014")
            rows_dist.append(row)

        # Fila kcal por tiempo
        kcal_row = ["kcal"]
        for tk in tiempos_keys:
            grupos_tiempo = distribucion.get(tk, {})
            k = sum(
                (GRUPOS_MACROS.get(g, {}).get("kcal", 0) * (prc or 0))
                for g, prc in grupos_tiempo.items()
            )
            kcal_row.append(_f(k))
        rows_dist.append(kcal_row)

        # Fila %VCT
        total_dist_kcal = sum(
            GRUPOS_MACROS.get(g, {}).get("kcal", 0) * (prc or 0)
            for grupos in distribucion.values()
            for g, prc in grupos.items()
        )
        pct_row = ["%VCT"]
        for tk in tiempos_keys:
            grupos_tiempo = distribucion.get(tk, {})
            k = sum(
                (GRUPOS_MACROS.get(g, {}).get("kcal", 0) * (prc or 0))
                for g, prc in grupos_tiempo.items()
            )
            pct = round((k / total_dist_kcal) * 100, 1) if total_dist_kcal else 0
            pct_row.append(f"{pct}%")
        rows_dist.append(pct_row)

        n_cols  = len(hdr_dist)
        col_w_d = [_CONTENT_W * 0.26] + [_CONTENT_W * 0.74 / max(n_cols - 1, 1)] * (n_cols - 1)
        td = Table(rows_dist, colWidths=col_w_d)
        ts_d = _hdr_style()
        ts_d.add("FONTSIZE", (0, 0), (-1, 0), 8)
        ts_d.add("FONTSIZE", (0, 1), (-1, -1), 8)
        n_rows = len(rows_dist)
        ts_d.add("FONTNAME",   (0, n_rows - 2), (-1, n_rows - 1), "Helvetica-Bold")
        ts_d.add("BACKGROUND", (0, n_rows - 2), (-1, n_rows - 1), NAVY_PALE)
        td.setStyle(ts_d)

        story.append(KeepTogether([banda_dist, Spacer(1, 0.25 * cm), td]))
    else:
        story.append(KeepTogether([
            banda_dist, Spacer(1, 0.2 * cm),
            Paragraph("Sin distribuci\xf3n asignada.", styles["body"])
        ]))

    story.append(PageBreak())


def _build_equivalencias(pauta: dict, styles: dict, story: list):
    """Páginas finales — Tabla de equivalencias."""
    # Usar tabla_equivalencias guardada; si no, fallback a tipo_pauta
    tipo = pauta.get("tabla_equivalencias") or pauta.get("tipo_pauta", "omnivoro")
    import database.db_manager as db_mod
    tabla_bd = db_mod.eq_exportar_tabla(tipo)
    # tabla_bd es {nombre_grupo: ["gramaje — desc", ...]}; ya es el formato esperado
    tabla = tabla_bd if tabla_bd else None
    if not tabla:
        # Fallback al dict hardcodeado si la BD aún no tiene datos
        tabla = TABLAS_EQUIVALENCIAS.get(tipo)
    if not tabla:
        return

    tipo_label = NOMBRES_TIPOS_PAUTA.get(tipo, tipo).upper()

    banda = _section_band(
        f"EQUIVALENCIAS DE 1 PORCI\xd3N \u2014 {tipo_label}", styles)

    abrev = Paragraph(
        f"<i>{ABREVIATURAS}</i>",
        ParagraphStyle("PAb", fontSize=8, textColor=GRAY, fontName="Helvetica-Oblique",
                       alignment=TA_CENTER)
    )

    story.append(KeepTogether([banda, Spacer(1, 0.2 * cm), abrev,
                               Spacer(1, 0.3 * cm)]))

    for nombre_grupo, alimentos in tabla.items():
        # nombre_grupo ya es el nombre legible (clave del dict de BD o del hardcodeado)
        # Para el dict hardcodeado aplicamos la traducción; para el de BD ya es legible
        if nombre_grupo in NOMBRES_GRUPOS_EQUIV:
            nombre_grupo = NOMBRES_GRUPOS_EQUIV[nombre_grupo]
        nombre_grupo = nombre_grupo.upper()

        # Encabezado de grupo con fondo navy pale
        hdr_tbl = Table(
            [[Paragraph(nombre_grupo, styles["equiv_group"])]],
            colWidths=[_CONTENT_W]
        )
        hdr_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), NAVY_PALE),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))

        items_para = []
        for a in alimentos:
            items_para.append(
                Paragraph(
                    f'<font color="#E87722">\u2022</font> {a}',
                    styles["equiv_item"]
                )
            )

        block = KeepTogether(
            [hdr_tbl]
            + items_para
            + [Spacer(1, 0.25 * cm)]
        )
        story.append(block)


# ── Sección: Ejemplos de Menú ─────────────────────────────────────────────────

def _build_menu_ejemplos(menu: dict, styles: dict, story: list):
    """Construye la sección de ejemplos de menú para el PDF."""
    if not menu:
        return

    banda = _section_band("EJEMPLOS DE MEN\xdc", styles)
    story.append(banda)
    story.append(Spacer(1, 0.3 * cm))

    letras = {1: "A", 2: "B", 3: "C"}

    for tk_key, tl in TIEMPOS_COMIDA:
        opciones = menu.get(tk_key)
        if not opciones:
            continue

        tiempo_blocks = []

        # Encabezado del tiempo (navy)
        tiempo_hdr = Table(
            [[Paragraph(tl, styles["col_header"])]],
            colWidths=[_CONTENT_W]
        )
        tiempo_hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ]))
        tiempo_blocks.append(tiempo_hdr)
        tiempo_blocks.append(Spacer(1, 0.1 * cm))

        for opcion_num in sorted(opciones.keys()):
            datos  = opciones[opcion_num]
            alimentos = datos.get("alimentos", [])
            if not alimentos:
                continue
            letra = letras.get(opcion_num, str(opcion_num))
            nombre_opcion = datos.get("nombre_opcion", f"Opci\xf3n {letra}")

            op_label = Table(
                [[Paragraph(f"Opci\xf3n {letra}", styles["small_bold"])]],
                colWidths=[_CONTENT_W]
            )
            op_label.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), ORANGE_PALE),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 16),
            ]))
            tiempo_blocks.append(op_label)

            # Tabla de alimentos
            col_w = [_CONTENT_W * 0.40, _CONTENT_W * 0.14,
                     _CONTENT_W * 0.11, _CONTENT_W * 0.11,
                     _CONTENT_W * 0.13, _CONTENT_W * 0.11]
            tbl_data = [[
                Paragraph("Alimento",  styles["col_header"]),
                Paragraph("Cantidad",  styles["col_header"]),
                Paragraph("kcal",      styles["col_header"]),
                Paragraph("P (g)",     styles["col_header"]),
                Paragraph("C (g)",     styles["col_header"]),
                Paragraph("G (g)",     styles["col_header"]),
            ]]
            tot = {"kcal": 0.0, "prot": 0.0, "carb": 0.0, "grasa": 0.0}
            for i, alim in enumerate(alimentos):
                tbl_data.append([
                    Paragraph(alim.get("nombre", "\u2014"), styles["cell"]),
                    Paragraph(f"{alim.get('cantidad_g', 0):.0f} g", styles["cell_c"]),
                    Paragraph(f"{alim.get('kcal', 0):.1f}", styles["cell_c"]),
                    Paragraph(f"{alim.get('proteinas_g', 0):.1f}", styles["cell_c"]),
                    Paragraph(f"{alim.get('carbohidratos_g', 0):.1f}", styles["cell_c"]),
                    Paragraph(f"{alim.get('grasas_g', 0):.1f}", styles["cell_c"]),
                ])
                tot["kcal"]  += alim.get("kcal", 0) or 0
                tot["prot"]  += alim.get("proteinas_g", 0) or 0
                tot["carb"]  += alim.get("carbohidratos_g", 0) or 0
                tot["grasa"] += alim.get("grasas_g", 0) or 0

            tbl_data.append([
                Paragraph("TOTAL", styles["small_bold"]),
                Paragraph("", styles["cell_c"]),
                Paragraph(f"{tot['kcal']:.1f}", styles["small_bold"]),
                Paragraph(f"{tot['prot']:.1f}", styles["small_bold"]),
                Paragraph(f"{tot['carb']:.1f}", styles["small_bold"]),
                Paragraph(f"{tot['grasa']:.1f}", styles["small_bold"]),
            ])
            tbl = Table(tbl_data, colWidths=col_w)
            n = len(tbl_data)
            tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
                ("BACKGROUND",    (0, n - 1), (-1, n - 1), GRAY_LIGHT),
                ("FONTNAME",      (0, n - 1), (-1, n - 1), "Helvetica-Bold"),
                ("ROWBACKGROUNDS",(0, 1), (-1, n - 2), [WHITE, ROW_ALT]),
                ("GRID",          (0, 0), (-1, -1), 0.3, BORDER_CLR),
                ("TOPPADDING",    (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING",   (0, 0), (-1, -1), 5),
                ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ]))
            tiempo_blocks.append(tbl)
            tiempo_blocks.append(Spacer(1, 0.15 * cm))

        story.append(KeepTogether(tiempo_blocks))
        story.append(Spacer(1, 0.2 * cm))


# ── Función principal de exportación ─────────────────────────────────────────

def generar_pdf_pauta(
    output_path: str,
    paciente: dict,
    pauta: dict,
    porciones: dict,
    distribucion: dict,
    menu: Optional[dict] = None,
    opciones_pdf: Optional[dict] = None,
):
    """
    Genera el PDF completo de la pauta de alimentación.

    paciente:     dict con datos del paciente (name, sex, age, height_cm, photo_path)
    pauta:        dict con datos de la pauta (requerimientos + config)
    porciones:    {grupo: porciones_dia}
    distribucion: {tiempo: {grupo: porciones}}
    menu:         {tiempo: {opcion_num: {"nombre": str, "alimentos": [...]}}}
    opciones_pdf: dict con flags incluir_reqs/porciones/dist/equiv/menu
    """
    if opciones_pdf is None:
        opciones_pdf = {}
    incl_reqs      = opciones_pdf.get("incluir_reqs", True)
    incl_porciones = opciones_pdf.get("incluir_porciones", True)
    incl_dist      = opciones_pdf.get("incluir_dist", True)
    incl_equiv     = opciones_pdf.get("incluir_equiv",
                                      bool(pauta.get("incluir_equivalencias", 1)))
    incl_menu      = opciones_pdf.get("incluir_menu", True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=_MARGIN, rightMargin=_MARGIN,
        topMargin=_MARGIN, bottomMargin=_MARGIN + 0.8 * cm,
        title="Pauta de Alimentaci\xf3n",
        author="NutriApp"
    )

    styles = _styles()
    story  = []

    _build_portada(paciente, pauta, styles, story)

    if incl_reqs:
        _build_requerimientos(pauta, paciente, styles, story)

    if incl_porciones or incl_dist:
        _build_porciones(
            pauta, porciones,
            distribucion if incl_dist else {},
            styles, story
        )

    if incl_menu and menu:
        _build_menu_ejemplos(menu, styles, story)

    if incl_equiv:
        _build_equivalencias(pauta, styles, story)

    doc.build(story, onFirstPage=_footer_first, onLaterPages=_footer)
