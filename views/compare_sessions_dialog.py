"""Dialog to compare two anthropometric sessions side by side."""
import customtkinter as ctk


COMPARE_ROWS = [
    ("Peso total (kg)",       "weight_kg",           None),
    ("Talla (cm)",            "height_cm",           None),
    ("Circ. cintura (cm)",    "waist_cm",            "lower"),
    ("Brazo relajado (BR)",   "arm_relaxed_cm",      None),
    ("Brazo contraído (BC)",  "arm_contracted_cm",   None),
    ("Dif. BC-BR",            "__dif_br_bc__",       "higher"),
    ('Cadera "glúteo"',       "hip_glute_cm",        None),
    ("Σ 6 pliegues (mm)",     "sum_6_skinfolds",     "lower"),
    ("% Masa grasa",          "fat_mass_pct",        "lower"),
    ("Masa grasa (kg)",       "fat_mass_kg",         "lower"),
    ("Masa magra (kg)",       "lean_mass_kg",        "higher"),
    ("IMC (kg/m²)",           "__bmi__",             None),
]

COLOR_GREEN  = "#16a34a"
COLOR_RED    = "#dc2626"
COLOR_AMBER  = "#ca8a04"
COLOR_GRAY   = "gray"


def _rec_date(r: dict) -> str:
    return r.get("session_date") or r.get("date", "—") or "—"


def _get_val(rec: dict, key: str):
    """Extract value from record, including computed keys."""
    if key == "__dif_br_bc__":
        br = rec.get("arm_relaxed_cm")
        bc = rec.get("arm_contracted_cm")
        if br is not None and bc is not None:
            return round(bc - br, 2)
        return None
    if key == "__bmi__":
        w = rec.get("weight_kg")
        h = rec.get("height_cm")
        if w and h:
            try:
                return round(w / ((h / 100) ** 2), 2)
            except Exception:
                return None
        return None
    return rec.get(key)


def _fmt(val, key: str = "") -> str:
    if val is None:
        return "—"
    if key == "fat_mass_pct":
        return f"{round(val, 1)}%"
    if isinstance(val, float):
        return str(round(val, 2))
    return str(val)


def _diff_color(diff, better: str | None) -> str:
    if diff is None or diff == 0:
        return COLOR_GRAY
    if better == "lower":
        return COLOR_GREEN if diff < 0 else COLOR_RED
    if better == "higher":
        return COLOR_GREEN if diff > 0 else COLOR_RED
    return COLOR_AMBER


class CompareSessionsDialog(ctk.CTkToplevel):
    def __init__(self, parent, rec_a: dict, rec_b: dict, patient: dict):
        super().__init__(parent)
        date_a = _rec_date(rec_a)
        date_b = _rec_date(rec_b)
        self.title(f"Comparar sesiones — {date_a} vs {date_b}")
        self.geometry("900x700")
        self.resizable(True, True)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(
            self,
            text=f"Comparación: {patient.get('name', '—')}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(16, 4), sticky="w")

        # Scrollable table
        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))
        scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)

        HDR_BG   = ("#1a6b3c", "#0d3d20")
        ROW_ALT  = ("#f0fdf4", "#1a2e22")
        ROW_NORM = ("white", "#1e1e1e")

        headers = ["Variable", f"Sesión A\n{date_a}", f"Sesión B\n{date_b}", "Diferencia (B−A)"]
        for c, h in enumerate(headers):
            frm = ctk.CTkFrame(scroll, fg_color=HDR_BG, corner_radius=0)
            frm.grid(row=0, column=c, padx=1, pady=1, sticky="nsew")
            ctk.CTkLabel(
                frm, text=h,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="white", justify="center"
            ).pack(padx=8, pady=6)

        for row_i, (label, key, better) in enumerate(COMPARE_ROWS, start=1):
            bg = ROW_ALT if row_i % 2 == 0 else ROW_NORM

            val_a = _get_val(rec_a, key)
            val_b = _get_val(rec_b, key)
            fmt_a = _fmt(val_a, key)
            fmt_b = _fmt(val_b, key)

            diff = None
            diff_str = "—"
            diff_color = COLOR_GRAY
            if val_a is not None and val_b is not None:
                diff = round(val_b - val_a, 3)
                diff_str = f"{diff:+.2f}"
                diff_color = _diff_color(diff, better)

            cells = [
                (label,    "gray10" if ctk.get_appearance_mode() == "Light" else "gray90"),
                (fmt_a,    None),
                (fmt_b,    None),
                (diff_str, diff_color),
            ]

            for c, (text, tc) in enumerate(cells):
                frm = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=0)
                frm.grid(row=row_i, column=c, padx=1, pady=1, sticky="nsew")
                kwargs = dict(
                    text=text,
                    font=ctk.CTkFont(size=11, weight="bold" if c == 3 else "normal"),
                    anchor="w" if c == 0 else "center",
                    justify="left" if c == 0 else "center",
                )
                if tc:
                    kwargs["text_color"] = tc
                ctk.CTkLabel(frm, **kwargs).pack(padx=8, pady=5, fill="x")

        # Close button
        ctk.CTkButton(
            self, text="Cerrar", width=120, height=34,
            command=self.destroy
        ).grid(row=2, column=0, padx=20, pady=(0, 16), sticky="e")
