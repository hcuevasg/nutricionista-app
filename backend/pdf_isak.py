"""PDF del informe antropométrico ISAK 1 / ISAK 2 para el paciente.

Sigue el diseño de Claude Design ("Informe ISAK"), misma familia visual que la
pauta (pdf_pauta.py): resumen de la evaluación, indicadores clave con cambio
respecto a la evaluación anterior, composición corporal en 4 componentes,
pliegues, medidas, somatotipo, indicadores de salud, metas y notas.

Composición en 4 componentes (De Rose & Guimarães 1980):
- Masa grasa: % grasa de Durnin & Womersley + Siri (calculado al registrar)
- Masa ósea: Rocha (1975) = 3,02 · (talla² · biestiloideo · bicondíleo fémur · 400)^0,712
- Masa residual: Würch (1974) = 24,1% del peso en hombres, 20,9% en mujeres
- Masa muscular: peso − (grasa + ósea + residual)
Si faltan diámetros (biestiloideo y fémur) se informan 2 componentes.
"""
import io
from datetime import date as dt_date
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Circle, Line, Path, String
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    CondPageBreak, Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from pdf_pauta import (
    C_BAR, C_BORDER, C_CALLOUT_BG, C_CARD_BG, C_CHIP_BG, C_GREEN, C_GREEN_SOFT, C_INK, C_MUTED,
    C_OPTION_BG, C_TEXT, C_TRACK, MESES, WHITE, _FONTS, _LeaderRow, _fecha_larga, _num,
)

C_TERRA = HexColor("#c98a6c")
C_TERRA_BG = HexColor("#f6e7df")
C_AMBER = HexColor("#e2c77f")
C_AMBER_BG = HexColor("#f6edd3")
C_RED = HexColor("#e3a493")
C_OK_BG = HexColor("#e3eedf")
C_NEUTRAL_BG = HexColor("#eef0ec")
C_ENDO, C_ENDO_BG = HexColor("#9b6a3c"), HexColor("#f4e6d8")
C_MESO, C_MESO_BG = HexColor("#3f6b52"), HexColor("#3f6b52")
C_ECTO, C_ECTO_BG = HexColor("#4f6aa3"), HexColor("#e3e8f4")

COMP_COLORS = {"muscular": "#3f6b52", "residual": "#b7c9b1", "osea": "#c9b78c", "grasa": "#e08a5a",
               "libre": "#3f6b52"}

SKINFOLDS = [("Tríceps", "triceps_mm"), ("Subescapular", "subscapular_mm"), ("Bíceps", "biceps_mm"),
             ("Cresta ilíaca", "iliac_crest_mm"), ("Supraespinal", "supraspinal_mm"),
             ("Abdominal", "abdominal_mm"), ("Muslo medial", "medial_thigh_mm"),
             ("Pantorrilla máx.", "max_calf_mm")]
SKINFOLDS_ISAK2 = [("Pectoral", "pectoral_mm"), ("Axilar medio", "axillary_mm"),
                   ("Muslo anterior", "front_thigh_mm")]
PERIMS = [("Brazo relajado", "arm_relaxed_cm"), ("Brazo flexionado", "arm_contracted_cm"),
          ("Cintura", "waist_cm"), ("Cadera", "hip_glute_cm"), ("Muslo máximo", "thigh_max_cm"),
          ("Muslo medio", "thigh_mid_cm"), ("Pantorrilla", "calf_cm")]
PERIMS_ISAK2 = [("Cabeza", "head_cm"), ("Cuello", "neck_cm"), ("Tórax", "chest_cm"),
                ("Tobillo mínimo", "ankle_min_cm")]
LENGTHS = [("Acromial–radial", "acromion_radial_cm"), ("Radial–estiloidea", "radial_styloid_cm"),
           ("Altura ilioespinal", "iliospinal_height_cm"), ("Trocantérea–tibial lateral", "trochanter_tibial_cm"),
           ("Altura tibial lateral", "tibiale_height_cm"), ("Pie", "foot_length_cm")]
BREADTHS = [("Biacromial", "biacromial_cm"), ("Biiliocrestídeo", "biiliocrestal_cm"),
            ("Tórax transverso", "transv_chest_cm"), ("Tórax anteroposterior", "ap_chest_cm"),
            ("Húmero (biepicondilar)", "humerus_width_cm"), ("Muñeca (biestiloideo)", "wrist_cm"),
            ("Fémur (bicondilar)", "femur_width_cm"), ("Tobillo (bimaleolar)", "ankle_bimalleolar_cm")]

RANGE_MM = (2.0, 80.0)
RANGE_CM = (10.0, 200.0)


# ── Cálculos ────────────────────────────────────────────────────────────────

def is_male(sex) -> bool:
    s = (sex or "").strip().lower()
    return s in ("m", "hombre") or "masculino" in s


def age_at(birth_date, on_date):
    try:
        b = dt_date.fromisoformat(str(birth_date)[:10])
        d = dt_date.fromisoformat(str(on_date)[:10])
    except (TypeError, ValueError):
        return None
    return d.year - b.year - ((d.month, d.day) < (b.month, b.day))


def _f(ev, attr):
    v = getattr(ev, attr, None) if ev is not None else None
    return float(v) if v is not None else None


def composition_valid(ev) -> bool:
    fat, lean, w = _f(ev, "fat_mass_pct"), _f(ev, "lean_mass_kg"), _f(ev, "weight_kg")
    return fat is not None and 0 < fat < 70 and lean is not None and w and lean < w


def four_components(ev, male: bool):
    """Masa grasa, ósea, residual y muscular en kg, o None si faltan datos."""
    w, h = _f(ev, "weight_kg"), _f(ev, "height_cm")
    wrist, femur = _f(ev, "wrist_cm"), _f(ev, "femur_width_cm")
    if not (w and h and wrist and femur and composition_valid(ev)):
        return None
    fat = w * _f(ev, "fat_mass_pct") / 100
    bone = 3.02 * ((h / 100) ** 2 * (wrist / 100) * (femur / 100) * 400) ** 0.712
    residual = w * (0.241 if male else 0.209)
    muscle = w - fat - bone - residual
    if muscle <= 0:
        return None
    return {"muscular": muscle, "residual": residual, "osea": bone, "grasa": fat}


