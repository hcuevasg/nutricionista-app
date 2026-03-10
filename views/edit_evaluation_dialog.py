"""
Full-form edit dialog for existing anthropometric evaluations.
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from typing import Optional

import database.db_manager as db
import utils.calculations as calc

try:
    from tkcalendar import DateEntry as _DateEntry
    _CAL_OK = True
except ImportError:
    _CAL_OK = False


# ── Shared UI helpers (same style as anthropometric_view) ─────────────────────

def _section_label(parent, text, row, cols=4):
    frm = ctk.CTkFrame(parent, fg_color=("#e8f5ee", "#1a3a28"), corner_radius=6)
    frm.grid(row=row, column=0, columnspan=cols * 2,
             padx=8, pady=(14, 2), sticky="ew")
    ctk.CTkLabel(
        frm, text=text,
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=("#1a6b3c", "#4ade80")
    ).pack(side="left", padx=10, pady=4)


def _field_row(parent, items, row, var_dict):
    for label, key, col in items:
        ctk.CTkLabel(
            parent, text=label, text_color="gray",
            font=ctk.CTkFont(size=11), anchor="w"
        ).grid(row=row, column=col * 2, padx=(10, 2), pady=(6, 0), sticky="w")
        var_dict[key] = ctk.StringVar()
        ctk.CTkEntry(parent, textvariable=var_dict[key], height=32
                     ).grid(row=row + 1, column=col * 2,
                            padx=(10, 2), pady=(0, 2), sticky="ew")


# ── Dialog class ──────────────────────────────────────────────────────────────

class EditEvaluationDialog(ctk.CTkToplevel):
    """
    Opens a full-form modal to edit an existing anthropometric record.
    Recalculates derived values in real time as the user types.
    """

    def __init__(self, parent, rec: dict, patient: dict, on_save):
        super().__init__(parent)
        self._rec     = rec
        self._patient = patient
        self._on_save = on_save          # callback fired after a successful save

        self._vars:          dict[str, ctk.StringVar]  = {}
        self._result_labels: dict[str, ctk.CTkLabel]   = {}
        self._isak_level   = ctk.StringVar(value=rec.get("isak_level") or "ISAK 1")
        self._date_entry   = None
        self._isak2_frame  = None
        self._isak2_res    = None

        session_date = (rec.get("session_date") or rec.get("date", "?"))[:10]
        self.title(f"Editar evaluación — {session_date}")
        self.geometry("1040x740")
        self.minsize(820, 580)
        self.grab_set()
        self.attributes("-topmost", True)
        self.after(50, lambda: self.attributes("-topmost", False))

        self._build_ui(session_date)
        self._setup_traces()
        self._preload()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self, session_date: str):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Warning banner ────────────────────────────────────────────────────
        banner = ctk.CTkFrame(self, fg_color=("#fefce8", "#2d2a0a"), corner_radius=8)
        banner.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            banner,
            text=(f"✏️  Estás editando la sesión del {session_date}. "
                  "Los cambios actualizarán todos los reportes."),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#92400e", "#fde68a"),
        ).pack(side="left", padx=14, pady=10)

        # ── ISAK level selector ───────────────────────────────────────────────
        level_bar = ctk.CTkFrame(self, fg_color=("#f0fdf4", "#1a2e22"), corner_radius=8)
        level_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 0))
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

        # ── Scrollable form ───────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 0))
        scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        f = scroll

        # DATOS BÁSICOS
        _section_label(f, "DATOS BÁSICOS", row=0, cols=4)
        ctk.CTkLabel(f, text="Fecha de la sesión *",
                     text_color=("#1a6b3c", "#4ade80"),
                     font=ctk.CTkFont(size=11, weight="bold"), anchor="w"
                     ).grid(row=1, column=0, padx=(10, 2), pady=(6, 0), sticky="w")
        today = date.today()
        if _CAL_OK:
            self._date_entry = _DateEntry(
                f, year=today.year, month=today.month, day=today.day,
                date_pattern="yyyy-mm-dd", width=14,
                background="#1a6b3c", foreground="white",
                selectbackground="#16a34a", font=("Segoe UI", 11),
            )
            self._date_entry.grid(row=2, column=0, padx=(10, 2), pady=(0, 2), sticky="w")
        else:
            self._vars["session_date"] = ctk.StringVar(value=today.isoformat())
            ctk.CTkEntry(f, textvariable=self._vars["session_date"], height=32,
                         placeholder_text="YYYY-MM-DD"
                         ).grid(row=2, column=0, padx=(10, 2), pady=(0, 2), sticky="ew")

        for label, key, col in [
            ("Peso (kg)",                 "weight_kg", 1),
            ("Talla (cm)",                "height_cm", 2),
            ("Circ. cintura mínima (cm)", "waist_cm",  3),
        ]:
            ctk.CTkLabel(f, text=label, text_color="gray",
                         font=ctk.CTkFont(size=11), anchor="w"
                         ).grid(row=1, column=col * 2, padx=(10, 2), pady=(6, 0), sticky="w")
            self._vars[key] = ctk.StringVar()
            ctk.CTkEntry(f, textvariable=self._vars[key], height=32
                         ).grid(row=2, column=col * 2, padx=(10, 2), pady=(0, 2), sticky="ew")

        # PERÍMETROS
        _section_label(f, "PERÍMETROS (cm)", row=3, cols=4)
        for label, key, frow, col in [
            ("Brazo relajado (BR)",  "arm_relaxed_cm",    4, 0),
            ("Brazo contraído (BC)", "arm_contracted_cm", 4, 1),
            ('Cadera "glúteo"',      "hip_glute_cm",      4, 2),
            ("Muslo máximo",         "thigh_max_cm",      4, 3),
            ("Muslo medio",          "thigh_mid_cm",      6, 0),
            ("Pantorrilla",          "calf_cm",           6, 1),
        ]:
            ctk.CTkLabel(f, text=label, text_color="gray",
                         font=ctk.CTkFont(size=11), anchor="w"
                         ).grid(row=frow, column=col * 2,
                                padx=(10, 2), pady=(6, 0), sticky="w")
            self._vars[key] = ctk.StringVar()
            ctk.CTkEntry(f, textvariable=self._vars[key], height=32
                         ).grid(row=frow + 1, column=col * 2,
                                padx=(10, 2), pady=(0, 2), sticky="ew")

        # PLIEGUES
        _section_label(f, "PLIEGUES CUTÁNEOS (mm)", row=8, cols=4)
        for label, key, frow, col in [
            ("Tríceps (*)",          "triceps_mm",      9,  0),
            ("Subescapular (*)",     "subscapular_mm",  9,  1),
            ("Bíceps",               "biceps_mm",       9,  2),
            ("Cresta iliaca",        "iliac_crest_mm",  9,  3),
            ("Supraespinal (*)",     "supraspinal_mm",  11, 0),
            ("Abdominal (*)",        "abdominal_mm",    11, 1),
            ("Muslo medial (*)",     "medial_thigh_mm", 11, 2),
            ("Pantorrilla máx. (*)", "max_calf_mm",     11, 3),
        ]:
            ctk.CTkLabel(f, text=label, text_color="gray",
                         font=ctk.CTkFont(size=11), anchor="w"
                         ).grid(row=frow, column=col * 2,
                                padx=(10, 2), pady=(6, 0), sticky="w")
            self._vars[key] = ctk.StringVar()
            ctk.CTkEntry(f, textvariable=self._vars[key], height=32
                         ).grid(row=frow + 1, column=col * 2,
                                padx=(10, 2), pady=(0, 2), sticky="ew")

        ctk.CTkLabel(f, text="Σ 6 pliegues (*) — auto",
                     text_color="#1a6b3c",
                     font=ctk.CTkFont(size=11, weight="bold"), anchor="w"
                     ).grid(row=13, column=0, padx=(10, 2), pady=(6, 0), sticky="w")
        self._vars["sum_6_skinfolds"] = ctk.StringVar(value="—")
        ctk.CTkEntry(f, textvariable=self._vars["sum_6_skinfolds"],
                     height=32, state="disabled",
                     fg_color=("#e8f5ee", "#1a3a28")
                     ).grid(row=14, column=0, padx=(10, 2), pady=(0, 2), sticky="ew")

        # ISAK 2 extra fields (hidden by default if ISAK 1)
        self._isak2_frame = ctk.CTkFrame(f, fg_color="transparent")
        self._isak2_frame.grid(row=15, column=0, columnspan=8, sticky="ew")
        self._isak2_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        self._build_isak2_fields(self._isak2_frame)
        if self._isak_level.get() != "ISAK 2":
            self._isak2_frame.grid_remove()

        # ── Results panel (real-time) ─────────────────────────────────────────
        res = ctk.CTkFrame(f, fg_color=("#f0fdf4", "#1a2e22"), corner_radius=10)
        res.grid(row=16, column=0, columnspan=8, padx=8, pady=(12, 4), sticky="ew")
        res.grid_columnconfigure(tuple(range(8)), weight=1)

        result_items = [
            ("dif_br_bc", "Dif. BC − BR"),
            ("sum6",      "Σ 6 pliegues"),
            ("fat_pct",   "% Masa grasa*"),
            ("fat_kg",    "Masa grasa (kg)"),
            ("lean_kg",   "Masa magra (kg)"),
            ("bmi",       "IMC (kg/m²)"),
            ("whr",       "Índice C/Cadera"),
            ("whtr",      "Índice C/Talla"),
        ]
        for col, (key, label) in enumerate(result_items):
            frm = ctk.CTkFrame(res, fg_color="transparent")
            frm.grid(row=0, column=col, padx=8, pady=8, sticky="ew")
            ctk.CTkLabel(frm, text=label,
                         font=ctk.CTkFont(size=9), text_color="gray"
                         ).pack(anchor="w")
            lbl = ctk.CTkLabel(frm, text="—",
                               font=ctk.CTkFont(size=13, weight="bold"))
            lbl.pack(anchor="w")
            self._result_labels[key] = lbl

        ctk.CTkLabel(
            res, text="*Durnin & Womersley (1974)",
            font=ctk.CTkFont(size=9), text_color="gray"
        ).grid(row=1, column=0, columnspan=8, padx=12, pady=(0, 6), sticky="w")

        # ISAK 2 results
        self._isak2_res = ctk.CTkFrame(
            f, fg_color=("#e8f5ee", "#1a3a28"), corner_radius=10)
        self._isak2_res.grid(row=17, column=0, columnspan=8,
                             padx=8, pady=(4, 16), sticky="ew")
        self._isak2_res.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        for col, (key, label) in enumerate([
            ("endo", "Endomorfia"),
            ("meso", "Mesomorfia"),
            ("ecto", "Ectomorfia"),
            ("whtr2", "Índ. Cintura/Talla"),
            ("amb",  "AMB (cm²)"),
        ]):
            frm2 = ctk.CTkFrame(self._isak2_res, fg_color="transparent")
            frm2.grid(row=0, column=col, padx=12, pady=8, sticky="ew")
            ctk.CTkLabel(frm2, text=label,
                         font=ctk.CTkFont(size=9), text_color="gray"
                         ).pack(anchor="w")
            lbl2 = ctk.CTkLabel(frm2, text="—",
                                font=ctk.CTkFont(size=13, weight="bold"))
            lbl2.pack(anchor="w")
            self._result_labels[f"isak2_{key}"] = lbl2
        ctk.CTkLabel(
            self._isak2_res,
            text="*Heath & Carter (1990)",
            font=ctk.CTkFont(size=9), text_color="gray"
        ).grid(row=1, column=0, columnspan=5, padx=12, pady=(0, 6), sticky="w")
        if self._isak_level.get() != "ISAK 2":
            self._isak2_res.grid_remove()

        # ── Action buttons ────────────────────────────────────────────────────
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 16))
        btn_bar.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            btn_bar, text="💾  Guardar cambios", height=44,
            fg_color="#16a34a", hover_color="#15803d",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(
            btn_bar, text="Cancelar", height=44,
            fg_color=("#9ca3af", "#4b5563"), hover_color=("#6b7280", "#374151"),
            command=self.destroy
        ).grid(row=0, column=1, sticky="ew")

    def _build_isak2_fields(self, f):
        _section_label(f, "PLIEGUES CUTÁNEOS ADICIONALES (mm)", row=0, cols=4)
        _field_row(f, [
            ("Pectoral (tórax)",   "pectoral_mm",    0),
            ("Axilar medio",       "axillary_mm",    1),
            ("Muslo anterior",     "front_thigh_mm", 2),
        ], row=1, var_dict=self._vars)

        _section_label(f, "PERÍMETROS ADICIONALES (cm)", row=3, cols=4)
        _field_row(f, [
            ("Cabeza",              "head_cm",      0),
            ("Cuello",              "neck_cm",      1),
            ("Tórax mesoesternal",  "chest_cm",     2),
            ("Tobillo mínimo",      "ankle_min_cm", 3),
        ], row=4, var_dict=self._vars)

        _section_label(f, "DIÁMETROS ÓSEOS (cm)", row=6, cols=4)
        _field_row(f, [
            ("Húmero bicondíleo",   "humerus_width_cm",  0),
            ("Fémur bicondíleo",    "femur_width_cm",    1),
            ("Biacromial",          "biacromial_cm",     2),
            ("Biiliocrestal",       "biiliocrestal_cm",  3),
        ], row=7, var_dict=self._vars)
        _field_row(f, [
            ("Ant-post. tórax",     "ap_chest_cm",       0),
            ("Transv. tórax",       "transv_chest_cm",   1),
            ("Longitud pie",        "foot_length_cm",    2),
            ("Muñeca biestiloideo", "wrist_cm",          3),
        ], row=9, var_dict=self._vars)
        _field_row(f, [
            ("Tobillo bimaleolar",  "ankle_bimalleolar_cm", 0),
        ], row=11, var_dict=self._vars)

        _section_label(f, "LONGITUDES (cm)", row=13, cols=4)
        _field_row(f, [
            ("Acromio-radial",       "acromion_radial_cm",   0),
            ("Radio-estiloide",      "radial_styloid_cm",    1),
            ("Iliospinal (pierna)",  "iliospinal_height_cm", 2),
            ("Trocánter-tibial",     "trochanter_tibial_cm", 3),
        ], row=14, var_dict=self._vars)

    # ── Traces and real-time calculation ─────────────────────────────────────

    def _setup_traces(self):
        skip = {"sum_6_skinfolds", "session_date"}
        for key, var in self._vars.items():
            if key not in skip:
                var.trace_add("write", lambda *_: self._recalculate())

    def _toggle_isak_level(self, value):
        if value == "ISAK 2":
            self._isak2_frame.grid()
            self._isak2_res.grid()
        else:
            self._isak2_frame.grid_remove()
            self._isak2_res.grid_remove()
        self._recalculate()

    def _gf(self, key) -> Optional[float]:
        try:
            v = self._vars.get(key)
            s = v.get().strip() if v else ""
            return float(s) if s else None
        except ValueError:
            return None

    def _recalculate(self):
        sex = self._patient.get("sex", "Femenino")
        age = self._patient.get("age") or 30
        w     = self._gf("weight_kg")
        h     = self._gf("height_cm")
        waist = self._gf("waist_cm")
        hip   = self._gf("hip_glute_cm")
        br    = self._gf("arm_relaxed_cm")
        bc    = self._gf("arm_contracted_cm")

        # Dif. BR-BC
        dif = round(bc - br, 2) if (br is not None and bc is not None) else None
        self._result_labels["dif_br_bc"].configure(
            text=f"{dif:+.2f} cm" if dif is not None else "—"
        )

        # Σ 6 pliegues
        s6 = calc.sum_6_skinfolds(
            self._gf("triceps_mm"),      self._gf("subscapular_mm"),
            self._gf("supraspinal_mm"),  self._gf("abdominal_mm"),
            self._gf("medial_thigh_mm"), self._gf("max_calf_mm"),
        )
        self._result_labels["sum6"].configure(
            text=f"{s6} mm" if s6 is not None else "—"
        )
        self._vars["sum_6_skinfolds"].set(f"{s6} mm" if s6 is not None else "—")

        # Durnin & Womersley
        bi = self._gf("biceps_mm"); tr = self._gf("triceps_mm")
        ss = self._gf("subscapular_mm"); ic = self._gf("iliac_crest_mm")
        density = fat_pct = None
        if all(v is not None for v in [bi, tr, ss, ic]):
            density, fat_pct = calc.body_fat_durnin_womersley(bi, tr, ss, ic, age, sex)
        fat_kg  = calc.fat_mass_kg(w, fat_pct) if (fat_pct is not None and w) else None
        lean_kg = calc.lean_mass_kg(w, fat_kg) if fat_kg is not None else None
        self._result_labels["fat_pct"].configure(
            text=f"{fat_pct}%" if fat_pct is not None else "—"
        )
        self._result_labels["fat_kg"].configure(
            text=f"{fat_kg} kg" if fat_kg is not None else "—"
        )
        self._result_labels["lean_kg"].configure(
            text=f"{lean_kg} kg" if lean_kg is not None else "—"
        )

        # IMC
        bmi_val = calc.bmi(w, h) if (w and h) else None
        self._result_labels["bmi"].configure(
            text=str(bmi_val) if bmi_val is not None else "—"
        )

        # WHR
        whr_val = calc.waist_hip_ratio(waist, hip) if (waist and hip) else None
        self._result_labels["whr"].configure(
            text=str(whr_val) if whr_val is not None else "—"
        )

        # WHtR
        whtr_val = calc.waist_height_ratio(waist, h) if (waist and h) else None
        self._result_labels["whtr"].configure(
            text=str(whtr_val) if whtr_val is not None else "—"
        )

        # ISAK 2
        if self._isak_level.get() == "ISAK 2":
            endo, meso, ecto = calc.somatotype_heath_carter(
                h, w,
                self._gf("triceps_mm"),      self._gf("subscapular_mm"),
                self._gf("supraspinal_mm"),
                self._gf("humerus_width_cm"), self._gf("femur_width_cm"),
                self._gf("arm_contracted_cm"), self._gf("calf_cm"),
                self._gf("max_calf_mm"),
            )
            amb = calc.arm_muscle_area(self._gf("arm_relaxed_cm"), self._gf("triceps_mm"))
            self._result_labels["isak2_endo"].configure(
                text=str(endo) if endo is not None else "—"
            )
            self._result_labels["isak2_meso"].configure(
                text=str(meso) if meso is not None else "—"
            )
            self._result_labels["isak2_ecto"].configure(
                text=str(ecto) if ecto is not None else "—"
            )
            self._result_labels["isak2_whtr2"].configure(
                text=str(whtr_val) if whtr_val is not None else "—"
            )
            self._result_labels["isak2_amb"].configure(
                text=str(amb) if amb is not None else "—"
            )

    # ── Preload from record ───────────────────────────────────────────────────

    def _preload(self):
        r   = self._rec
        sd  = (r.get("session_date") or r.get("date", ""))[:10]

        if _CAL_OK and self._date_entry is not None:
            try:
                parts = sd.split("-")
                self._date_entry.set_date(
                    date(int(parts[0]), int(parts[1]), int(parts[2]))
                )
            except Exception:
                pass
        elif "session_date" in self._vars:
            self._vars["session_date"].set(sd)

        fields = [
            "weight_kg", "height_cm", "waist_cm",
            "arm_relaxed_cm", "arm_contracted_cm", "hip_glute_cm",
            "thigh_max_cm", "thigh_mid_cm", "calf_cm",
            "triceps_mm", "subscapular_mm", "biceps_mm", "iliac_crest_mm",
            "supraspinal_mm", "abdominal_mm", "medial_thigh_mm", "max_calf_mm",
            "pectoral_mm", "axillary_mm", "front_thigh_mm",
            "head_cm", "neck_cm", "chest_cm", "ankle_min_cm",
            "humerus_width_cm", "femur_width_cm", "biacromial_cm",
            "biiliocrestal_cm", "ap_chest_cm", "transv_chest_cm",
            "foot_length_cm", "wrist_cm", "ankle_bimalleolar_cm",
            "acromion_radial_cm", "radial_styloid_cm",
            "iliospinal_height_cm", "trochanter_tibial_cm",
        ]
        for key in fields:
            if key in self._vars:
                v = r.get(key)
                if v is not None:
                    self._vars[key].set(str(v))

        self._recalculate()

    # ── Save ─────────────────────────────────────────────────────────────────

    def _get_session_date(self) -> str:
        if _CAL_OK and self._date_entry is not None:
            try:
                return self._date_entry.get_date().isoformat()
            except Exception:
                pass
        v = self._vars.get("session_date")
        return v.get().strip() if v else date.today().isoformat()

    def _save(self):
        w = self._gf("weight_kg")
        if not w:
            messagebox.showerror("Datos incompletos",
                                 "El peso es obligatorio.", parent=self)
            return

        sex = self._patient.get("sex", "Femenino")
        age = self._patient.get("age") or 30
        h     = self._gf("height_cm")
        waist = self._gf("waist_cm")

        bi = self._gf("biceps_mm"); tr = self._gf("triceps_mm")
        ss = self._gf("subscapular_mm"); ic = self._gf("iliac_crest_mm")
        density = fat_pct = None
        if all(v is not None for v in [bi, tr, ss, ic]):
            density, fat_pct = calc.body_fat_durnin_womersley(bi, tr, ss, ic, age, sex)
        fat_kg  = calc.fat_mass_kg(w, fat_pct) if (fat_pct is not None and w) else None
        lean_kg = calc.lean_mass_kg(w, fat_kg) if fat_kg is not None else None

        s6 = calc.sum_6_skinfolds(
            self._gf("triceps_mm"),      self._gf("subscapular_mm"),
            self._gf("supraspinal_mm"),  self._gf("abdominal_mm"),
            self._gf("medial_thigh_mm"), self._gf("max_calf_mm"),
        )

        endo = meso = ecto = whtr = amb = None
        if self._isak_level.get() == "ISAK 2":
            endo, meso, ecto = calc.somatotype_heath_carter(
                h, w,
                self._gf("triceps_mm"),      self._gf("subscapular_mm"),
                self._gf("supraspinal_mm"),
                self._gf("humerus_width_cm"), self._gf("femur_width_cm"),
                self._gf("arm_contracted_cm"), self._gf("calf_cm"),
                self._gf("max_calf_mm"),
            )
            whtr = calc.waist_height_ratio(waist, h)
            amb  = calc.arm_muscle_area(self._gf("arm_relaxed_cm"), self._gf("triceps_mm"))

        data = {
            "id":                   self._rec["id"],
            "session_date":         self._get_session_date(),
            "isak_level":           self._isak_level.get(),
            "weight_kg":            self._gf("weight_kg"),
            "height_cm":            self._gf("height_cm"),
            "waist_cm":             self._gf("waist_cm"),
            "arm_relaxed_cm":       self._gf("arm_relaxed_cm"),
            "arm_contracted_cm":    self._gf("arm_contracted_cm"),
            "hip_glute_cm":         self._gf("hip_glute_cm"),
            "thigh_max_cm":         self._gf("thigh_max_cm"),
            "thigh_mid_cm":         self._gf("thigh_mid_cm"),
            "calf_cm":              self._gf("calf_cm"),
            "triceps_mm":           self._gf("triceps_mm"),
            "subscapular_mm":       self._gf("subscapular_mm"),
            "biceps_mm":            self._gf("biceps_mm"),
            "iliac_crest_mm":       self._gf("iliac_crest_mm"),
            "supraspinal_mm":       self._gf("supraspinal_mm"),
            "abdominal_mm":         self._gf("abdominal_mm"),
            "medial_thigh_mm":      self._gf("medial_thigh_mm"),
            "max_calf_mm":          self._gf("max_calf_mm"),
            "pectoral_mm":          self._gf("pectoral_mm"),
            "axillary_mm":          self._gf("axillary_mm"),
            "front_thigh_mm":       self._gf("front_thigh_mm"),
            "head_cm":              self._gf("head_cm"),
            "neck_cm":              self._gf("neck_cm"),
            "chest_cm":             self._gf("chest_cm"),
            "ankle_min_cm":         self._gf("ankle_min_cm"),
            "humerus_width_cm":     self._gf("humerus_width_cm"),
            "femur_width_cm":       self._gf("femur_width_cm"),
            "biacromial_cm":        self._gf("biacromial_cm"),
            "biiliocrestal_cm":     self._gf("biiliocrestal_cm"),
            "ap_chest_cm":          self._gf("ap_chest_cm"),
            "transv_chest_cm":      self._gf("transv_chest_cm"),
            "foot_length_cm":       self._gf("foot_length_cm"),
            "wrist_cm":             self._gf("wrist_cm"),
            "ankle_bimalleolar_cm": self._gf("ankle_bimalleolar_cm"),
            "acromion_radial_cm":   self._gf("acromion_radial_cm"),
            "radial_styloid_cm":    self._gf("radial_styloid_cm"),
            "iliospinal_height_cm": self._gf("iliospinal_height_cm"),
            "trochanter_tibial_cm": self._gf("trochanter_tibial_cm"),
            # Calculated
            "sum_6_skinfolds":      s6,
            "body_density":         density,
            "fat_mass_pct":         fat_pct,
            "fat_mass_kg":          fat_kg,
            "lean_mass_kg":         lean_kg,
            "somatotype_endo":      endo,
            "somatotype_meso":      meso,
            "somatotype_ecto":      ecto,
            "waist_height_ratio":   whtr,
            "arm_muscle_area":      amb,
        }

        db.update_anthropometric(data)
        self.destroy()
        self._on_save()
