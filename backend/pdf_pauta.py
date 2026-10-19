"""PDF de la pauta de alimentación para el paciente.

Sigue el diseño "Día a día" (Claude Design, Opción 1): encabezado con el
paciente, objetivo del plan, adecuación del plan, una tarjeta por comida con
dos opciones equivalentes, porciones por grupo, hidratación y notas.
"""
import base64
import io
import json
import os
from datetime import date as dt_date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable, Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from ai_service import NOMBRES_GRUPOS, TIEMPOS_COMIDA, TIPO_LABELS

# ── Paleta (diseño "fresco y natural") ──────────────────────────────────────
C_INK = HexColor("#1f3a2b")       # títulos
C_TEXT = HexColor("#33443a")      # cuerpo
C_MUTED = HexColor("#7b877f")
C_GREEN = HexColor("#3f6b52")     # primario
C_GREEN_SOFT = HexColor("#5f8f6f")
C_BAR = HexColor("#7fa58c")
C_TRACK = HexColor("#e4ebe5")
C_CARD_BG = HexColor("#f4f7f2")
C_CALLOUT_BG = HexColor("#eef4ec")
C_HYDRA_BG = HexColor("#e6f0e3")
C_BORDER = HexColor("#e2e8e1")
C_OPTION_BG = HexColor("#fbfcfa")
C_CHIP_BG = HexColor("#f0f3ec")
WHITE = colors.white

GROUP_COLORS = {
    "cereales": "#d1a04c", "verduras_cg": "#4f9a5f", "verduras_lc": "#8cc084",
    "frutas": "#e08a5a", "lacteos_ag": "#5b7fbf", "lacteos_mg": "#7a99cf",
    "lacteos_bg": "#9fb6dd", "legumbres": "#a8754f", "carnes_ag": "#b5574b",
    "carnes_bg": "#d07a6c", "otros_proteicos": "#c4677e", "aceite_grasas": "#c9a94a",
    "alim_ricos_lipidos": "#d08860", "leches_vegetales": "#8fb3a8", "lacteos_soya": "#6f8fc9",
    "semillas_chia": "#6b7a4f", "azucares": "#b9a3c9",
}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

# ── Tipografías: Quicksand/Nunito si están en assets/fonts, si no Helvetica ──
_FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")
_FONTS = {"head": "Helvetica-Bold", "body": "Helvetica", "bold": "Helvetica-Bold", "semi": "Helvetica-Bold"}


def _register_fonts():
    files = {"head": "Quicksand-Bold.ttf", "body": "Nunito-Regular.ttf",
             "bold": "Nunito-Bold.ttf", "semi": "Nunito-SemiBold.ttf"}
    for role, fname in files.items():
        path = os.path.join(_FONT_DIR, fname)
        if os.path.exists(path):
            name = fname.rsplit(".", 1)[0]
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, path))
            _FONTS[role] = name


_register_fonts()


# ── Formato chileno ─────────────────────────────────────────────────────────

def _num(v, d=0) -> str:
    """1925.4 → "1.925"; 22.34 (d=1) → "22,3"."""
    s = f"{float(v):,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _porc(v) -> str:
    v = float(v)
    return _num(v, 0) if v.is_integer() else _num(v, 1)


def _fecha_larga(iso) -> str:
    try:
        d = dt_date.fromisoformat(str(iso)[:10])
    except ValueError:
        return str(iso or "")
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def _load(raw, default):
    try:
        return json.loads(raw) if raw else default
    except (TypeError, ValueError):
        return default


# ── Flowables dibujados ─────────────────────────────────────────────────────

class _Checkbox(Flowable):
    """Casilla "Cumplí" para que el paciente marque la comida."""

    def __init__(self, label="Cumplí"):
        super().__init__()
        self.label = label
        self.width, self.height = 2.2 * cm, 0.75 * cm

    def draw(self):
        c = self.canv
        c.setStrokeColor(C_BORDER)
        c.setFillColor(WHITE)
        c.roundRect(0, 0, self.width, self.height, 9, stroke=1, fill=1)
        c.setStrokeColor(C_MUTED)
        c.roundRect(0.28 * cm, 0.2 * cm, 0.35 * cm, 0.35 * cm, 2, stroke=1, fill=0)
        c.setFillColor(C_INK)
        c.setFont(_FONTS["semi"], 8.5)
        c.drawString(0.8 * cm, 0.27 * cm, self.label)