def sum8(ev):
    vals = [_f(ev, a) for _, a in SKINFOLDS]
    return sum(vals) if all(v is not None for v in vals) else None


def somatotype_category(endo, meso, ecto) -> str:
    """Categoría de Carter (13 categorías; componentes 'iguales' si difieren ≤ 0,5)."""
    e, m, c = endo, meso, ecto
    eq = lambda a, b: abs(a - b) <= 0.5  # noqa: E731
    if eq(e, m) and eq(m, c) and eq(e, c):
        return "Central"
    if e > m + 0.5 and e > c + 0.5:
        if eq(m, c):
            return "Endomorfo balanceado"
        return "Endomorfo mesomórfico" if m > c else "Endomorfo ectomórfico"
    if m > e + 0.5 and m > c + 0.5:
        if eq(e, c):
            return "Mesomorfo balanceado"
        return "Mesomorfo endomórfico" if e > c else "Mesomorfo ectomórfico"
    if c > e + 0.5 and c > m + 0.5:
        if eq(e, m):
            return "Ectomorfo balanceado"
        return "Ectomorfo mesomórfico" if m > e else "Ectomorfo endomórfico"
    if eq(e, m):
        return "Endomorfo-mesomorfo"
    if eq(m, c):
        return "Mesomorfo-ectomorfo"
    return "Endomorfo-ectomorfo"


def _rating(v):
    return "baja" if v < 2.75 else "moderada" if v < 5.25 else "alta" if v < 7.25 else "muy alta"


# ── Flowables ───────────────────────────────────────────────────────────────

class _StackBar(Flowable):
    def __init__(self, width, parts, height=12):
        super().__init__()
        self.width, self.height, self.parts = width, height, parts

    def draw(self):
        c = self.canv
        total = sum(v for _, v in self.parts) or 1
        x, gap = 0, 1.5
        r = self.height / 2
        for i, (color, v) in enumerate(self.parts):
            w = self.width * v / total
            c.setFillColor(HexColor(color))
            first, last = i == 0, i == len(self.parts) - 1
            if first or last:
                c.roundRect(x, 0, max(w - (0 if last else gap), 0.1), self.height, r, stroke=0, fill=1)
                if first and not last:
                    c.rect(x + r, 0, max(w - r - gap, 0), self.height, stroke=0, fill=1)
                if last and not first:
                    c.rect(x, 0, max(w - r, 0), self.height, stroke=0, fill=1)
            else:
                c.rect(x, 0, max(w - gap, 0.1), self.height, stroke=0, fill=1)
            x += w


class _FoldBar(Flowable):
    """Barra del pliegue con marca vertical en la medición anterior."""

    def __init__(self, width, value, prev, scale):
        super().__init__()
        self.width, self.height = width, 7
        self.value, self.prev, self.scale = value, prev, scale

    def draw(self):
        c = self.canv
        h = 4.5
        y = 1
        c.setFillColor(C_TRACK)
        c.roundRect(0, y, self.width, h, h / 2, stroke=0, fill=1)
        c.setFillColor(C_BAR)
        c.roundRect(0, y, self.width * min(self.value / self.scale, 1), h, h / 2, stroke=0, fill=1)
        if self.prev is not None:
            x = self.width * min(self.prev / self.scale, 1)
            c.setStrokeColor(HexColor("#a3aea6"))
            c.setLineWidth(1)
            c.line(x, -0.5, x, self.height)


class _RangeBar(Flowable):
    """Barra de rango con segmentos de color y un punto en el valor."""

    def __init__(self, width, segments, lo, hi, value):
        super().__init__()
        self.width, self.height = width, 10
        self.segments, self.lo, self.hi, self.value = segments, lo, hi, value

    def draw(self):
        c = self.canv
        span = self.hi - self.lo
        y, h = 3, 4
        for a, b, color in self.segments:
            x0 = self.width * (a - self.lo) / span
            x1 = self.width * (b - self.lo) / span
            c.setFillColor(color)
            c.roundRect(x0, y, max(x1 - x0 - 1.5, 0.1), h, 2, stroke=0, fill=1)
        x = self.width * (min(max(self.value, self.lo), self.hi) - self.lo) / span
        c.setFillColor(WHITE)
        c.setStrokeColor(C_INK)
        c.setLineWidth(1)
        c.circle(x, y + h / 2, 4.5, stroke=1, fill=1)
        c.setFillColor(C_INK)
        c.circle(x, y + h / 2, 2.6, stroke=0, fill=1)


class _SmallBox(Flowable):
    def __init__(self, size=9):
        super().__init__()
        self.width = self.height = size

    def draw(self):
        self.canv.setStrokeColor(C_GREEN)
        self.canv.setLineWidth(1)
        self.canv.roundRect(0, 0, self.width, self.height, 2, stroke=1, fill=0)


