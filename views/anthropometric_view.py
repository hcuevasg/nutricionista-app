import customtkinter as ctk
from tkinter import messagebox
from datetime import date
import database.db_manager as db
import utils.calculations as calc


def _section_label(parent, text, row, cols=4):
    """Styled section header spanning all columns."""
    frm = ctk.CTkFrame(parent, fg_color=("#e8f5ee", "#1a3a28"), corner_radius=6)
    frm.grid(row=row, column=0, columnspan=cols * 2,
             padx=8, pady=(14, 2), sticky="ew")
    ctk.CTkLabel(
        frm, text=text,
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=("#1a6b3c", "#4ade80")
    ).pack(side="left", padx=10, pady=4)


def _field_row(parent, items, row, var_dict):
    """
    items: list of (label, key, col_index) — col_index 0..3
    Places label at (row, col*2) and entry at (row+1, col*2).
    """
    for label, key, col in items:
        ctk.CTkLabel(
            parent, text=label, text_color="gray",
            font=ctk.CTkFont(size=11), anchor="w"
        ).grid(row=row, column=col * 2, padx=(10, 2), pady=(6, 0), sticky="w")
        var_dict[key] = ctk.StringVar()
        ctk.CTkEntry(parent, textvariable=var_dict[key], height=32
                     ).grid(row=row + 1, column=col * 2,
                            padx=(10, 2), pady=(0, 2), sticky="ew")


class AnthropometricFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app
        self._vars: dict[str, ctk.StringVar] = {}
        self._result_labels: dict[str, ctk.CTkLabel] = {}
        self._last_calc: dict = {}
        self._isak_level = ctk.StringVar(value="ISAK 1")
        self._isak2_frame = None
        self._build_ui()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header bar
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hdr, text="Evaluación Antropométrica ISAK",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self._patient_lbl = ctk.CTkLabel(
            hdr, text="Ningún paciente seleccionado",
            font=ctk.CTkFont(size=13), text_color="gray"
        )
        self._patient_lbl.grid(row=0, column=1, padx=16, sticky="w")

        # Tabs
        self._tabs = ctk.CTkTabview(self)
        self._tabs.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self._tabs.add("Nueva evaluación")
        self._tabs.add("Historial")

        self._build_form_tab(self._tabs.tab("Nueva evaluación"))
        self._build_history_tab(self._tabs.tab("Historial"))

    # ── Form tab ──────────────────────────────────────────────────────────────
    def _build_form_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # ── ISAK Level selector ────────────────────────────────────────────
        level_bar = ctk.CTkFrame(tab, fg_color=("#f0fdf4", "#1a2e22"),
                                 corner_radius=8)
        level_bar.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 0))

        ctk.CTkLabel(
            level_bar, text="Nivel ISAK:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#1a6b3c", "#4ade80")
        ).pack(side="left", padx=(12, 8), pady=8)

        ctk.CTkSegmentedButton(
            level_bar, values=["ISAK 1", "ISAK 2"],
            variable=self._isak_level,
            command=self._toggle_isak_level,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left", pady=6)

        ctk.CTkLabel(
            level_bar,
            text="ISAK 1: perfil restringido  |  ISAK 2: perfil completo + somatotipo",
            font=ctk.CTkFont(size=10), text_color="gray"
        ).pack(side="left", padx=16, pady=8)

        # ── Scrollable form ────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        f = scroll  # alias

        # ── DATOS BÁSICOS ──────────────────────────────────────────────────
        _section_label(f, "DATOS BÁSICOS", row=0, cols=4)

        self._vars["date"] = ctk.StringVar(value=date.today().isoformat())
        ctk.CTkLabel(f, text="Fecha sesión", text_color="gray",
                     font=ctk.CTkFont(size=11), anchor="w"
                     ).grid(row=1, column=0, padx=(10, 2), pady=(6, 0), sticky="w")
        ctk.CTkEntry(f, textvariable=self._vars["date"], height=32
                     ).grid(row=2, column=0, padx=(10, 2), pady=(0, 2), sticky="ew")

        for label, key, col in [
            ("Peso (kg)",                  "weight_kg", 1),
            ("Talla (cm)",                 "height_cm", 2),
            ("Circ. cintura mínima (cm)",  "waist_cm",  3),
        ]:
            ctk.CTkLabel(f, text=label, text_color="gray",
                         font=ctk.CTkFont(size=11), anchor="w"
                         ).grid(row=1, column=col * 2, padx=(10, 2), pady=(6, 0), sticky="w")
            self._vars[key] = ctk.StringVar()
            ctk.CTkEntry(f, textvariable=self._vars[key], height=32
                         ).grid(row=2, column=col * 2, padx=(10, 2), pady=(0, 2), sticky="ew")

        # ── PERÍMETROS ────────────────────────────────────────────────────
        _section_label(f, "PERÍMETROS (cm)", row=3, cols=4)

        perimeters = [
            ("Brazo relajado (BR)",  "arm_relaxed_cm",   4, 0),
            ("Brazo contraído (BC)", "arm_contracted_cm", 4, 1),
            ('Cadera "glúteo"',      "hip_glute_cm",      4, 2),
            ("Muslo máximo",         "thigh_max_cm",      4, 3),
            ("Muslo medio",          "thigh_mid_cm",      6, 0),
            ("Pantorrilla",          "calf_cm",           6, 1),
        ]
        for label, key, row, col in perimeters:
            ctk.CTkLabel(f, text=label, text_color="gray",
                         font=ctk.CTkFont(size=11), anchor="w"
                         ).grid(row=row, column=col * 2,
                                padx=(10, 2), pady=(6, 0), sticky="w")
            self._vars[key] = ctk.StringVar()
            ctk.CTkEntry(f, textvariable=self._vars[key], height=32
                         ).grid(row=row + 1, column=col * 2,
                                padx=(10, 2), pady=(0, 2), sticky="ew")

        # ── PLIEGUES CUTÁNEOS ─────────────────────────────────────────────
        _section_label(f, "PLIEGUES CUTÁNEOS (mm)", row=8, cols=4)

        skinfolds = [
            ("Tríceps (*)",          "triceps_mm",      9,  0),
            ("Subescapular (*)",     "subscapular_mm",  9,  1),
            ("Bíceps",               "biceps_mm",       9,  2),
            ("Cresta iliaca",        "iliac_crest_mm",  9,  3),
            ("Supraespinal (*)",     "supraspinal_mm",  11, 0),
            ("Abdominal (*)",        "abdominal_mm",    11, 1),
            ("Muslo medial (*)",     "medial_thigh_mm", 11, 2),
            ("Pantorrilla máx. (*)", "max_calf_mm",     11, 3),
        ]
        for label, key, row, col in skinfolds:
            ctk.CTkLabel(f, text=label, text_color="gray",
                         font=ctk.CTkFont(size=11), anchor="w"
                         ).grid(row=row, column=col * 2,
                                padx=(10, 2), pady=(6, 0), sticky="w")
            self._vars[key] = ctk.StringVar()
            ent = ctk.CTkEntry(f, textvariable=self._vars[key], height=32)
            ent.grid(row=row + 1, column=col * 2,
                     padx=(10, 2), pady=(0, 2), sticky="ew")
            self._vars[key].trace_add("write", lambda *_: self._update_sum())

        # Sumatoria 6 pliegues (readonly, auto)
        ctk.CTkLabel(f, text="Σ 6 pliegues (*) — auto",
                     text_color="#1a6b3c",
                     font=ctk.CTkFont(size=11, weight="bold"), anchor="w"
                     ).grid(row=13, column=0, padx=(10, 2), pady=(6, 0), sticky="w")
        self._vars["sum_6_skinfolds"] = ctk.StringVar(value="—")
        ctk.CTkEntry(f, textvariable=self._vars["sum_6_skinfolds"],
                     height=32, state="disabled",
                     fg_color=("#e8f5ee", "#1a3a28")
                     ).grid(row=14, column=0, padx=(10, 2), pady=(0, 2), sticky="ew")

        # ── ISAK 2 EXTRA FIELDS (hidden by default) ───────────────────────
        self._isak2_frame = ctk.CTkFrame(f, fg_color="transparent")
        self._isak2_frame.grid(row=15, column=0, columnspan=8,
                               sticky="ew", padx=0, pady=0)
        self._isak2_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        self._build_isak2_fields(self._isak2_frame)
        self._isak2_frame.grid_remove()   # hidden until ISAK 2 selected

        # ── BUTTONS ───────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(f, fg_color="transparent")
        btn_row.grid(row=16, column=0, columnspan=8, padx=8, pady=(14, 6), sticky="ew")
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_row, text="Calcular", height=40,
            command=self._calculate
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            btn_row, text="Guardar evaluación", height=40,
            fg_color="#16a34a", hover_color="#15803d",
            command=self._save
        ).grid(row=0, column=1, sticky="ew")

        # ── RESULTS BOX (ISAK 1) ──────────────────────────────────────────
        res = ctk.CTkFrame(f, fg_color=("#f0fdf4", "#1a2e22"), corner_radius=10)
        res.grid(row=17, column=0, columnspan=8, padx=8, pady=(8, 4), sticky="ew")
        res.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        result_items = [
            ("dif_br_bc",   "Diferencia BC - BR"),
            ("sum6",        "Σ 6 pliegues"),
            ("fat_pct",     "% Masa grasa (D&W)"),
            ("fat_kg",      "Masa grasa (kg)"),
            ("lean_kg",     "Masa magra (kg)"),
        ]
        for col, (key, label) in enumerate(result_items):
            frm = ctk.CTkFrame(res, fg_color="transparent")
            frm.grid(row=0, column=col, padx=12, pady=10, sticky="ew")
            ctk.CTkLabel(frm, text=label,
                         font=ctk.CTkFont(size=9), text_color="gray"
                         ).pack(anchor="w")
            lbl = ctk.CTkLabel(frm, text="—",
                               font=ctk.CTkFont(size=15, weight="bold"))
            lbl.pack(anchor="w")
            self._result_labels[key] = lbl

        ctk.CTkLabel(
            res, text="*Ecuación Durnin & Womersley — Medición antropométrica ISAK 1",
            font=ctk.CTkFont(size=9), text_color="gray"
        ).grid(row=1, column=0, columnspan=5, padx=12, pady=(0, 8), sticky="w")

        # ── RESULTS BOX (ISAK 2 — hidden by default) ──────────────────────
        self._isak2_results_frame = ctk.CTkFrame(
            f, fg_color=("#e8f5ee", "#1a3a28"), corner_radius=10)
        self._isak2_results_frame.grid(row=18, column=0, columnspan=8,
                                       padx=8, pady=(4, 16), sticky="ew")
        self._isak2_results_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        result2_items = [
            ("endo",  "Endomorfia"),
            ("meso",  "Mesomorfia"),
            ("ecto",  "Ectomorfia"),
            ("whtr",  "Índ. Cintura/Talla"),
            ("amb",   "Área Musc. Brazo (cm²)"),
        ]
        for col, (key, label) in enumerate(result2_items):
            frm2 = ctk.CTkFrame(self._isak2_results_frame, fg_color="transparent")
            frm2.grid(row=0, column=col, padx=12, pady=10, sticky="ew")
            ctk.CTkLabel(frm2, text=label,
                         font=ctk.CTkFont(size=9), text_color="gray"
                         ).pack(anchor="w")
            lbl2 = ctk.CTkLabel(frm2, text="—",
                                font=ctk.CTkFont(size=15, weight="bold"))
            lbl2.pack(anchor="w")
            self._result_labels[f"isak2_{key}"] = lbl2

        ctk.CTkLabel(
            self._isak2_results_frame,
            text="*Somatotipo Heath & Carter (1990) — Medición antropométrica ISAK 2",
            font=ctk.CTkFont(size=9), text_color="gray"
        ).grid(row=1, column=0, columnspan=5, padx=12, pady=(0, 8), sticky="w")
        self._isak2_results_frame.grid_remove()

    def _build_isak2_fields(self, f):
        """Build all ISAK 2 extra input fields inside wrapper frame f."""

        # ── PLIEGUES CUTÁNEOS ADICIONALES ─────────────────────────────────
        _section_label(f, "PLIEGUES CUTÁNEOS ADICIONALES (mm)", row=0, cols=4)
        _field_row(f, [
            ("Pectoral (tórax)",   "pectoral_mm",    0),
            ("Axilar medio",       "axillary_mm",    1),
            ("Muslo anterior",     "front_thigh_mm", 2),
        ], row=1, var_dict=self._vars)

        # ── PERÍMETROS ADICIONALES ────────────────────────────────────────
        _section_label(f, "PERÍMETROS ADICIONALES (cm)", row=3, cols=4)
        _field_row(f, [
            ("Cabeza",              "head_cm",      0),
            ("Cuello",              "neck_cm",      1),
            ("Tórax mesoesternal",  "chest_cm",     2),
            ("Tobillo mínimo",      "ankle_min_cm", 3),
        ], row=4, var_dict=self._vars)

        # ── DIÁMETROS ÓSEOS ───────────────────────────────────────────────
        _section_label(f, "DIÁMETROS ÓSEOS (cm)", row=6, cols=4)
        _field_row(f, [
            ("Húmero bicondíleo",    "humerus_width_cm",  0),
            ("Fémur bicondíleo",     "femur_width_cm",    1),
            ("Biacromial",           "biacromial_cm",     2),
            ("Biiliocrestal",        "biiliocrestal_cm",  3),
        ], row=7, var_dict=self._vars)
        _field_row(f, [
            ("Ant-post. tórax",      "ap_chest_cm",       0),
            ("Transv. tórax",        "transv_chest_cm",   1),
            ("Longitud pie",         "foot_length_cm",    2),
            ("Muñeca biestiloideo",  "wrist_cm",          3),
        ], row=9, var_dict=self._vars)
        _field_row(f, [
            ("Tobillo bimaleolar",   "ankle_bimalleolar_cm", 0),
        ], row=11, var_dict=self._vars)

        # ── LONGITUDES ────────────────────────────────────────────────────
        _section_label(f, "LONGITUDES (cm)", row=13, cols=4)
        _field_row(f, [
            ("Acromio-radial",       "acromion_radial_cm",  0),
            ("Radio-estiloide",      "radial_styloid_cm",   1),
            ("Iliospinal (pierna)",  "iliospinal_height_cm", 2),
            ("Trocánter-tibial",     "trochanter_tibial_cm", 3),
        ], row=14, var_dict=self._vars)

    # ── Toggle ISAK level ─────────────────────────────────────────────────────
    def _toggle_isak_level(self, value):
        if value == "ISAK 2":
            self._isak2_frame.grid()
            self._isak2_results_frame.grid()
        else:
            self._isak2_frame.grid_remove()
            self._isak2_results_frame.grid_remove()

    # ── History tab ───────────────────────────────────────────────────────────
    def _build_history_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self._history_scroll = ctk.CTkScrollableFrame(tab)
        self._history_scroll.grid(row=0, column=0, sticky="nsew", pady=8)

    # ── Logic ─────────────────────────────────────────────────────────────────
    def on_show(self):
        pid = self.app.get_patient_id()
        if pid:
            p = db.get_patient(pid)
            if p:
                self._patient_lbl.configure(text=f"Paciente: {p['name']}")
                if p.get("height_cm") and not self._vars["height_cm"].get():
                    self._vars["height_cm"].set(str(p["height_cm"]))
                if p.get("weight_kg") and not self._vars["weight_kg"].get():
                    self._vars["weight_kg"].set(str(p["weight_kg"]))
                self._load_history()
                return
        self._patient_lbl.configure(text="Ningún paciente seleccionado")

    def _gf(self, key) -> float | None:
        """Get float from var dict, return None if empty/invalid."""
        try:
            v = self._vars.get(key)
            if v is None:
                return None
            s = v.get().strip()
            return float(s) if s else None
        except ValueError:
            return None

    def _update_sum(self):
        """Live-recalculate Σ6 as fields are typed."""
        s = calc.sum_6_skinfolds(
            self._gf("triceps_mm"),    self._gf("subscapular_mm"),
            self._gf("supraspinal_mm"), self._gf("abdominal_mm"),
            self._gf("medial_thigh_mm"), self._gf("max_calf_mm"),
        )
        self._vars["sum_6_skinfolds"].set(f"{s} mm" if s is not None else "—")

    def _calculate(self) -> bool:
        pid = self.app.get_patient_id()
        if not pid:
            messagebox.showwarning("Sin paciente",
                                   "Selecciona un paciente primero.")
            return False

        patient = db.get_patient(pid)
        sex = (patient or {}).get("sex", "Femenino")
        age = (patient or {}).get("age", 30) or 30

        w = self._gf("weight_kg")
        if not w:
            messagebox.showerror("Datos incompletos", "El peso es obligatorio.")
            return False

        # Diferencia BR-BC
        br = self._gf("arm_relaxed_cm")
        bc = self._gf("arm_contracted_cm")
        dif = round(bc - br, 2) if (br is not None and bc is not None) else None
        self._result_labels["dif_br_bc"].configure(
            text=f"{dif:+.2f} cm" if dif is not None else "—"
        )

        # Σ 6 pliegues
        s6 = calc.sum_6_skinfolds(
            self._gf("triceps_mm"),    self._gf("subscapular_mm"),
            self._gf("supraspinal_mm"), self._gf("abdominal_mm"),
            self._gf("medial_thigh_mm"), self._gf("max_calf_mm"),
        )
        self._result_labels["sum6"].configure(
            text=f"{s6} mm" if s6 is not None else "—"
        )

        # Durnin & Womersley
        bi = self._gf("biceps_mm")
        tr = self._gf("triceps_mm")
        ss = self._gf("subscapular_mm")
        ic = self._gf("iliac_crest_mm")

        density, fat_pct = None, None
        if all(v is not None for v in [bi, tr, ss, ic]):
            density, fat_pct = calc.body_fat_durnin_womersley(
                bi, tr, ss, ic, age, sex
            )

        fat_kg  = calc.fat_mass_kg(w, fat_pct)  if fat_pct is not None else None
        lean_kg = calc.lean_mass_kg(w, fat_kg)  if fat_kg  is not None else None

        self._result_labels["fat_pct"].configure(
            text=f"{fat_pct}%" if fat_pct is not None else "—"
        )
        self._result_labels["fat_kg"].configure(
            text=f"{fat_kg} kg" if fat_kg is not None else "—"
        )
        self._result_labels["lean_kg"].configure(
            text=f"{lean_kg} kg" if lean_kg is not None else "—"
        )

        self._last_calc = {
            "dif_br_bc":       dif,
            "sum_6_skinfolds": s6,
            "body_density":    density,
            "fat_mass_pct":    fat_pct,
            "fat_mass_kg":     fat_kg,
            "lean_mass_kg":    lean_kg,
            # ISAK 2 placeholders
            "somatotype_endo":  None,
            "somatotype_meso":  None,
            "somatotype_ecto":  None,
            "waist_height_ratio": None,
            "arm_muscle_area":  None,
        }

        # ── ISAK 2 calculations ────────────────────────────────────────────
        if self._isak_level.get() == "ISAK 2":
            h = self._gf("height_cm")

            # Somatotipo Heath & Carter
            endo, meso, ecto = calc.somatotype_heath_carter(
                h, w,
                self._gf("triceps_mm"),    self._gf("subscapular_mm"),
                self._gf("supraspinal_mm"),
                self._gf("humerus_width_cm"), self._gf("femur_width_cm"),
                self._gf("arm_contracted_cm"), self._gf("calf_cm"),
                self._gf("max_calf_mm"),
            )
            self._result_labels["isak2_endo"].configure(
                text=f"{endo}" if endo is not None else "—"
            )
            self._result_labels["isak2_meso"].configure(
                text=f"{meso}" if meso is not None else "—"
            )
            self._result_labels["isak2_ecto"].configure(
                text=f"{ecto}" if ecto is not None else "—"
            )

            # Índice cintura/talla
            waist = self._gf("waist_cm")
            whtr = calc.waist_height_ratio(waist, h)
            self._result_labels["isak2_whtr"].configure(
                text=f"{whtr}" if whtr is not None else "—"
            )

            # AMB
            amb = calc.arm_muscle_area(
                self._gf("arm_relaxed_cm"), self._gf("triceps_mm")
            )
            self._result_labels["isak2_amb"].configure(
                text=f"{amb}" if amb is not None else "—"
            )

            self._last_calc.update({
                "somatotype_endo":    endo,
                "somatotype_meso":    meso,
                "somatotype_ecto":    ecto,
                "waist_height_ratio": whtr,
                "arm_muscle_area":    amb,
            })

        return True

    def _save(self):
        if not self._calculate():
            return
        pid = self.app.get_patient_id()
        if not pid:
            return

        level = self._isak_level.get()

        data = {
            "patient_id":         pid,
            "date":               self._vars["date"].get().strip(),
            "isak_level":         level,
            "weight_kg":          self._gf("weight_kg"),
            "height_cm":          self._gf("height_cm"),
            "waist_cm":           self._gf("waist_cm"),
            "arm_relaxed_cm":     self._gf("arm_relaxed_cm"),
            "arm_contracted_cm":  self._gf("arm_contracted_cm"),
            "hip_glute_cm":       self._gf("hip_glute_cm"),
            "thigh_max_cm":       self._gf("thigh_max_cm"),
            "thigh_mid_cm":       self._gf("thigh_mid_cm"),
            "calf_cm":            self._gf("calf_cm"),
            "triceps_mm":         self._gf("triceps_mm"),
            "subscapular_mm":     self._gf("subscapular_mm"),
            "biceps_mm":          self._gf("biceps_mm"),
            "iliac_crest_mm":     self._gf("iliac_crest_mm"),
            "supraspinal_mm":     self._gf("supraspinal_mm"),
            "abdominal_mm":       self._gf("abdominal_mm"),
            "medial_thigh_mm":    self._gf("medial_thigh_mm"),
            "max_calf_mm":        self._gf("max_calf_mm"),
            # ISAK 2 extra skinfolds
            "pectoral_mm":        self._gf("pectoral_mm"),
            "axillary_mm":        self._gf("axillary_mm"),
            "front_thigh_mm":     self._gf("front_thigh_mm"),
            # ISAK 2 extra perimeters
            "head_cm":            self._gf("head_cm"),
            "neck_cm":            self._gf("neck_cm"),
            "chest_cm":           self._gf("chest_cm"),
            "ankle_min_cm":       self._gf("ankle_min_cm"),
            # ISAK 2 bone diameters
            "humerus_width_cm":   self._gf("humerus_width_cm"),
            "femur_width_cm":     self._gf("femur_width_cm"),
            "biacromial_cm":      self._gf("biacromial_cm"),
            "biiliocrestal_cm":   self._gf("biiliocrestal_cm"),
            "ap_chest_cm":        self._gf("ap_chest_cm"),
            "transv_chest_cm":    self._gf("transv_chest_cm"),
            "foot_length_cm":     self._gf("foot_length_cm"),
            "wrist_cm":           self._gf("wrist_cm"),
            "ankle_bimalleolar_cm": self._gf("ankle_bimalleolar_cm"),
            # ISAK 2 lengths
            "acromion_radial_cm": self._gf("acromion_radial_cm"),
            "radial_styloid_cm":  self._gf("radial_styloid_cm"),
            "iliospinal_height_cm": self._gf("iliospinal_height_cm"),
            "trochanter_tibial_cm": self._gf("trochanter_tibial_cm"),
            **self._last_calc,
        }
        db.insert_anthropometric(data)
        messagebox.showinfo("Guardado",
                            f"Evaluación {level} guardada correctamente.")
        self._clear_form()
        self._load_history()
        self._tabs.set("Historial")

    def _clear_form(self):
        skip = {"date", "sum_6_skinfolds"}
        for key, var in self._vars.items():
            if key not in skip:
                var.set("")
        self._vars["sum_6_skinfolds"].set("—")
        for lbl in self._result_labels.values():
            lbl.configure(text="—")
        self._last_calc = {}

    # ── History tab ───────────────────────────────────────────────────────────
    def _load_history(self):
        for w in self._history_scroll.winfo_children():
            w.destroy()

        pid = self.app.get_patient_id()
        if not pid:
            return

        records = db.get_anthropometrics(pid)   # ASC by date
        if not records:
            ctk.CTkLabel(
                self._history_scroll,
                text="Sin evaluaciones registradas.",
                text_color="gray"
            ).grid(row=0, column=0, pady=30)
            return

        has_isak2 = any(r.get("isak_level") == "ISAK 2" for r in records)

        n_sessions = len(records)
        total_cols = n_sessions + 2
        for c in range(total_cols):
            self._history_scroll.grid_columnconfigure(c, weight=1)

        # Header row — show date + ISAK level badge
        headers = ["Variable"]
        for r in records:
            lvl = r.get("isak_level") or "ISAK 1"
            headers.append(f"{r['date']}\n[{lvl}]")
        headers.append("Cambios")

        for c, h in enumerate(headers):
            ctk.CTkLabel(
                self._history_scroll, text=h,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="gray", justify="center"
            ).grid(row=0, column=c, padx=6, pady=(4, 8), sticky="w")

        # Variable rows definition
        sections = [
            ("── DATOS BÁSICOS ──", []),
            (None, [
                ("Peso (kg)",             "weight_kg"),
                ("Talla (cm)",            "height_cm"),
                ("Circ. cintura mín. (cm)", "waist_cm"),
            ]),
            ("── PERÍMETROS (cm) ──", []),
            (None, [
                ("Brazo relajado (BR)",  "arm_relaxed_cm"),
                ("Brazo contraído (BC)", "arm_contracted_cm"),
                ("Dif. BC - BR",         "__dif_br_bc__"),
                ('Cadera "glúteo"',      "hip_glute_cm"),
                ("Muslo máximo",         "thigh_max_cm"),
                ("Muslo medio",          "thigh_mid_cm"),
                ("Pantorrilla",          "calf_cm"),
            ]),
            ("── PLIEGUES CUTÁNEOS (mm) ──", []),
            (None, [
                ("Tríceps (*)",          "triceps_mm"),
                ("Subescapular (*)",     "subscapular_mm"),
                ("Bíceps",               "biceps_mm"),
                ("Cresta iliaca",        "iliac_crest_mm"),
                ("Supraespinal (*)",     "supraspinal_mm"),
                ("Abdominal (*)",        "abdominal_mm"),
                ("Muslo medial (*)",     "medial_thigh_mm"),
                ("Pantorrilla máx. (*)", "max_calf_mm"),
                ("Σ 6 pliegues (*)",     "sum_6_skinfolds"),
            ]),
            ("── RESULTADOS D&W ──", []),
            (None, [
                ("% Masa grasa* (D&W)", "fat_mass_pct"),
                ("Masa grasa (kg)",     "fat_mass_kg"),
                ("Masa magra (kg)",     "lean_mass_kg"),
            ]),
        ]

        if has_isak2:
            sections += [
                ("── PLIEGUES ADICIONALES ISAK 2 (mm) ──", []),
                (None, [
                    ("Pectoral",        "pectoral_mm"),
                    ("Axilar medio",    "axillary_mm"),
                    ("Muslo anterior",  "front_thigh_mm"),
                ]),
                ("── PERÍMETROS ADICIONALES ISAK 2 (cm) ──", []),
                (None, [
                    ("Cabeza",              "head_cm"),
                    ("Cuello",              "neck_cm"),
                    ("Tórax mesoesternal",  "chest_cm"),
                    ("Tobillo mínimo",      "ankle_min_cm"),
                ]),
                ("── DIÁMETROS ÓSEOS ISAK 2 (cm) ──", []),
                (None, [
                    ("Húmero bicondíleo",   "humerus_width_cm"),
                    ("Fémur bicondíleo",    "femur_width_cm"),
                    ("Biacromial",          "biacromial_cm"),
                    ("Biiliocrestal",       "biiliocrestal_cm"),
                    ("Ant-post. tórax",     "ap_chest_cm"),
                    ("Transv. tórax",       "transv_chest_cm"),
                    ("Longitud pie",        "foot_length_cm"),
                    ("Muñeca biestiloideo", "wrist_cm"),
                    ("Tobillo bimaleolar",  "ankle_bimalleolar_cm"),
                ]),
                ("── LONGITUDES ISAK 2 (cm) ──", []),
                (None, [
                    ("Acromio-radial",      "acromion_radial_cm"),
                    ("Radio-estiloide",     "radial_styloid_cm"),
                    ("Iliospinal (pierna)", "iliospinal_height_cm"),
                    ("Trocánter-tibial",    "trochanter_tibial_cm"),
                ]),
                ("── SOMATOTIPO ISAK 2 ──", []),
                (None, [
                    ("Endomorfia",          "somatotype_endo"),
                    ("Mesomorfia",          "somatotype_meso"),
                    ("Ectomorfia",          "somatotype_ecto"),
                    ("Índ. Cintura/Talla",  "waist_height_ratio"),
                    ("AMB (cm²)",           "arm_muscle_area"),
                ]),
            ]

        row_idx = 1
        for section_title, rows in sections:
            if section_title:
                frm = ctk.CTkFrame(self._history_scroll,
                                   fg_color=("#e8f5ee", "#1a3a28"), corner_radius=4)
                frm.grid(row=row_idx, column=0, columnspan=total_cols,
                         padx=6, pady=(10, 2), sticky="ew")
                ctk.CTkLabel(
                    frm, text=section_title,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=("#1a6b3c", "#4ade80")
                ).pack(side="left", padx=8, pady=3)
                row_idx += 1
                continue

            for var_label, db_key in rows:
                ctk.CTkLabel(
                    self._history_scroll, text=var_label,
                    font=ctk.CTkFont(size=11), anchor="w"
                ).grid(row=row_idx, column=0, padx=6, pady=3, sticky="w")

                vals = []
                for rec in records:
                    if db_key == "__dif_br_bc__":
                        br = rec.get("arm_relaxed_cm")
                        bc = rec.get("arm_contracted_cm")
                        v = round(bc - br, 2) if (br and bc) else None
                    else:
                        v = rec.get(db_key)

                    if db_key == "fat_mass_pct" and v is not None:
                        cell = f"{v}%"
                    elif v is not None:
                        cell = str(v)
                    else:
                        cell = "—"
                    vals.append((v, cell))

                for c, (raw, cell) in enumerate(vals, start=1):
                    ctk.CTkLabel(
                        self._history_scroll, text=cell,
                        font=ctk.CTkFont(size=11)
                    ).grid(row=row_idx, column=c, padx=6, pady=3, sticky="w")

                # Cambios column
                cambio_text = "—"
                if len(vals) >= 2:
                    first_v, last_v = vals[0][0], vals[-1][0]
                    if first_v is not None and last_v is not None:
                        diff = round(last_v - first_v, 2)
                        cambio_text = f"{diff:+.2f}"
                ctk.CTkLabel(
                    self._history_scroll, text=cambio_text,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=("#16a34a" if cambio_text.startswith("+") else
                                ("#dc2626" if cambio_text.startswith("-") else "gray"))
                ).grid(row=row_idx, column=n_sessions + 1,
                       padx=6, pady=3, sticky="w")

                row_idx += 1

        # Footer note
        ctk.CTkLabel(
            self._history_scroll,
            text="*Según ecuación de Durnin & Womersley — ISAK 1  |  "
                 "**Somatotipo Heath & Carter (1990) — ISAK 2",
            font=ctk.CTkFont(size=9), text_color="gray"
        ).grid(row=row_idx, column=0, columnspan=total_cols,
               padx=6, pady=(12, 4), sticky="w")

        row_idx += 1
        # Delete buttons per session
        del_frm = ctk.CTkFrame(self._history_scroll, fg_color="transparent")
        del_frm.grid(row=row_idx, column=0, columnspan=total_cols,
                     padx=6, pady=(4, 12), sticky="w")
        ctk.CTkLabel(del_frm, text="Eliminar sesión:",
                     font=ctk.CTkFont(size=10), text_color="gray"
                     ).pack(side="left", padx=(0, 8))
        for rec in records:
            rid = rec["id"]
            lvl = rec.get("isak_level") or "ISAK 1"
            ctk.CTkButton(
                del_frm, text=f"{rec['date']}", width=110, height=26,
                fg_color="#dc2626", hover_color="#991b1b",
                font=ctk.CTkFont(size=10),
                command=lambda r=rid: self._delete_record(r)
            ).pack(side="left", padx=3)

    def _delete_record(self, rid: int):
        if messagebox.askyesno("Eliminar", "¿Eliminar esta evaluación?"):
            db.delete_anthropometric(rid)
            self._load_history()