class _Glasses(Flowable):
    """Vasos de agua para marcar."""

    def __init__(self, n=8):
        super().__init__()
        self.n = n
        self.width, self.height = n * 0.62 * cm, 0.75 * cm

    def draw(self):
        c = self.canv
        c.setStrokeColor(C_GREEN_SOFT)
        c.setLineWidth(0.8)
        c.setFillColor(WHITE)
        for i in range(self.n):
            c.roundRect(i * 0.62 * cm, 0, 0.44 * cm, self.height, 3, stroke=1, fill=1)


class _LeaderRow(Flowable):
    """"Alimento ······ 150 g" con la línea punteada entre nombre y cantidad."""

    def __init__(self, name, qty, width, size=8.5):
        super().__init__()
        self.name, self.qty, self.width, self.size = name, qty, width, size
        self.height = size * 1.75

    def draw(self):
        c = self.canv
        y = self.size * 0.45
        qty_w = pdfmetrics.stringWidth(self.qty, _FONTS["semi"], self.size)
        size = self.size
        while pdfmetrics.stringWidth(self.name, _FONTS["body"], size) > self.width - qty_w - 14 and size > 6.5:
            size -= 0.25
        name_w = pdfmetrics.stringWidth(self.name, _FONTS["body"], size)
        c.setFont(_FONTS["body"], size)
        c.setFillColor(C_TEXT)
        c.drawString(0, y, self.name)
        c.setFont(_FONTS["semi"], self.size)
        c.setFillColor(C_INK)
        c.drawRightString(self.width, y, self.qty)
        x0, x1 = name_w + 5, self.width - qty_w - 5
        if x1 > x0:
            c.setStrokeColor(HexColor("#c9d3ca"))
            c.setLineWidth(0.7)
            c.setDash(0.6, 2.2)
            c.line(x0, y + 1.2, x1, y + 1.2)
            c.setDash()


class _Bar(Flowable):
    def __init__(self, width, pct, color=C_BAR, height=4):
        super().__init__()
        self.width, self.height, self.pct, self.color = width, height, max(0.0, min(pct, 100.0)), color

    def draw(self):
        c = self.canv
        c.setFillColor(C_TRACK)
        c.roundRect(0, 0, self.width, self.height, self.height / 2, stroke=0, fill=1)
        if self.pct > 0:
            c.setFillColor(self.color)
            c.roundRect(0, 0, self.width * self.pct / 100, self.height, self.height / 2, stroke=0, fill=1)


class _Dot(Flowable):
    def __init__(self, color, size=5, square=False):
        super().__init__()
        self.color, self.size, self.square = HexColor(color), size, square
        self.width = self.height = size

    def draw(self):
        self.canv.setFillColor(self.color)
        if self.square:
            self.canv.roundRect(0, 0, self.size, self.size, 1.5, stroke=0, fill=1)
        else:
            self.canv.circle(self.size / 2, self.size / 2, self.size / 2, stroke=0, fill=1)