def _somatochart(points, size=5.2 * cm):
    """Somatocarta Heath-Carter: X = ecto − endo, Y = 2·meso − (endo + ecto)."""
    d = Drawing(size, size * 1.05)
    xmin, xmax, ymin, ymax = -9.0, 9.0, -9.0, 15.0

    def tx(x):
        return (x - xmin) / (xmax - xmin) * size

    def ty(y):
        return (y - ymin) / (ymax - ymin) * size * 0.92 + size * 0.1

    E, M, C = (-7.5, -6.0), (0.0, 13.0), (7.5, -6.0)
    p = Path(fillColor=HexColor("#f4f7f1"), strokeColor=HexColor("#c8d3c6"), strokeWidth=0.8)
    p.moveTo(tx(E[0]), ty(E[1]))
    p.curveTo(tx(-6.5), ty(5.5), tx(-3.0), ty(11.0), tx(M[0]), ty(M[1]))
    p.curveTo(tx(3.0), ty(11.0), tx(6.5), ty(5.5), tx(C[0]), ty(C[1]))
    p.curveTo(tx(3.0), ty(-8.0), tx(-3.0), ty(-8.0), tx(E[0]), ty(E[1]))
    p.closePath()
    d.add(p)
    for v in (E, M, C):
        d.add(Line(tx(0), ty(0), tx(v[0]), ty(v[1]), strokeColor=HexColor("#dde4db"), strokeWidth=0.7))
    font = _FONTS["bold"]
    d.add(String(tx(0), ty(M[1]) + 7, "MESOMORFIA", fontName=font, fontSize=6.5,
                 fillColor=C_GREEN, textAnchor="middle"))
    d.add(String(tx(E[0]) + 6, 2, "ENDOMORFIA", fontName=font, fontSize=6.5, fillColor=C_ENDO,
                 textAnchor="start"))
    d.add(String(tx(C[0]) - 6, 2, "ECTOMORFIA", fontName=font, fontSize=6.5, fillColor=C_ECTO,
                 textAnchor="end"))
    for i, (endo, meso, ecto) in enumerate(points):
        x, y = ecto - endo, 2 * meso - (endo + ecto)
        current = i == len(points) - 1
        if current:
            d.add(Circle(tx(x), ty(y), 4.2, fillColor=C_GREEN, strokeColor=WHITE, strokeWidth=1))
        else:
            d.add(Circle(tx(x), ty(y), 3.2, fillColor=WHITE, strokeColor=HexColor("#a3aea6"), strokeWidth=1))
    return d


# ── Generador ───────────────────────────────────────────────────────────────