class _NumberBadge(Flowable):
    def __init__(self, n):
        super().__init__()
        self.n = n
        self.width = self.height = 0.75 * cm

    def draw(self):
        c = self.canv
        r = self.width / 2
        c.setFillColor(C_GREEN)
        c.circle(r, r, r, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(_FONTS["bold"], 10)
        c.drawCentredString(r, r - 3.5, str(self.n))


# ── Generador ───────────────────────────────────────────────────────────────

def generate_pauta_pdf(patient, pauta, nutritionist, grupos_macros) -> bytes:
    buf = io.BytesIO()
    page_w, _ = LETTER
    margin = 2.0 * cm
    W = page_w - 2 * margin - 12  # el Frame de ReportLab tiene 6 pt de padding por lado

    def S(name, size=9.5, color=C_TEXT, font="body", leading=None, align=TA_LEFT, **kw):
        return ParagraphStyle(name, fontName=_FONTS[font], fontSize=size, textColor=color,
                              leading=leading or size * 1.35, alignment=align, **kw)

    def P(text, style):
        return Paragraph(text, style)

    def plain_table(rows, widths, extra=(), **kw):
        t = Table(rows, colWidths=widths, hAlign="LEFT", **kw)
        t.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), *extra,
        ]))
        return t

    patient_name = escape(patient.name or "")
    profesional = escape(nutritionist.name or nutritionist.username or "")
    tipo_label = TIPO_LABELS.get(pauta.tipo_pauta, pauta.tipo_pauta or "")
    porciones = {g: float(p) for g, p in _load(pauta.porciones_json, {}).items() if float(p or 0) > 0}
    distribucion = _load(pauta.distribucion_json, {})
    menu = _load(pauta.menu_json, {})

    def aporte(grupos: dict, macro: str) -> float:
        return sum(grupos_macros.get(g, {}).get(macro, 0) * float(p or 0) for g, p in grupos.items())

    total_kcal = aporte(porciones, "kcal")
    story = []

    # ── 1. Encabezado ───────────────────────────────────────────────────────
    chip = plain_table([[_Dot("#4f9a5f"), P(escape(tipo_label), S("chip", 8.5, C_GREEN, "semi"))]],
                       [8, None], extra=[("LEFTPADDING", (1, 0), (1, 0), 4)])
    chip_box = Table([[chip]], colWidths=[len(tipo_label) * 5.2 + 26])
    chip_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_CALLOUT_BG), ("ROUNDEDCORNERS", [8, 8, 8, 8]),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    sub_txt = pauta.name or "Plan de alimentación"
    sub_w = min(pdfmetrics.stringWidth(sub_txt, _FONTS["body"], 10) + 4, W - 4 * cm)
    chip_w = len(tipo_label) * 5.2 + 26
    subtitle = plain_table(
        [[P(escape(sub_txt), S("sub", 10, C_MUTED)), P("•", S("dot", 10, HexColor("#b8c4ba"))), chip_box, ""]],
        [sub_w, 0.5 * cm, chip_w, max(W - sub_w - 0.5 * cm - chip_w, 0)])
    title_block = [
        P("PLAN DE ALIMENTACIÓN", S("eyebrow", 8, C_GREEN_SOFT, "bold", charSpace=1.4)),
        Spacer(1, 3),
        P(patient_name, S("name", 25, C_INK, "head", leading=30)),
        Spacer(1, 4),
    ]
    logo_cell = ""
    if getattr(nutritionist, "logo_base64", None):
        try:
            raw = nutritionist.logo_base64.split(",", 1)[-1]
            logo_cell = Image(io.BytesIO(base64.b64decode(raw)), width=2.8 * cm, height=1.6 * cm,
                              kind="proportional")
        except Exception:
            logo_cell = ""
    elif getattr(nutritionist, "clinic_name", None):
        logo_cell = P(escape(nutritionist.clinic_name), S("clinic", 9, C_GREEN, "semi", align=TA_RIGHT))
    head = plain_table([[title_block, logo_cell]], [W - 3.2 * cm, 3.2 * cm],
                       extra=[("VALIGN", (0, 0), (-1, -1), "TOP")])
    story += [head, subtitle, Spacer(1, 12)]

    # Línea + datos de consulta
    def meta(label, value):
        return [P(label, S("ml", 7.5, C_MUTED, "bold", charSpace=0.8)), Spacer(1, 2),
                P(value, S("mv", 10, C_INK, "semi"))]
    meta_row = plain_table([[meta("PACIENTE", patient_name),
                             meta("FECHA DE CONSULTA", _fecha_larga(pauta.date)),
                             meta("PROFESIONAL", profesional), ""]],
                           [3.9 * cm, 4.6 * cm, 4.6 * cm, W - 13.1 * cm],
                           extra=[("LINEABOVE", (0, 0), (-1, 0), 0.8, C_BORDER),
                                  ("TOPPADDING", (0, 0), (-1, -1), 12), ("VALIGN", (0, 0), (-1, -1), "TOP")])
    story += [meta_row, Spacer(1, 14)]

    # ── 2. Objetivo del plan ────────────────────────────────────────────────
    ajuste = float(pauta.ajuste_kcal or 0)
    if ajuste < 0:
        foco = f"con un déficit de {_num(-ajuste)} kcal respecto a tu gasto diario"
    elif ajuste > 0:
        foco = f"con un aporte extra de {_num(ajuste)} kcal sobre tu gasto diario"
    else:
        foco = "para mantener tu peso y composición corporal"
    objetivo = (f"Plan {tipo_label.lower()} de {_num(pauta.kcal_objetivo or 0)} kcal al día, "
                f"{foco}, cubriendo tus requerimientos de energía y proteínas.")
    callout = Table([[[P("OBJETIVO DEL PLAN", S("ol", 7.5, C_GREEN_SOFT, "bold", charSpace=1)),
                       Spacer(1, 3), P(objetivo, S("ot", 10.5, C_TEXT, leading=15))]]], colWidths=[W])
    callout.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_CALLOUT_BG), ("LINEBEFORE", (0, 0), (0, -1), 3, C_GREEN),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]), ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
    ]))
    story += [callout, Spacer(1, 12)]

    # ── 3. Adecuación del plan ──────────────────────────────────────────────
    if porciones:
        card_w = (W - 3 * 8) / 4
        metas = [
            ("Energía", total_kcal, pauta.kcal_objetivo, "kcal"),
            ("Carbohidratos", aporte(porciones, "cho"), pauta.cho_g, "g"),
            ("Lípidos", aporte(porciones, "lip"), pauta.lip_g, "g"),
            ("Proteínas", aporte(porciones, "prot"), pauta.prot_g, "g"),
        ]
        cards = []
        for label, plan, target, unit in metas:
            pct = (plan / float(target) * 100) if target else 0
            card = Table([[P(label, S("al", 8.5, C_TEXT, "semi"))],
                          [P(f"{_num(pct, 1 if pct < 100 else 0)}%", S("av", 17, C_INK, "head", leading=21))],
                          [_Bar(card_w - 20, pct, HexColor("#c98a6c") if pct > 110 else C_BAR)],
                          [P(f"{_num(plan)} {unit} / {_num(target or 0)} {unit}", S("as", 7, C_MUTED))]],
                         colWidths=[card_w])
            card.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER), ("ROUNDEDCORNERS", [6, 6, 6, 6]),
                ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, 0), 9), ("BOTTOMPADDING", (0, -1), (-1, -1), 9),
                ("TOPPADDING", (0, 2), (-1, 2), 4), ("BOTTOMPADDING", (0, 2), (-1, 2), 5),
            ]))
            cards.append(card)
        row = plain_table([[cards[0], "", cards[1], "", cards[2], "", cards[3]]],
                          [card_w, 8, card_w, 8, card_w, 8, card_w])
        story += [KeepTogether([row, Spacer(1, 4), P(
            "Adecuación = cuánto cubre tu plan respecto a tu requerimiento diario.", S("an", 7.5, C_MUTED))]),
            Spacer(1, 18)]

    # ── 4. Tu día a día ─────────────────────────────────────────────────────
    tiempos = [(k, l) for k, l in TIEMPOS_COMIDA
               if any(float(p or 0) > 0 for p in (distribucion.get(k) or {}).values()) or menu.get(k)]
    if tiempos:
        story += [P("Tu día a día", S("h2", 17, C_INK, "head", leading=22)), Spacer(1, 2),
                  P("Elige <b>una sola opción</b> en cada comida. Las dos opciones son equivalentes en tu plan.",
                    S("h2s", 9.5, C_MUTED)), Spacer(1, 10)]

    def option_box(n, items, width):
        inner = width - 18
        rows = [[P(f"OPCIÓN {n}", S("on", 7.5, C_GREEN_SOFT, "bold", charSpace=1))]]
        if isinstance(items, str):
            rows.append([P(escape(items), S("ostr", 8.5, C_TEXT))])
        else:
            for it in items or []:
                nombre = str(it.get("nombre") or it.get("alimento") or "")
                cant = it.get("cantidad")
                unidad = str(it.get("unidad") or it.get("medida") or "")
                qty = f"{_porc(cant)} {unidad}".strip() if isinstance(cant, (int, float)) else str(cant or "")
                rows.append([_LeaderRow(nombre, qty, inner)])
        if len(rows) == 1:
            rows.append([P("Sin alimentos definidos.", S("oe", 8.5, C_MUTED))])
        t = Table(rows, colWidths=[width], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_OPTION_BG), ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
            ("ROUNDEDCORNERS", [5, 5, 5, 5]),
            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        ]))
        return t

    for idx, (key, label) in enumerate(tiempos, start=1):
        grupos_t = {g: float(p) for g, p in (distribucion.get(key) or {}).items() if float(p or 0) > 0}
        kcal_t = aporte(grupos_t, "kcal")
        vct = kcal_t / total_kcal * 100 if total_kcal else 0
        sub = f"{_num(kcal_t)} kcal · {_num(vct, 1)}% VCT" if kcal_t else ""

        head_cells = plain_table(
            [[_NumberBadge(idx), [P(label, S("mt", 13, C_INK, "head", leading=16)),
                                  P(sub, S("ms", 8, C_MUTED))], _Checkbox()]],
            [1.05 * cm, None, 2.3 * cm], extra=[("LEFTPADDING", (1, 0), (1, 0), 6)])

        chips = []
        for g, p in grupos_t.items():
            chip = plain_table([[_Dot(GROUP_COLORS.get(g, "#9aa79f")),
                                 P(f"{escape(NOMBRES_GRUPOS.get(g, g))} {_porc(p)}", S("cp", 7.5, C_TEXT))]],
                               [7, None], extra=[("LEFTPADDING", (1, 0), (1, 0), 4)])
            w = 7 + 4 + pdfmetrics.stringWidth(f"{NOMBRES_GRUPOS.get(g, g)} {_porc(p)}", _FONTS["body"], 7.5) + 2
            box = Table([[chip]], colWidths=[w + 14])
            box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), C_CHIP_BG), ("ROUNDEDCORNERS", [7, 7, 7, 7]),
                ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ]))
            chips.append((box, w + 14))
        chip_rows, cur, cur_w = [], [], 0
        inner_w = W - 24
        for box, w in chips:
            if cur and cur_w + w + 5 > inner_w:
                chip_rows.append(cur)
                cur, cur_w = [], 0
            cur.append((box, w))
            cur_w += w + 5
        if cur:
            chip_rows.append(cur)
        chip_flows = []
        for r in chip_rows:
            cells, widths = [], []
            for box, w in r:
                cells += [box, ""]
                widths += [w, 5]
            chip_flows.append(plain_table([cells + [""]], widths + [None]))
            chip_flows.append(Spacer(1, 4))

        entry = menu.get(key) or {}
        opt_w = (inner_w - 8) / 2
        if entry.get("opcion1") or entry.get("opcion2"):
            options = plain_table([[option_box(1, entry.get("opcion1"), opt_w), "",
                                    option_box(2, entry.get("opcion2"), opt_w)]],
                                  [opt_w, 8, opt_w], extra=[("VALIGN", (0, 0), (-1, -1), "TOP")])
        else:
            options = P("Las opciones de menú para esta comida se definirán con tu nutricionista.",
                        S("nom", 8.5, C_MUTED))
        body = chip_flows + [Spacer(1, 2), options]
        receta = entry.get("receta")
        if isinstance(receta, dict) and receta.get("nombre"):
            body += [Spacer(1, 6), P(f"Receta sugerida: <b>{escape(receta['nombre'])}</b>",
                                     S("rec", 8.5, C_GREEN, "semi"))]

        card = Table([[head_cells], [body]], colWidths=[W])
        card.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER), ("ROUNDEDCORNERS", [8, 8, 8, 8]),
            ("BACKGROUND", (0, 0), (-1, 0), C_CARD_BG), ("LINEBELOW", (0, 0), (-1, 0), 0.6, C_BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, 0), 9), ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
            ("TOPPADDING", (0, 1), (-1, 1), 10), ("BOTTOMPADDING", (0, 1), (-1, 1), 12),
        ]))
        story += [KeepTogether([card]), Spacer(1, 10)]

    # ── 5. Porciones por grupo ──────────────────────────────────────────────
    if porciones:
        items = list(porciones.items())
        half = (len(items) + 1) // 2
        col_w = (W - 0.8 * cm) / 2

        def porc_row(g, p):
            return plain_table([[_Dot(GROUP_COLORS.get(g, "#9aa79f"), 6, square=True),
                                 P(escape(NOMBRES_GRUPOS.get(g, g)), S("pn", 9.5, C_TEXT)),
                                 P(f"<b>{_porc(p)}</b>", S("pv", 11, C_GREEN, "bold", align=TA_RIGHT)),
                                 P("porc.", S("pu", 7, C_MUTED)),
                                 P(f"{_num(grupos_macros.get(g, {}).get('kcal', 0) * p)} kcal",
                                   S("pk", 7, C_MUTED, align=TA_RIGHT))]],
                               [12, col_w - 12 - 1.0 * cm - 0.9 * cm - 1.5 * cm, 1.0 * cm, 0.9 * cm, 1.5 * cm],
                               extra=[("LEFTPADDING", (1, 0), (1, 0), 4), ("LEFTPADDING", (3, 0), (3, 0), 5),
                                      ("LINEBELOW", (0, 0), (-1, -1), 0.5, C_BORDER),
                                      ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)])
        left, right = items[:half], items[half:]
        rows = []
        for i in range(half):
            rows.append([porc_row(*left[i]), "", porc_row(*right[i]) if i < len(right) else ""])
        grid = plain_table(rows, [col_w, 0.8 * cm, col_w])
        story += [KeepTogether([
            Spacer(1, 6), P("Porciones por grupo", S("h2p", 17, C_INK, "head", leading=22)), Spacer(1, 2),
            P("Las porciones diarias que distribuimos entre tus comidas.", S("h2ps", 9.5, C_MUTED)),
            Spacer(1, 8), grid]), Spacer(1, 16)]

    # ── 6. Hidratación ──────────────────────────────────────────────────────
    hydra = Table([[[P("Hidratación", S("hy", 12, C_INK, "head", leading=15)),
                     P("Toma alrededor de 2 litros de agua al día — marca cada vaso.", S("hys", 8.5, C_MUTED))],
                    _Glasses(8)]], colWidths=[W - 5.4 * cm, 5.4 * cm])
    hydra.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_HYDRA_BG), ("ROUNDEDCORNERS", [8, 8, 8, 8]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 11), ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
    ]))

    # ── 7. Indicaciones del profesional + notas del paciente ────────────────
    tail = [hydra, Spacer(1, 14)]
    if pauta.notes:
        tail += [P("Indicaciones de tu nutricionista", S("ih", 11, C_INK, "head", leading=14)), Spacer(1, 4),
                 P(escape(pauta.notes).replace("\n", "<br/>"), S("ib", 9.5, C_TEXT, leading=14)),
                 Spacer(1, 12)]
    notes = Table([[""], [""], [""]], colWidths=[W], rowHeights=[0.75 * cm] * 3)
    notes.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER), ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("BACKGROUND", (0, 0), (-1, -1), C_OPTION_BG),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, C_BORDER),
    ]))
    tail += [P("Notas", S("nh", 11, C_INK, "head", leading=14)), Spacer(1, 5), notes]
    story.append(KeepTogether(tail))

    # ── Pie de página ───────────────────────────────────────────────────────
    left_txt = f"Nut. {nutritionist.name or nutritionist.username or ''} · {pauta.name or ''}"
    right_txt = f"Total distribuido del día · {_num(total_kcal)} kcal" if total_kcal else ""

    def footer(canvas, doc):
        canvas.saveState()
        y = 1.15 * cm
        canvas.setStrokeColor(C_BORDER)
        canvas.setLineWidth(0.6)
        x0, x1 = margin + 6, page_w - margin - 6
        canvas.line(x0, y + 0.42 * cm, x1, y + 0.42 * cm)
        canvas.setFont(_FONTS["body"], 7.5)
        canvas.setFillColor(C_MUTED)
        canvas.drawString(x0, y, left_txt)
        canvas.drawRightString(x1, y, f"{right_txt}   ·   Pág. {doc.page}" if right_txt
                               else f"Pág. {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=LETTER, leftMargin=margin, rightMargin=margin,
                            topMargin=1.8 * cm, bottomMargin=2.0 * cm,
                            title=f"Pauta de alimentación — {patient.name or ''}",
                            author=nutritionist.name or nutritionist.username or "NutriApp")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