def generate_isak_pdf(patient, ev, nutritionist, prev=None, eval_number=None) -> bytes:
    buf = io.BytesIO()
    page_w, _ = LETTER
    margin = 2.0 * cm
    W = page_w - 2 * margin - 12

    def S(name, size=9.5, color=C_TEXT, font="body", leading=None, align=TA_LEFT, **kw):
        return ParagraphStyle(name, fontName=_FONTS[font], fontSize=size, textColor=color,
                              leading=leading or size * 1.35, alignment=align, **kw)

    P = Paragraph

    def plain(rows, widths, extra=(), **kw):
        t = Table(rows, colWidths=widths, hAlign="LEFT", **kw)
        t.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), *extra,
        ]))
        return t

    def card(content, width, pad=12, bg=WHITE, extra=()):
        t = Table([[content]], colWidths=[width], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER),
            ("ROUNDEDCORNERS", [7, 7, 7, 7]),
            ("LEFTPADDING", (0, 0), (-1, -1), pad), ("RIGHTPADDING", (0, 0), (-1, -1), pad),
            ("TOPPADDING", (0, 0), (-1, -1), pad - 2), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
            *extra,
        ]))
        return t

    def chip(text, bg=C_NEUTRAL_BG, color=C_TEXT, size=7.5):
        from reportlab.pdfbase import pdfmetrics
        w = pdfmetrics.stringWidth(text, _FONTS["semi"], size) + 12
        t = Table([[P(escape(text), S("chip", size, color, "semi", align=TA_CENTER))]], colWidths=[w])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg), ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return t

    def section_title(title, subtitle=None):
        out = [P(title, S("st", 16, C_INK, "head", leading=20))]
        if subtitle:
            out += [Spacer(1, 1), P(subtitle, S("ss", 9, C_MUTED))]
        return out + [Spacer(1, 8)]

    male = is_male(patient.sex)
    level2 = (ev.isak_level or "").upper().replace(" ", "") == "ISAK2"
    age = age_at(patient.birth_date, ev.date) or getattr(patient, "age", None)
    prev_label = None
    if prev is not None:
        try:
            prev_label = MESES[dt_date.fromisoformat(str(prev.date)[:10]).month - 1]
        except ValueError:
            prev_label = "anterior"

    def delta(cur, old, d=1, unit=""):
        if cur is None or old is None:
            return None
        diff = cur - old
        if abs(diff) < 0.05:
            return "= " + unit if unit else "="
        return f"{'+' if diff > 0 else '−'}{_num(abs(diff), d)}" + (f" {unit}" if unit else "")

    def delta_chip(cur, old, d=1, unit="", better="down", suffix=True):
        txt = delta(cur, old, d, unit)
        if txt is None:
            return ""
        if suffix and prev_label:
            txt = f"{txt} vs. {prev_label}"
        diff = cur - old
        if abs(diff) < 0.05 or better is None:
            bg, fg = C_NEUTRAL_BG, C_MUTED
        elif (diff < 0) == (better == "down"):
            bg, fg = C_OK_BG, C_GREEN
        else:
            bg, fg = C_TERRA_BG, HexColor("#9a5a3f")
        return chip(txt, bg, fg)

    # Validación de datos
    comp_ok = composition_valid(ev)
    suspicious = {n for n, a in SKINFOLDS + SKINFOLDS_ISAK2 if _f(ev, a) is not None
                  and not RANGE_MM[0] <= _f(ev, a) <= RANGE_MM[1]}
    suspicious |= {n for n, a in PERIMS + PERIMS_ISAK2 if _f(ev, a) is not None
                   and not RANGE_CM[0] <= _f(ev, a) <= RANGE_CM[1]}

    w, h = _f(ev, "weight_kg"), _f(ev, "height_cm")
    bmi = w / (h / 100) ** 2 if w and h else None
    prev_bmi = None
    if prev is not None and _f(prev, "weight_kg") and _f(prev, "height_cm"):
        prev_bmi = _f(prev, "weight_kg") / (_f(prev, "height_cm") / 100) ** 2
    comps = four_components(ev, male)
    prev_comps = four_components(prev, male) if prev is not None else None
    prev_ok = prev is not None and composition_valid(prev)

    story = []

    # ── 1. Encabezado ───────────────────────────────────────────────────────
    nivel = "ISAK 2 · Perfil completo" if level2 else "ISAK 1 · Perfil restringido"
    clinic = getattr(nutritionist, "clinic_name", None)
    head = plain([[[P("EVALUACIÓN ANTROPOMÉTRICA", S("eb", 8, C_GREEN_SOFT, "bold", charSpace=1.4)),
                    Spacer(1, 3), P(escape(patient.name or ""), S("nm", 25, C_INK, "head", leading=30)),
                    Spacer(1, 3)],
                   P(escape(clinic), S("cl", 9, C_GREEN, "semi", align=TA_RIGHT)) if clinic else ""]],
                 [W - 4 * cm, 4 * cm], extra=[("VALIGN", (0, 0), (-1, -1), "TOP")])
    from reportlab.pdfbase import pdfmetrics
    sub = "Informe de composición corporal"
    sub_w = pdfmetrics.stringWidth(sub, _FONTS["body"], 10) + 4
    lvl_chip = chip(nivel, C_CALLOUT_BG, C_GREEN, 8.5)
    story += [head, plain([[P(sub, S("sb", 10, C_MUTED)), P("•", S("dt", 10, HexColor("#b8c4ba"))),
                            lvl_chip, ""]], [sub_w, 0.5 * cm, lvl_chip._colWidths[0],
                                              max(W - sub_w - 0.5 * cm - lvl_chip._colWidths[0], 0)]),
              Spacer(1, 12)]

    def meta(label, value):
        return [P(label, S("ml", 7.5, C_MUTED, "bold", charSpace=0.8)), Spacer(1, 2),
                P(value, S("mv", 10, C_INK, "semi"))]
    eval_txt = f"N° {eval_number}" if eval_number else "—"
    if prev is not None:
        eval_txt += f" · anterior {_fecha_larga(prev.date).replace(' de ', ' ', 1)}"
    edad_sexo = (f"{age} años · " if age else "") + ("Masculino" if male else "Femenino")
    prof = escape(nutritionist.name or nutritionist.username or "")
    story += [plain([[meta("FECHA DE EVALUACIÓN", _fecha_larga(ev.date)), meta("EDAD · SEXO", edad_sexo),
                      meta("EVALUACIÓN", eval_txt), meta("ANTROPOMETRISTA", prof)]],
                    [W * 0.25, W * 0.22, W * 0.31, W * 0.22],
                    extra=[("LINEABOVE", (0, 0), (-1, 0), 0.8, C_BORDER),
                           ("TOPPADDING", (0, 0), (-1, -1), 12), ("VALIGN", (0, 0), (-1, -1), "TOP")]),
              Spacer(1, 14)]

    # ── 2. Resumen ──────────────────────────────────────────────────────────
    s6, ps6 = _f(ev, "sum_6_skinfolds"), _f(prev, "sum_6_skinfolds")
    sentences = []
    if prev is not None:
        changes = []
        if s6 is not None and ps6 is not None and abs(s6 - ps6) >= 0.1:
            changes.append(f"{'bajaste' if s6 < ps6 else 'subiste'} {_num(abs(s6 - ps6), 1)} mm "
                           f"en la suma de 6 pliegues")
        if comp_ok and prev_ok:
            changes.append(f"tu grasa corporal pasó de {_num(_f(prev, 'fat_mass_pct'), 1)}% a "
                           f"{_num(_f(ev, 'fat_mass_pct'), 1)}%")
        if comps and prev_comps:
            dm = comps["muscular"] - prev_comps["muscular"]
            changes.append("tu masa muscular se mantuvo" if abs(dm) < 0.3 else
                           f"tu masa muscular {'aumentó' if dm > 0 else 'disminuyó'} {_num(abs(dm), 1)} kg")
        if changes:
            joined = ", ".join(changes[:-1]) + (" y " if len(changes) > 1 else "") + changes[-1]
            sentences.append(f"Desde {prev_label} {joined}.")
    else:
        sentences.append("Esta es tu evaluación inicial: servirá como punto de partida para comparar "
                         "tus próximos controles.")
    warning = ""
    if suspicious:
        warning = ("Revisar mediciones: valores fuera de rango fisiológico en "
                   + ", ".join(sorted(suspicious)[:6]) + (" y otros" if len(suspicious) > 6 else "") + ".")
    if not comp_ok and ev.fat_mass_pct is not None:
        warning += (" " if warning else "") + "La composición corporal calculada no es válida y no se informa."
    summary = [P("RESUMEN DE TU EVALUACIÓN", S("rl", 7.5, C_GREEN_SOFT, "bold", charSpace=1)), Spacer(1, 3),
               P(" ".join(sentences), S("rt", 10.5, C_TEXT, leading=15))]
    if warning:
        summary += [Spacer(1, 4), P(f"* {warning}", S("rw", 8.5, HexColor("#9a5a3f"), "semi", leading=12))]
    callout = Table([[summary]], colWidths=[W], hAlign="LEFT")
    callout.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_CALLOUT_BG), ("LINEBEFORE", (0, 0), (0, -1), 3, C_GREEN),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]), ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
    ]))
    story += [callout, Spacer(1, 12)]

    # ── 3. Indicadores clave ────────────────────────────────────────────────
    cw = (W - 3 * 8) / 4

    def kpi(label, value, unit, chip_flow):
        rows = [[P(label, S("kl", 8.5, C_TEXT, "semi"))],
                [P(f'{value} <font size="8.5" color="#7b877f">{unit}</font>' if value != "—" else "—",
                   S("kv", 18, C_INK, "head", leading=22))],
                [chip_flow or Spacer(1, 12)]]
        t = Table(rows, colWidths=[cw])
        t.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER), ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("TOPPADDING", (0, 0), (-1, 0), 9), ("BOTTOMPADDING", (0, -1), (-1, -1), 9),
            ("TOPPADDING", (0, 2), (-1, 2), 4),
        ]))
        return t
    kpis = [
        kpi("Peso", _num(w, 1) if w else "—", "kg", delta_chip(w, _f(prev, "weight_kg"), better=None)),
        kpi("IMC", _num(bmi, 1) if bmi else "—", "kg/m²", delta_chip(bmi, prev_bmi, better=None)),
        kpi("Grasa corporal", _num(_f(ev, "fat_mass_pct"), 1) if comp_ok else "—", "%",
            delta_chip(_f(ev, "fat_mass_pct"), _f(prev, "fat_mass_pct")) if comp_ok and prev_ok else ""),
        kpi("Σ 6 pliegues", _num(s6, 1) if s6 else "—", "mm", delta_chip(s6, ps6) if s6 else ""),
    ]
    story += [plain([[kpis[0], "", kpis[1], "", kpis[2], "", kpis[3]]], [cw, 8, cw, 8, cw, 8, cw]),
              Spacer(1, 20)]

    # ── 4. Composición corporal ─────────────────────────────────────────────
    if comp_ok:
        if comps:
            parts = [("Masa muscular", "muscular"), ("Masa residual", "residual"), ("Masa ósea", "osea"),
                     ("Masa grasa", "grasa")]
            values = comps
            subtitle = f"Cómo se reparten tus {_num(w, 1)} kg en cuatro componentes."
            prev_vals = prev_comps
        else:
            lean = _f(ev, "lean_mass_kg")
            values = {"libre": lean, "grasa": w - lean}
            parts = [("Masa libre de grasa", "libre"), ("Masa grasa", "grasa")]
            subtitle = (f"Cómo se reparten tus {_num(w, 1)} kg. Con diámetros de muñeca y fémur se "
                        f"informan cuatro componentes.")
            prev_vals = None
            if prev_ok:
                pl = _f(prev, "lean_mass_kg")
                prev_vals = {"libre": pl, "grasa": _f(prev, "weight_kg") - pl}
        inner = W - 28
        rows = [[_StackBar(inner, [(COMP_COLORS[k], values[k]) for _, k in parts])]]
        for name, k in parts:
            pct = values[k] / w * 100
            rows.append([plain([[
                _swatch(COMP_COLORS[k]), P(name, S("cn", 9.5, C_TEXT)),
                P(f"<b>{_num(values[k], 1)} kg</b>", S("cv", 10.5, C_INK, "bold", align=TA_RIGHT)),
                P(f"{_num(pct, 1)}%", S("cp", 8.5, C_MUTED, align=TA_RIGHT)),
                delta_chip(values[k], prev_vals[k], unit="kg", suffix=False,
                           better="up" if k in ("muscular", "libre") else ("down" if k == "grasa" else None))
                if prev_vals else "",
            ]], [14, inner - 14 - 2.4 * cm - 1.6 * cm - 2.0 * cm, 2.4 * cm, 1.6 * cm, 2.0 * cm],
                extra=[("LEFTPADDING", (1, 0), (1, 0), 4), ("ALIGN", (4, 0), (4, 0), "RIGHT"),
                       ("LINEBELOW", (0, 0), (-1, -1), 0.5, C_BORDER),
                       ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)])])
        comp_table = Table(rows, colWidths=[inner], hAlign="LEFT")
        comp_table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8)]))
        foot = []
        if comps and _f(ev, "lean_mass_kg"):
            foot = [Spacer(1, 6), P(f"Índice músculo / óseo <b>{_num(comps['muscular'] / comps['osea'], 2)}</b>"
                                    "  ·  Grasa: Durnin & Womersley + Siri · Ósea: Rocha · Residual: Würch",
                                    S("cf", 7.5, C_MUTED))]
        story.append(KeepTogether(section_title("Composición corporal", subtitle)
                                  + [card([comp_table] + foot, W, 14), Spacer(1, 20)]))

    # ── 5. Pliegues cutáneos ────────────────────────────────────────────────
    folds = SKINFOLDS + (SKINFOLDS_ISAK2 if level2 else [])
    fold_rows = [(n, _f(ev, a), _f(prev, a)) for n, a in folds if _f(ev, a) is not None]
    if fold_rows:
        inner = W - 24
        has_prev = prev is not None and any(p is not None for _, _, p in fold_rows)
        # (la tabla lleva su propio borde; inner es el ancho útil sin el padding lateral)
        scale = max(30.0, max(v for _, v, _ in fold_rows) * 1.15)
        cols = [3.4 * cm, None, 1.4 * cm] + ([1.4 * cm, 1.6 * cm] if has_prev else [])
        fixed = sum(c for c in cols if c)
        cols[1] = inner - fixed
        hdr = [P("PLIEGUE", S("ph", 7.5, C_GREEN_SOFT, "bold", charSpace=0.8)), "",
               P("HOY", S("ph2", 7.5, C_GREEN_SOFT, "bold", align=TA_RIGHT))]
        if has_prev:
            hdr += [P((prev_label or "ANTERIOR").upper(), S("ph3", 7.5, C_GREEN_SOFT, "bold", align=TA_RIGHT)),
                    P("CAMBIO", S("ph4", 7.5, C_GREEN_SOFT, "bold", align=TA_RIGHT))]
        data = [hdr]
        for n, v, p in fold_rows:
            flag = n in suspicious
            row = [P(n, S("fn", 9.5, C_TEXT)), _FoldBar(cols[1] - 16, v, p, scale),
                   P(f"<b>{_num(v, 1)}</b>{' *' if flag else ''}",
                     S("fv", 10, HexColor("#9a5a3f") if flag else C_INK, "bold", align=TA_RIGHT))]
            if has_prev:
                row += [P(_num(p, 1) if p is not None else "—", S("fp", 9, C_MUTED, align=TA_RIGHT)),
                        delta_chip(v, p, suffix=False) if p is not None else ""]
            data.append(row)
        cols[0] += 12
        cols[-1] += 12
        t = Table(data, colWidths=cols, hAlign="LEFT", repeatRows=1)
        st = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
              ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 4.5),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5), ("LEFTPADDING", (1, 0), (1, -1), 8),
              ("LEFTPADDING", (0, 0), (0, -1), 12), ("RIGHTPADDING", (-1, 0), (-1, -1), 12),
              ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER), ("ROUNDEDCORNERS", [7, 7, 7, 7]),
              ("BACKGROUND", (0, 0), (-1, 0), C_CARD_BG),
              ("LINEBELOW", (0, 1), (-1, -2), 0.5, C_BORDER), ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
              ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
              ("LINEBELOW", (0, 0), (-1, 0), 0.6, C_BORDER), ("BOTTOMPADDING", (0, -1), (-1, -1), 8)]
        t.setStyle(TableStyle(st))
        s8, ps8 = sum8(ev), sum8(prev) if prev is not None else None
        totals = []
        for label, cur, old in (("Σ 6 pliegues", s6, ps6), ("Σ 8 pliegues", s8, ps8)):
            if cur is None:
                continue
            totals.append(plain([[P(f"<b>{label}</b>", S("tl", 9, C_INK, "semi")),
                                  P(f'{_num(cur, 1)} <font size="7.5" color="#7b877f">mm</font>',
                                    S("tv", 14, C_GREEN, "head", align=TA_RIGHT)),
                                  delta_chip(cur, old, suffix=False) if old is not None else ""]],
                                [None, 2.6 * cm, 1.6 * cm],
                                extra=[("LEFTPADDING", (2, 0), (2, 0), 6)]))
        body = [t]
        if totals:
            half = (W - 10) / 2
            row = [[totals[0], "", totals[1] if len(totals) > 1 else ""]]
            tt = Table(row, colWidths=[half, 10, half], hAlign="LEFT")
            tt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), C_CARD_BG), ("LINEAFTER", (0, 0), (0, 0), 0.5, C_BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("ROUNDEDCORNERS", [5, 5, 5, 5]),
            ]))
            body += [Spacer(1, 8), tt]
        n_folds = len(fold_rows)
        sub = f"El grosor de la grasa bajo la piel en {n_folds} puntos. Menos milímetros, menos grasa subcutánea."
        note = [Spacer(1, 4), P(f"La línea vertical marca tu medición de {prev_label}.", S("fl", 7.5, C_MUTED))] \
            if has_prev else []
        story += [CondPageBreak(7 * cm)] + section_title("Pliegues cutáneos", sub) + body + note \
            + [Spacer(1, 20)]

    # ── 6. Medidas ──────────────────────────────────────────────────────────
    def measure_box(title, items, width, unit="cm"):
        dcol = 1.1 * cm
        rows = [[P(title, S("mt", 7.5, C_GREEN_SOFT, "bold", charSpace=0.8)), ""]]
        for name, attr, u, d in items:
            v = _f(ev, attr)
            if v is None:
                continue
            p = _f(prev, attr)
            dtxt = delta(v, p, 1) if p is not None else ""
            rows.append([_LeaderRow(name, f"{_num(v, d)} {u}", width - dcol - 10 - 6),
                         P(dtxt or "", S("md", 7.5, C_MUTED, align=TA_RIGHT))])
        if len(rows) == 1:
            return None
        t = Table(rows, colWidths=[width - dcol, dcol], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_OPTION_BG), ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
            ("ROUNDEDCORNERS", [5, 5, 5, 5]), ("SPAN", (0, 0), (-1, 0)), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (1, 0), (1, -1), 0), ("RIGHTPADDING", (1, 0), (1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        ]))
        return t

    half = (W - 10) / 2
    basics = [("Peso", "weight_kg", "kg", 1), ("Talla", "height_cm", "cm", 1),
              ("Envergadura", "arm_span_cm", "cm", 1)]
    perims = [(n, a, "cm", 1) for n, a in PERIMS + (PERIMS_ISAK2 if level2 else [])]
    breadths = [(n, a, "cm", 1) for n, a in BREADTHS]
    lengths = [(n, a, "cm", 1) for n, a in LENGTHS]
    left = [b for b in (measure_box("BÁSICAS", basics, half),
                        measure_box("DIÁMETROS ÓSEOS", breadths, half)) if b]
    right = [b for b in (measure_box("PERÍMETROS", perims, half),
                         measure_box("LONGITUDES Y ALTURAS", lengths, half) if level2 else None) if b]
    if left or right:
        n = max(len(left), len(right))
        rows = [[left[i] if i < len(left) else "", "", right[i] if i < len(right) else ""] for i in range(n)]
        grid = plain(rows, [half, 10, half], extra=[("VALIGN", (0, 0), (-1, -1), "TOP"),
                                                   ("BOTTOMPADDING", (0, 0), (-1, -2), 8)])
        sub = ("Las medidas tomadas en tu evaluación (los pliegues se detallan arriba)." if level2
               else "Medidas básicas, perímetros y diámetros óseos.")
        story += [CondPageBreak(7 * cm)] + section_title("Medidas del perfil completo" if level2 else "Medidas",
                                                         sub) + [grid, Spacer(1, 20)]

    # ── 7. Somatotipo ───────────────────────────────────────────────────────
    endo, meso, ecto = _f(ev, "somatotype_endo"), _f(ev, "somatotype_meso"), _f(ev, "somatotype_ecto")
    if None not in (endo, meso, ecto):
        pendo, pmeso, pecto = (_f(prev, "somatotype_endo"), _f(prev, "somatotype_meso"),
                               _f(prev, "somatotype_ecto"))
        has_prev_soma = None not in (pendo, pmeso, pecto) and prev is not None

        def comp_row(val, pval, name, desc, fg, bg, txt_color):
            badge = Table([[P(f"<b>{_num(val, 1)}</b>", S("sb", 11, txt_color, "bold", align=TA_CENTER))]],
                          colWidths=[1.15 * cm], rowHeights=[0.9 * cm])
            badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("ROUNDEDCORNERS", [6, 6, 6, 6]),
                                       ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
            return plain([[badge, [P(f"<b>{name}</b>", S("sn", 10, C_INK, "semi")), P(desc, S("sd", 8, C_MUTED))],
                           P(f"{prev_label} {_num(pval, 1)}" if has_prev_soma else "",
                             S("sp", 7.5, C_MUTED, align=TA_RIGHT))]],
                         [1.35 * cm, 6.2 * cm, 1.8 * cm], extra=[("LEFTPADDING", (1, 0), (1, 0), 6),
                                                          ("BOTTOMPADDING", (0, 0), (-1, -1), 6)])
        left_w = W - 28 - 5.6 * cm
        rows_left = [
            P("CLASIFICACIÓN", S("sc", 7.5, C_GREEN_SOFT, "bold", charSpace=0.8)), Spacer(1, 2),
            P(somatotype_category(endo, meso, ecto), S("sct", 15, C_INK, "head", leading=19)),
            P(f"{_num(endo, 1)} – {_num(meso, 1)} – {_num(ecto, 1)}", S("scv", 10, C_MUTED, "semi")),
            Spacer(1, 8),
            comp_row(endo, pendo, "Endomorfia", f"Adiposidad relativa {_rating(endo)}", C_ENDO, C_ENDO_BG, C_ENDO),
            comp_row(meso, pmeso, "Mesomorfia", f"Desarrollo músculo-esquelético {_rating(meso).replace('baja', 'bajo').replace('moderada', 'moderado').replace('alta', 'alto')}",
                     WHITE, C_MESO_BG, WHITE),
            comp_row(ecto, pecto, "Ectomorfia", f"Linealidad relativa {_rating(ecto)}", C_ECTO, C_ECTO_BG, C_ECTO),
        ]
        points = ([(pendo, pmeso, pecto)] if has_prev_soma else []) + [(endo, meso, ecto)]
        soma = plain([[rows_left, _somatochart(points)]], [left_w, 5.6 * cm],
                     extra=[("VALIGN", (0, 0), (-1, -1), "TOP")])
        story.append(KeepTogether(section_title("Somatotipo", "Tu forma corporal en tres componentes, "
                                                "según el método Heath-Carter.") + [card(soma, W, 14),
                                                                                     Spacer(1, 20)]))

    # ── 7b. Índices de proporcionalidad (ISAK 2) ───────────────────────────
    if level2:
        def ratio(a, b, mult=100):
            va, vb = _f(ev, a), _f(ev, b)
            return va / vb * mult if va and vb else None
        idx = []
        ar, rs, il, tt_, tb = (_f(ev, k) for k in ("acromion_radial_cm", "radial_styloid_cm",
                                                   "iliospinal_height_cm", "trochanter_tibial_cm",
                                                   "tibiale_height_cm"))
        if comps:
            idx.append(("Índice músculo / óseo", comps["muscular"] / comps["osea"], 2))
        if ar and rs and h:
            idx.append(("I.R.E.S. superior", (ar + rs) / h * 100, 2))
        if il and h:
            idx.append(("I.R.E.S. inferior", il / h * 100, 2))
        if ar and rs and il:
            idx.append(("Índice intermembral", (ar + rs) / il * 100, 2))
        if ratio("radial_styloid_cm", "acromion_radial_cm"):
            idx.append(("Índice braquial", ratio("radial_styloid_cm", "acromion_radial_cm"), 2))
        if tb and tt_:
            idx.append(("Índice crural", tb / tt_ * 100, 2))
        if il and h and h - il > 0:
            idx.append(("Índice córmico", (h - il) / h * 100, 2))
            idx.append(("Índice esquelético (Manouvrier)", il / (h - il) * 100, 2))
        if ratio("biacromial_cm", "biiliocrestal_cm"):
            idx.append(("Índice acromio-ilíaco", ratio("biacromial_cm", "biiliocrestal_cm"), 2))
        if ratio("arm_span_cm", "height_cm"):
            idx.append(("Envergadura relativa", ratio("arm_span_cm", "height_cm"), 2))
        if idx:
            half_i = (len(idx) + 1) // 2
            boxw = (W - 10) / 2

            def idx_box(items):
                rows = [[_LeaderRow(n, _num(v, d), boxw - 20)] for n, v, d in items]
                t = Table(rows, colWidths=[boxw], hAlign="LEFT")
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), C_OPTION_BG), ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                    ("ROUNDEDCORNERS", [5, 5, 5, 5]), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, 0), 7),
                    ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
                ]))
                return t
            story.append(KeepTogether(section_title("Índices de proporcionalidad",
                                                    "Relaciones entre segmentos del cuerpo (perfil completo).")
                                      + [plain([[idx_box(idx[:half_i]), "", idx_box(idx[half_i:])]],
                                               [boxw, 10, boxw], extra=[("VALIGN", (0, 0), (-1, -1), "TOP")]),
                                         Spacer(1, 20)]))

    # ── 8. Indicadores de salud ─────────────────────────────────────────────
    ind = []
    iw = (W - 2 * 8) / 3
    seg_ok, seg_mid, seg_bad = HexColor("#bcd7b3"), C_AMBER, C_RED
    if bmi:
        label = ("Bajo peso", C_AMBER_BG, "#8a6d1f") if bmi < 18.5 else ("Normal", C_OK_BG, "#3f6b52") \
            if bmi < 25 else ("Sobrepeso", C_AMBER_BG, "#8a6d1f") if bmi < 30 else ("Obesidad", C_TERRA_BG, "#9a5a3f")
        ind.append(("IMC", _num(bmi, 1), label,
                    [(15, 18.5, seg_mid), (18.5, 25, seg_ok), (25, 30, seg_mid), (30, 40, seg_bad)], 15, 40, bmi,
                    "Normal 18,5–24,9 (OMS). Con alta masa muscular el IMC sobrestima la grasa."))
    waist, hip = _f(ev, "waist_cm"), _f(ev, "hip_glute_cm")
    if waist and h and "Cintura" not in suspicious:
        r = waist / h
        label = ("Saludable", C_OK_BG, "#3f6b52") if r < 0.5 else ("Riesgo aumentado", C_AMBER_BG, "#8a6d1f") \
            if r < 0.6 else ("Riesgo alto", C_TERRA_BG, "#9a5a3f")
        ind.append(("Cintura / talla", _num(r, 2), label,
                    [(0.3, 0.5, seg_ok), (0.5, 0.6, seg_mid), (0.6, 0.8, seg_bad)], 0.3, 0.8, r,
                    f"Saludable bajo 0,50 · cintura {_num(waist, 1)} cm"))
    if waist and hip and not ({"Cintura", "Cadera"} & suspicious):
        r = waist / hip
        cut = 0.90 if male else 0.85
        label = ("Saludable", C_OK_BG, "#3f6b52") if r < cut else ("Riesgo aumentado", C_TERRA_BG, "#9a5a3f")
        ind.append(("Cintura / cadera", _num(r, 2), label,
                    [(0.6, cut, seg_ok), (cut, cut + 0.08, seg_mid), (cut + 0.08, 1.2, seg_bad)], 0.6, 1.2, r,
                    f"Saludable bajo {_num(cut, 2)} en {'hombres' if male else 'mujeres'} (OMS)"))
    if ind:
        cards = []
        for title, val, (lab, bg, fg), segs, lo, hi, v, note in ind:
            top = plain([[P(f'<font size="8.5" color="#33443a">{title}</font><br/><b>{val}</b>',
                            S("iv", 17, C_INK, "head", leading=22)), chip(lab, bg, HexColor(fg))]],
                        [None, 2.4 * cm], extra=[("VALIGN", (1, 0), (1, 0), "BOTTOM"), ("ALIGN", (1, 0), (1, 0), "RIGHT")])
            cards.append(card([top, Spacer(1, 6), _RangeBar(iw - 22, segs, lo, hi, v), Spacer(1, 5),
                               P(note, S("in", 7, C_MUTED, leading=9))], iw, 10))
        while len(cards) < 3:
            cards.append("")
        story.append(KeepTogether(section_title("Indicadores de salud", "El punto muestra dónde estás dentro "
                                                "de cada rango.")
                                  + [plain([[cards[0], "", cards[1], "", cards[2]]], [iw, 8, iw, 8, iw],
                                           extra=[("VALIGN", (0, 0), (-1, -1), "TOP")]), Spacer(1, 20)]))

    # ── 9. Metas ────────────────────────────────────────────────────────────
    goals = [g.strip(" -•\t") for g in (getattr(ev, "goals_text", None) or "").splitlines() if g.strip(" -•\t")]
    tail = []
    if goals:
        when = ""
        nxt = getattr(ev, "next_eval_date", None)
        if nxt:
            try:
                d = dt_date.fromisoformat(str(nxt)[:10])
                when = f"{MESES[d.month - 1].capitalize()} {d.year}"
            except ValueError:
                when = str(nxt)
        hdr = plain([[P("Metas para tu próxima evaluación", S("gh", 12, C_INK, "head", leading=15)),
                      P(when, S("gw", 8.5, C_GREEN, "semi", align=TA_RIGHT))]], [W - 28 - 3.5 * cm, 3.5 * cm])
        rows = [[hdr]] + [[plain([[_SmallBox(), P(escape(g), S("gi", 9.5, C_TEXT))]], [16, W - 28 - 16])]
                          for g in goals]
        gt = Table(rows, colWidths=[W], hAlign="LEFT")
        gt.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER), ("ROUNDEDCORNERS", [7, 7, 7, 7]),
            ("BACKGROUND", (0, 0), (-1, 0), C_CARD_BG), ("LINEBELOW", (0, 0), (-1, 0), 0.6, C_BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, 0), 9), ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
            ("TOPPADDING", (0, 1), (-1, 1), 9), ("BOTTOMPADDING", (0, -1), (-1, -1), 11),
        ]))
        tail += [gt, Spacer(1, 16)]
    notes = Table([[""], [""], [""]], colWidths=[W], rowHeights=[0.75 * cm] * 3, hAlign="LEFT")
    notes.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER), ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("BACKGROUND", (0, 0), (-1, -1), C_OPTION_BG), ("LINEBELOW", (0, 0), (-1, -2), 0.5, C_BORDER),
    ]))
    tail += [P("Notas", S("nh", 11, C_INK, "head", leading=14)), Spacer(1, 5), notes]
    story.append(KeepTogether(tail))

    # ── Pie de página ───────────────────────────────────────────────────────
    left_txt = f"Nut. {nutritionist.name or nutritionist.username or ''} · Informe antropométrico {ev.isak_level or ''}"

    def footer(canvas, doc):
        canvas.saveState()
        y = 1.15 * cm
        x0, x1 = margin + 6, page_w - margin - 6
        canvas.setStrokeColor(C_BORDER)
        canvas.setLineWidth(0.6)
        canvas.line(x0, y + 0.42 * cm, x1, y + 0.42 * cm)
        canvas.setFont(_FONTS["body"], 7.5)
        canvas.setFillColor(C_MUTED)
        canvas.drawString(x0, y, left_txt)
        canvas.drawRightString(x1, y, f"Documento confidencial   ·   Pág. {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=LETTER, leftMargin=margin, rightMargin=margin,
                            topMargin=1.8 * cm, bottomMargin=2.0 * cm,
                            title=f"Informe ISAK — {patient.name or ''}",
                            author=nutritionist.name or nutritionist.username or "NutriApp")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


class _Swatch(Flowable):
    def __init__(self, color, size=8):
        super().__init__()
        self.color, self.width, self.height = HexColor(color), size, size

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.height, 2, stroke=0, fill=1)


def _swatch(color):
    return _Swatch(color)
