import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import date
from typing import Optional
import database.db_manager as db
import utils.calculations as calc
from views.edit_evaluation_dialog import EditEvaluationDialog
from views.compare_sessions_dialog import CompareSessionsDialog

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _MPL_OK = True
except ImportError:
    _MPL_OK = False

try:
    from tkcalendar import DateEntry as _DateEntry
    _CAL_OK = True
except ImportError:
    _CAL_OK = False


def _rec_date(r: dict) -> str:
    """Return the session date for display (falls back to system date)."""
    return r.get("session_date") or r.get("date", "—") or "—"


def _section_label(parent, text, row, cols=4):
    frm = ctk.CTkFrame(parent, fg_color=("#e0ede8", "#2f5a40"), corner_radius=6)
    frm.grid(row=row, column=0, columnspan=cols * 2,
             padx=8, pady=(14, 2), sticky="ew")
    ctk.CTkLabel(
        frm, text=text,
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=("#4b7c60", "#6ee7b7")
    ).pack(side="left", padx=10, pady=4)


def _field_row(parent, items, row, var_dict):
    for label, key, col in items:
        ctk.CTkLabel(
            parent, text=label, text_color="gray",
            font=ctk.CTkFont(size=11), anchor="w"
        ).grid(row=row, column=col * 2, padx=(10, 2), pady=(6, 0), sticky="w")
        var_dict[key] = ctk.StringVar()
        ctk.CTkEntry(parent, textvariable=var_dict[key], height=36
                     ).grid(row=row + 1, column=col * 2,
                            padx=(10, 2), pady=(0, 2), sticky="ew")


class AnthropometricFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app
        self._vars: dict[str, ctk.StringVar] = {}
        self._result_labels: dict[str, ctk.CTkLabel] = {}
        self._class_labels:  dict[str, ctk.CTkLabel] = {}
        self._last_calc: dict = {}
        self._isak_level = ctk.StringVar(value="ISAK 1")
        self._isak2_frame = None
        self._evo_figures: list = []
        self._date_entry = None  # tkcalendar DateEntry widget (if available)
        self._compare_vars: dict[int, ctk.BooleanVar] = {}
        self._compare_btn = None
        self._build_ui()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, minsize=260, weight=0)   # left panel fixed
        self.grid_columnconfigure(1, weight=1)                # right panel expands
        self.grid_rowconfigure(0, weight=1)

        # ── LEFT PANEL: patient profile ──────────────────────────────────────
        self._left_panel = ctk.CTkFrame(
            self, width=260, corner_radius=0,
            fg_color=("white", "#141f19"),
            border_width=1, border_color=("#E5EAE7", "#2a3d30")
        )
        self._left_panel.grid(row=0, column=0, sticky="nsew")
        self._left_panel.grid_propagate(False)
        self._left_panel.grid_columnconfigure(0, weight=1)
        self._build_left_panel()

        # ── RIGHT PANEL: tabs ────────────────────────────────────────────────
        right = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        # Tabs (top bar)
        self._tabs = ctk.CTkTabview(right, command=self._on_tab_change)
        self._tabs.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=16, pady=12)
        self._tabs.add("Nueva evaluación")
        self._tabs.add("Historial")
        self._tabs.add("Evolución")

        self._build_form_tab(self._tabs.tab("Nueva evaluación"))
        self._build_history_tab(self._tabs.tab("Historial"))
        self._build_evolution_tab(self._tabs.tab("Evolución"))

        # Keep a label ref for backwards compat (on_show updates it)
        self._patient_lbl = ctk.CTkLabel(
            right, text="", font=ctk.CTkFont(size=13), text_color="gray"
        )

    def _build_left_panel(self):
        p = self._left_panel

        # Avatar circle
        self._avatar_lbl = ctk.CTkLabel(
            p, text="?", width=80, height=80,
            corner_radius=40,
            fg_color=("#8da399", "#2a3d30"),
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=("#4b7c60", "#6ec896")
        )
        self._avatar_lbl.grid(row=0, column=0, pady=(30, 8))

        self._name_lbl = ctk.CTkLabel(
            p, text="Ningún paciente",
            font=ctk.CTkFont(size=16, weight="bold"),
            wraplength=220
        )
        self._name_lbl.grid(row=1, column=0, padx=16, pady=(0, 2))

        self._patient_info_lbl = ctk.CTkLabel(
            p, text="Selecciona un paciente",
            font=ctk.CTkFont(size=11), text_color="#6b7280"
        )
        self._patient_info_lbl.grid(row=2, column=0, padx=16, pady=(0, 16))

        # Buttons
        btn_frame = ctk.CTkFrame(p, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=16, pady=(0, 12), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            btn_frame, text="✎  Editar Perfil", height=36,
            fg_color="#c06c52", hover_color="#a85a43",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.app.open_patient_form(self.app.get_patient_id())
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        ctk.CTkButton(
            btn_frame, text="＋  Nueva Evaluación", height=36,
            fg_color="#4b7c60", hover_color="#3d6b50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._new_evaluation
        ).grid(row=1, column=0, sticky="ew")

        # Separator
        ctk.CTkFrame(p, height=1, fg_color=("#E5EAE7", "#2a3d30")).grid(
            row=4, column=0, sticky="ew", padx=16, pady=16
        )

        # IMC card
        imc_card = ctk.CTkFrame(
            p, corner_radius=10,
            fg_color=("#4b7c60", "#1a2e22"),
            border_width=1, border_color=("#4b7c60", "#2a4030")
        )
        imc_card.grid(row=5, column=0, padx=16, pady=(0, 10), sticky="ew")
        imc_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            imc_card, text="ÚLTIMO IMC",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=("#4b7c60", "#6ec896")
        ).grid(row=0, column=0, padx=12, pady=(10, 0), sticky="w")

        self._imc_lbl = ctk.CTkLabel(
            imc_card, text="—",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=("#4b7c60", "#6ec896")
        )
        self._imc_lbl.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")

        # Estado
        estado_card = ctk.CTkFrame(
            p, corner_radius=10,
            fg_color="transparent",
            border_width=1, border_color=("#E5EAE7", "#2a3d30")
        )
        estado_card.grid(row=6, column=0, padx=16, pady=(0, 20), sticky="ew")
        estado_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            estado_card, text="ESTADO GENERAL",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#6b7280"
        ).grid(row=0, column=0, padx=12, pady=(10, 0), sticky="w")

        self._estado_lbl = ctk.CTkLabel(
            estado_card, text="—",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self._estado_lbl.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")

    def _new_evaluation(self):
        """Clear form fields and focus the Nueva evaluación tab."""
        for var in self._vars.values():
            var.set("")
        self._vars["sum_6_skinfolds"].set("—")
        if _CAL_OK and self._date_entry is not None:
            self._date_entry.set_date(date.today())
        elif "session_date" in self._vars:
            self._vars["session_date"].set(date.today().isoformat())
        self._tabs.set("Nueva evaluación")

    def _refresh_left_panel(self, p):
        from utils.image_helpers import get_initials
        name = p.get("name", "—")
        self._name_lbl.configure(text=name)
        age = f"{p.get('age')} años" if p.get("age") else ""
        pid = self.app.get_patient_id()
        if pid:
            records = db.get_anthropometrics(pid)
            if records:
                last = records[-1]
                w = last.get("weight_kg")
                h = last.get("height_cm") or p.get("height_cm")
                if w and h:
                    bmi = calc.bmi(float(w), float(h))
                    bmi_str = f"{bmi:.1f}"
                    cls_text, _ = calc.classify_bmi(bmi)
                    self._patient_info_lbl.configure(
                        text=f"{age}  •  IMC {bmi_str}  •  {cls_text}"
                    )
                    self._imc_lbl.configure(text=bmi_str)
                    self._estado_lbl.configure(text=cls_text)
                else:
                    self._patient_info_lbl.configure(text=age or "Sin datos")
                    self._imc_lbl.configure(text="—")
                    self._estado_lbl.configure(text="—")
            else:
                self._patient_info_lbl.configure(text=age or "Sin datos")
                self._imc_lbl.configure(text="—")
                self._estado_lbl.configure(text="—")
        initials = get_initials(name)[:2]
        self._avatar_lbl.configure(text=initials)

    # ── Form tab ──────────────────────────────────────────────────────────────
    def _build_form_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # ISAK level selector
        level_bar = ctk.CTkFrame(tab, fg_color=("#e8f5ee", "#1a2e22"), corner_radius=8)
        level_bar.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 0))
        ctk.CTkLabel(
            level_bar, text="Nivel ISAK:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#4b7c60", "#6ec896")
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
        ).pack(side="left", padx=16)

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        f = scroll

        # ── DATOS BÁSICOS ──────────────────────────────────────────────────
        _section_label(f, "DATOS BÁSICOS", row=0, cols=4)
        ctk.CTkLabel(f, text="Fecha de la sesión *",
                     text_color=("#4b7c60", "#6ec896"),
                     font=ctk.CTkFont(size=11, weight="bold"), anchor="w"
                     ).grid(row=1, column=0, padx=(10, 2), pady=(6, 0), sticky="w")
        today = date.today()
        if _CAL_OK:
            self._date_entry = _DateEntry(
                f, year=today.year, month=today.month, day=today.day,
                date_pattern="yyyy-mm-dd", width=14,
                background="#4b7c60", foreground="white",
                selectbackground="#3d6b50", font=("Segoe UI", 11),
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

        # ── PERÍMETROS ─────────────────────────────────────────────────────
        _section_label(f, "PERÍMETROS (cm)", row=3, cols=4)
        for label, key, row, col in [
            ("Brazo relajado (BR)",  "arm_relaxed_cm",   4, 0),
            ("Brazo contraído (BC)", "arm_contracted_cm", 4, 1),
            ('Cadera "glúteo"',      "hip_glute_cm",      4, 2),
            ("Muslo máximo",         "thigh_max_cm",      4, 3),
            ("Muslo medio",          "thigh_mid_cm",      6, 0),
            ("Pantorrilla",          "calf_cm",           6, 1),
        ]:
            ctk.CTkLabel(f, text=label, text_color="gray",
                         font=ctk.CTkFont(size=11), anchor="w"
                         ).grid(row=row, column=col * 2, padx=(10, 2), pady=(6, 0), sticky="w")
            self._vars[key] = ctk.StringVar()
            ctk.CTkEntry(f, textvariable=self._vars[key], height=32
                         ).grid(row=row + 1, column=col * 2, padx=(10, 2), pady=(0, 2), sticky="ew")

        # ── PLIEGUES CUTÁNEOS ──────────────────────────────────────────────
        _section_label(f, "PLIEGUES CUTÁNEOS (mm)", row=8, cols=4)
        for label, key, row, col in [
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
                         ).grid(row=row, column=col * 2, padx=(10, 2), pady=(6, 0), sticky="w")
            self._vars[key] = ctk.StringVar()
            ent = ctk.CTkEntry(f, textvariable=self._vars[key], height=32)
            ent.grid(row=row + 1, column=col * 2, padx=(10, 2), pady=(0, 2), sticky="ew")
            self._vars[key].trace_add("write", lambda *_: self._update_sum())

        ctk.CTkLabel(f, text="Σ 6 pliegues (*) — auto",
                     text_color="#4b7c60",
                     font=ctk.CTkFont(size=11, weight="bold"), anchor="w"
                     ).grid(row=13, column=0, padx=(10, 2), pady=(6, 0), sticky="w")
        self._vars["sum_6_skinfolds"] = ctk.StringVar(value="—")
        ctk.CTkEntry(f, textvariable=self._vars["sum_6_skinfolds"],
                     height=32, state="disabled",
                     fg_color=("#e8f5ee", "#1a3a28")
                     ).grid(row=14, column=0, padx=(10, 2), pady=(0, 2), sticky="ew")

        # ── ISAK 2 EXTRA FIELDS ────────────────────────────────────────────
        self._isak2_frame = ctk.CTkFrame(f, fg_color="transparent")
        self._isak2_frame.grid(row=15, column=0, columnspan=8, sticky="ew")
        self._isak2_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        self._build_isak2_fields(self._isak2_frame)
        self._isak2_frame.grid_remove()

        # ── BUTTONS ────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(f, fg_color="transparent")
        btn_row.grid(row=16, column=0, columnspan=8, padx=8, pady=(14, 6), sticky="ew")
        btn_row.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(btn_row, text="Calcular", height=40,
                      command=self._calculate
                      ).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(btn_row, text="Guardar evaluación", height=40,
                      fg_color="#4b7c60", hover_color="#3d6b50",
                      command=self._save
                      ).grid(row=0, column=1, sticky="ew")

        # ── RESULTS BOX (ISAK 1) ───────────────────────────────────────────
        res = ctk.CTkFrame(f, fg_color=("#e8f5ee", "#1a2e22"), corner_radius=10)
        res.grid(row=17, column=0, columnspan=8, padx=8, pady=(8, 4), sticky="ew")
        res.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        # (key, label, has_classification)
        result_items = [
            ("dif_br_bc", "Diferencia BC - BR",  False),
            ("sum6",      "Σ 6 pliegues",         False),
            ("fat_pct",   "% Masa grasa (D&W)",   True),
            ("fat_kg",    "Masa grasa (kg)",       False),
            ("lean_kg",   "Masa magra (kg)",       False),
            ("bmi",       "IMC (kg/m²)",           True),
        ]
        for col, (key, label, has_cls) in enumerate(result_items):
            frm = ctk.CTkFrame(res, fg_color="transparent")
            frm.grid(row=0, column=col, padx=10, pady=10, sticky="ew")
            ctk.CTkLabel(frm, text=label,
                         font=ctk.CTkFont(size=9), text_color="gray"
                         ).pack(anchor="w")
            lbl = ctk.CTkLabel(frm, text="—",
                               font=ctk.CTkFont(size=15, weight="bold"))
            lbl.pack(anchor="w")
            self._result_labels[key] = lbl
            if has_cls:
                cls_lbl = ctk.CTkLabel(frm, text="",
                                       font=ctk.CTkFont(size=10))
                cls_lbl.pack(anchor="w")
                self._class_labels[key] = cls_lbl

        ctk.CTkLabel(
            res, text="*Ecuación Durnin & Womersley — Medición antropométrica ISAK 1",
            font=ctk.CTkFont(size=9), text_color="gray"
        ).grid(row=1, column=0, columnspan=6, padx=12, pady=(0, 8), sticky="w")

        # ── RESULTS BOX (ISAK 2) ───────────────────────────────────────────
        self._isak2_results_frame = ctk.CTkFrame(
            f, fg_color=("#e8f5ee", "#1a3a28"), corner_radius=10)
        self._isak2_results_frame.grid(row=18, column=0, columnspan=8,
                                       padx=8, pady=(4, 16), sticky="ew")
        self._isak2_results_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        result2_items = [
            ("endo",  "Endomorfia",           False),
            ("meso",  "Mesomorfia",           False),
            ("ecto",  "Ectomorfia",           False),
            ("whtr",  "Índ. Cintura/Talla",   True),
            ("amb",   "Área Musc. Brazo(cm²)",False),
        ]
        for col, (key, label, has_cls) in enumerate(result2_items):
            frm2 = ctk.CTkFrame(self._isak2_results_frame, fg_color="transparent")
            frm2.grid(row=0, column=col, padx=12, pady=10, sticky="ew")
            ctk.CTkLabel(frm2, text=label,
                         font=ctk.CTkFont(size=9), text_color="gray"
                         ).pack(anchor="w")
            lbl2 = ctk.CTkLabel(frm2, text="—",
                                font=ctk.CTkFont(size=15, weight="bold"))
            lbl2.pack(anchor="w")
            self._result_labels[f"isak2_{key}"] = lbl2
            if has_cls:
                cls_lbl2 = ctk.CTkLabel(frm2, text="",
                                        font=ctk.CTkFont(size=10))
                cls_lbl2.pack(anchor="w")
                self._class_labels[f"isak2_{key}"] = cls_lbl2

        ctk.CTkLabel(
            self._isak2_results_frame,
            text="*Somatotipo Heath & Carter (1990) — Medición antropométrica ISAK 2",
            font=ctk.CTkFont(size=9), text_color="gray"
        ).grid(row=1, column=0, columnspan=5, padx=12, pady=(0, 8), sticky="w")
        self._isak2_results_frame.grid_remove()

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

    # ── Evolution tab ─────────────────────────────────────────────────────────
    def _build_evolution_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))

        ctk.CTkButton(
            toolbar, text="↺ Actualizar gráficos", height=34, width=160,
            command=self._load_evolution
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            toolbar, text="Exportar PDF evolución", height=34, width=180,
            fg_color="#c06c52", hover_color="#a85a43",
            command=self._export_evolution_pdf
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            toolbar,
            text="Peso · %Grasa · Masa grasa · Masa magra · Σ6 pliegues · Cintura · IMC",
            font=ctk.CTkFont(size=10), text_color="gray"
        ).pack(side="left", padx=12)

        self._evo_scroll = ctk.CTkScrollableFrame(tab)
        self._evo_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

    # ── Tab change ────────────────────────────────────────────────────────────
    def _on_tab_change(self):
        if self._tabs.get() == "Evolución":
            self._load_evolution()

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
                self._refresh_left_panel(p)
                self._load_history()
                return
        self._patient_lbl.configure(text="Ningún paciente seleccionado")

    def _gf(self, key) -> Optional[float]:
        try:
            v = self._vars.get(key)
            if v is None:
                return None
            s = v.get().strip()
            return float(s) if s else None
        except ValueError:
            return None

    def _get_session_date(self) -> str:
        """Return the session date as ISO string (YYYY-MM-DD)."""
        if _CAL_OK and self._date_entry is not None:
            try:
                return self._date_entry.get_date().isoformat()
            except Exception:
                pass
        v = self._vars.get("session_date")
        return v.get().strip() if v else date.today().isoformat()

    def _update_sum(self):
        s = calc.sum_6_skinfolds(
            self._gf("triceps_mm"),     self._gf("subscapular_mm"),
            self._gf("supraspinal_mm"), self._gf("abdominal_mm"),
            self._gf("medial_thigh_mm"), self._gf("max_calf_mm"),
        )
        self._vars["sum_6_skinfolds"].set(f"{s} mm" if s is not None else "—")

    def _set_class(self, key, pct_or_val, classify_fn, *fn_args):
        """Helper: compute classification and update class label."""
        lbl = self._class_labels.get(key)
        if lbl is None:
            return
        if pct_or_val is None:
            lbl.configure(text="", text_color="gray")
            return
        try:
            cat, level = classify_fn(pct_or_val, *fn_args)
            emoji = calc.LEVEL_EMOJI.get(level, "")
            color = calc.LEVEL_COLOR.get(level, "gray")
            lbl.configure(text=f"{emoji} {cat}", text_color=color)
        except Exception:
            lbl.configure(text="", text_color="gray")

    def _calculate(self) -> bool:
        pid = self.app.get_patient_id()
        if not pid:
            messagebox.showwarning("Sin paciente", "Selecciona un paciente primero.")
            return False

        patient = db.get_patient(pid)
        sex = (patient or {}).get("sex", "Femenino")
        age = (patient or {}).get("age", 30) or 30

        w = self._gf("weight_kg")
        h = self._gf("height_cm")
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
            self._gf("triceps_mm"),     self._gf("subscapular_mm"),
            self._gf("supraspinal_mm"), self._gf("abdominal_mm"),
            self._gf("medial_thigh_mm"), self._gf("max_calf_mm"),
        )
        self._result_labels["sum6"].configure(
            text=f"{s6} mm" if s6 is not None else "—"
        )

        # Durnin & Womersley
        bi = self._gf("biceps_mm");  tr = self._gf("triceps_mm")
        ss = self._gf("subscapular_mm"); ic = self._gf("iliac_crest_mm")
        density, fat_pct = None, None
        if all(v is not None for v in [bi, tr, ss, ic]):
            density, fat_pct = calc.body_fat_durnin_womersley(bi, tr, ss, ic, age, sex)

        fat_kg  = calc.fat_mass_kg(w, fat_pct) if fat_pct is not None else None
        lean_kg = calc.lean_mass_kg(w, fat_kg) if fat_kg  is not None else None

        self._result_labels["fat_pct"].configure(
            text=f"{fat_pct}%" if fat_pct is not None else "—"
        )
        self._result_labels["fat_kg"].configure(
            text=f"{fat_kg} kg" if fat_kg is not None else "—"
        )
        self._result_labels["lean_kg"].configure(
            text=f"{lean_kg} kg" if lean_kg is not None else "—"
        )
        self._set_class("fat_pct", fat_pct, calc.classify_fat_pct, sex, age)

        # IMC + clasificación
        bmi_val = calc.bmi(w, h) if h else None
        self._result_labels["bmi"].configure(
            text=str(bmi_val) if bmi_val is not None else "—"
        )
        self._set_class("bmi", bmi_val, calc.classify_bmi)

        self._last_calc = {
            "dif_br_bc":       dif,
            "sum_6_skinfolds": s6,
            "body_density":    density,
            "fat_mass_pct":    fat_pct,
            "fat_mass_kg":     fat_kg,
            "lean_mass_kg":    lean_kg,
            "somatotype_endo": None,
            "somatotype_meso": None,
            "somatotype_ecto": None,
            "waist_height_ratio": None,
            "arm_muscle_area":  None,
        }

        # ── ISAK 2 calculations ────────────────────────────────────────────
        if self._isak_level.get() == "ISAK 2":
            endo, meso, ecto = calc.somatotype_heath_carter(
                h, w,
                self._gf("triceps_mm"),     self._gf("subscapular_mm"),
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

            waist = self._gf("waist_cm")
            whtr = calc.waist_height_ratio(waist, h)
            self._result_labels["isak2_whtr"].configure(
                text=f"{whtr}" if whtr is not None else "—"
            )
            self._set_class("isak2_whtr", whtr, calc.classify_whtr)

            amb = calc.arm_muscle_area(self._gf("arm_relaxed_cm"), self._gf("triceps_mm"))
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
            "session_date":       self._get_session_date(),
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
            "pectoral_mm":        self._gf("pectoral_mm"),
            "axillary_mm":        self._gf("axillary_mm"),
            "front_thigh_mm":     self._gf("front_thigh_mm"),
            "head_cm":            self._gf("head_cm"),
            "neck_cm":            self._gf("neck_cm"),
            "chest_cm":           self._gf("chest_cm"),
            "ankle_min_cm":       self._gf("ankle_min_cm"),
            "humerus_width_cm":   self._gf("humerus_width_cm"),
            "femur_width_cm":     self._gf("femur_width_cm"),
            "biacromial_cm":      self._gf("biacromial_cm"),
            "biiliocrestal_cm":   self._gf("biiliocrestal_cm"),
            "ap_chest_cm":        self._gf("ap_chest_cm"),
            "transv_chest_cm":    self._gf("transv_chest_cm"),
            "foot_length_cm":     self._gf("foot_length_cm"),
            "wrist_cm":           self._gf("wrist_cm"),
            "ankle_bimalleolar_cm": self._gf("ankle_bimalleolar_cm"),
            "acromion_radial_cm": self._gf("acromion_radial_cm"),
            "radial_styloid_cm":  self._gf("radial_styloid_cm"),
            "iliospinal_height_cm": self._gf("iliospinal_height_cm"),
            "trochanter_tibial_cm": self._gf("trochanter_tibial_cm"),
            **self._last_calc,
        }
        db.insert_anthropometric(data)
        messagebox.showinfo("Guardado", f"Evaluación {level} guardada correctamente.")
        self._clear_form()
        self._load_history()
        self._tabs.set("Historial")

    def _clear_form(self):
        skip = {"session_date", "sum_6_skinfolds"}
        for key, var in self._vars.items():
            if key not in skip:
                var.set("")
        self._vars["sum_6_skinfolds"].set("—")
        # Reset date picker to today
        if _CAL_OK and self._date_entry is not None:
            self._date_entry.set_date(date.today())
        elif "session_date" in self._vars:
            self._vars["session_date"].set(date.today().isoformat())
        for lbl in self._result_labels.values():
            lbl.configure(text="—")
        for lbl in self._class_labels.values():
            lbl.configure(text="")
        self._last_calc = {}

    # ── History tab ───────────────────────────────────────────────────────────
    def _load_history(self):
        for w in self._history_scroll.winfo_children():
            w.destroy()

        pid = self.app.get_patient_id()
        if not pid:
            return
        records = db.get_anthropometrics(pid)
        if not records:
            ctk.CTkLabel(
                self._history_scroll,
                text="Sin evaluaciones registradas.", text_color="gray"
            ).grid(row=0, column=0, pady=30)
            return

        has_isak2 = any(r.get("isak_level") == "ISAK 2" for r in records)
        n_sessions = len(records)
        total_cols = n_sessions + 2
        for c in range(total_cols):
            self._history_scroll.grid_columnconfigure(c, weight=1)

        def _is_suspicious(r: dict) -> bool:
            sd = r.get("session_date") or ""
            return not sd or " " in sd  # NULL or datetime-format (not user-set)

        # ── Compare row (row 0) ──────────────────────────────────────────────
        self._compare_vars = {}
        sel_frm = ctk.CTkFrame(self._history_scroll, fg_color="transparent")
        sel_frm.grid(row=0, column=0, columnspan=total_cols,
                     padx=6, pady=(4, 2), sticky="w")
        ctk.CTkLabel(
            sel_frm, text="Seleccionar para comparar:",
            font=ctk.CTkFont(size=10), text_color="gray"
        ).pack(side="left", padx=(0, 8))
        for rec in records:
            var = ctk.BooleanVar()
            self._compare_vars[rec["id"]] = var
            ctk.CTkCheckBox(
                sel_frm, text=_rec_date(rec), variable=var,
                font=ctk.CTkFont(size=10), width=20,
                command=self._update_compare_btn
            ).pack(side="left", padx=4)
        self._compare_btn = ctk.CTkButton(
            sel_frm, text="Comparar sesiones", height=28, width=160,
            state="disabled",
            fg_color="#0d6efd", hover_color="#0a58ca",
            command=self._open_comparison
        )
        self._compare_btn.pack(side="left", padx=8)

        # Header (row 1)
        headers = ["Variable"]
        for r in records:
            lvl = r.get("isak_level") or "ISAK 1"
            prefix = "⚠️ " if _is_suspicious(r) else ""
            headers.append(f"{prefix}{_rec_date(r)}\n[{lvl}]")
        headers.append("Cambios")
        for c, h in enumerate(headers):
            ctk.CTkLabel(
                self._history_scroll, text=h,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="gray", justify="center"
            ).grid(row=1, column=c, padx=6, pady=(4, 8), sticky="w")

        # Sections
        sections = [
            ("── DATOS BÁSICOS ──", []),
            (None, [
                ("Peso (kg)",               "weight_kg"),
                ("Talla (cm)",              "height_cm"),
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
            ("── RESULTADOS ──", []),
            (None, [
                ("% Masa grasa* (D&W)", "fat_mass_pct"),
                ("Masa grasa (kg)",     "fat_mass_kg"),
                ("Masa magra (kg)",     "lean_mass_kg"),
            ]),
        ]
        if has_isak2:
            sections += [
                ("── ISAK 2 — PLIEGUES ADICIONALES (mm) ──", []),
                (None, [
                    ("Pectoral",        "pectoral_mm"),
                    ("Axilar medio",    "axillary_mm"),
                    ("Muslo anterior",  "front_thigh_mm"),
                ]),
                ("── ISAK 2 — PERÍMETROS ADICIONALES (cm) ──", []),
                (None, [
                    ("Cabeza",             "head_cm"),
                    ("Cuello",             "neck_cm"),
                    ("Tórax mesoesternal", "chest_cm"),
                    ("Tobillo mínimo",     "ankle_min_cm"),
                ]),
                ("── ISAK 2 — DIÁMETROS ÓSEOS (cm) ──", []),
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
                ("── ISAK 2 — LONGITUDES (cm) ──", []),
                (None, [
                    ("Acromio-radial",       "acromion_radial_cm"),
                    ("Radio-estiloide",      "radial_styloid_cm"),
                    ("Iliospinal (pierna)",  "iliospinal_height_cm"),
                    ("Trocánter-tibial",     "trochanter_tibial_cm"),
                ]),
                ("── ISAK 2 — SOMATOTIPO ──", []),
                (None, [
                    ("Endomorfia",         "somatotype_endo"),
                    ("Mesomorfia",         "somatotype_meso"),
                    ("Ectomorfia",         "somatotype_ecto"),
                    ("Índ. Cintura/Talla", "waist_height_ratio"),
                    ("AMB (cm²)",          "arm_muscle_area"),
                ]),
            ]

        row_idx = 2
        # Compute BMI for history (for classification display)
        bmi_by_id = {}
        for r in records:
            ww, hh = r.get("weight_kg"), r.get("height_cm")
            bmi_by_id[r["id"]] = calc.bmi(ww, hh) if ww and hh else None

        for section_title, rows in sections:
            if section_title:
                frm = ctk.CTkFrame(self._history_scroll,
                                   fg_color=("#e0ede8", "#1a3a28"), corner_radius=4)
                frm.grid(row=row_idx, column=0, columnspan=total_cols,
                         padx=6, pady=(10, 2), sticky="ew")
                ctk.CTkLabel(
                    frm, text=section_title,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=("#4b7c60", "#6ec896")
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
                    cell = f"{v}%" if db_key == "fat_mass_pct" and v is not None else (
                           str(v) if v is not None else "—")
                    vals.append((v, cell))

                for c, (raw, cell) in enumerate(vals, start=1):
                    ctk.CTkLabel(
                        self._history_scroll, text=cell,
                        font=ctk.CTkFont(size=11)
                    ).grid(row=row_idx, column=c, padx=6, pady=3, sticky="w")

                # Cambios
                cambio_text = "—"
                if len(vals) >= 2:
                    fv, lv = vals[0][0], vals[-1][0]
                    if fv is not None and lv is not None:
                        diff = round(lv - fv, 2)
                        cambio_text = f"{diff:+.2f}"
                ctk.CTkLabel(
                    self._history_scroll, text=cambio_text,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=("#4b7c60" if cambio_text.startswith("+") else
                                ("#c13333" if cambio_text.startswith("-") else "gray"))
                ).grid(row=row_idx, column=n_sessions + 1,
                       padx=6, pady=3, sticky="w")
                row_idx += 1

        # Footer
        ctk.CTkLabel(
            self._history_scroll,
            text="*Durnin & Womersley (1974)  |  **Heath & Carter (1990)",
            font=ctk.CTkFont(size=9), text_color="gray"
        ).grid(row=row_idx, column=0, columnspan=total_cols,
               padx=6, pady=(12, 4), sticky="w")
        row_idx += 1

        # ⚠️ notice if any session has suspicious date
        if any(_is_suspicious(r) for r in records):
            ctk.CTkLabel(
                self._history_scroll,
                text="⚠️  Fecha pendiente de verificar — usa \"Editar fecha\" para corregirla.",
                font=ctk.CTkFont(size=10), text_color="#ca8a04"
            ).grid(row=row_idx, column=0, columnspan=total_cols,
                   padx=6, pady=(4, 2), sticky="w")
            row_idx += 1

        # Edit evaluation buttons
        edit_frm = ctk.CTkFrame(self._history_scroll, fg_color="transparent")
        edit_frm.grid(row=row_idx, column=0, columnspan=total_cols,
                      padx=6, pady=(4, 2), sticky="w")
        ctk.CTkLabel(edit_frm, text="Editar evaluación:",
                     font=ctk.CTkFont(size=10), text_color="gray"
                     ).pack(side="left", padx=(0, 8))
        for rec in records:
            btn_color = "#ca8a04" if _is_suspicious(rec) else "#0d6efd"
            btn_hover  = "#92400e" if _is_suspicious(rec) else "#0a58ca"
            ctk.CTkButton(
                edit_frm,
                text=f"{'⚠️ ' if _is_suspicious(rec) else '✏️ '}{_rec_date(rec)}",
                width=120, height=26,
                fg_color=btn_color, hover_color=btn_hover,
                font=ctk.CTkFont(size=10),
                command=lambda r=rec: self._edit_evaluation(r)
            ).pack(side="left", padx=3)
        row_idx += 1

        # Delete buttons
        del_frm = ctk.CTkFrame(self._history_scroll, fg_color="transparent")
        del_frm.grid(row=row_idx, column=0, columnspan=total_cols,
                     padx=6, pady=(2, 12), sticky="w")
        ctk.CTkLabel(del_frm, text="Eliminar sesión:",
                     font=ctk.CTkFont(size=10), text_color="gray"
                     ).pack(side="left", padx=(0, 8))
        for rec in records:
            rid = rec["id"]
            ctk.CTkButton(
                del_frm, text=_rec_date(rec), width=110, height=26,
                fg_color="#dc2626", hover_color="#991b1b",
                font=ctk.CTkFont(size=10),
                command=lambda r=rid: self._delete_record(r)
            ).pack(side="left", padx=3)

    def _delete_record(self, rid: int):
        if messagebox.askyesno("Eliminar", "¿Eliminar esta evaluación?"):
            db.delete_anthropometric(rid)
            self._load_history()

    def _update_compare_btn(self):
        """Enable compare button only when exactly 2 sessions are checked."""
        if self._compare_btn is None:
            return
        checked = [rid for rid, var in self._compare_vars.items() if var.get()]
        self._compare_btn.configure(
            state="normal" if len(checked) == 2 else "disabled"
        )

    def _open_comparison(self):
        """Open CompareSessionsDialog for the 2 selected sessions."""
        checked = [rid for rid, var in self._compare_vars.items() if var.get()]
        if len(checked) != 2:
            return
        pid = self.app.get_patient_id()
        patient = db.get_patient(pid) or {} if pid else {}
        # Get the full records
        all_records = db.get_anthropometrics(pid) if pid else []
        by_id = {r["id"]: r for r in all_records}
        rec_a = by_id.get(checked[0])
        rec_b = by_id.get(checked[1])
        if rec_a and rec_b:
            CompareSessionsDialog(self, rec_a, rec_b, patient)

    def _edit_evaluation(self, rec: dict):
        """Open the full edit dialog for an existing evaluation."""
        pid = self.app.get_patient_id()
        patient = db.get_patient(pid) if pid else {}

        def on_save():
            self._load_history()
            if self._tabs.get() == "Evolución":
                self._load_evolution()

        EditEvaluationDialog(self, rec, patient or {}, on_save)

    # ── Evolution charts ──────────────────────────────────────────────────────
    def _load_evolution(self):
        """Render matplotlib evolution charts for all 7 variables."""
        for w in self._evo_scroll.winfo_children():
            w.destroy()
        # Close previous figures to free memory
        for fig in self._evo_figures:
            try:
                fig.clf()
            except Exception:
                pass
        self._evo_figures.clear()

        if not _MPL_OK:
            ctk.CTkLabel(
                self._evo_scroll,
                text="matplotlib no instalado.\nEjecuta: pip install matplotlib",
                font=ctk.CTkFont(size=13), text_color="gray"
            ).grid(row=0, column=0, pady=40, columnspan=2)
            return

        pid = self.app.get_patient_id()
        if not pid:
            return

        patient = db.get_patient(pid) or {}
        records = db.get_anthropometrics(pid)
        if len(records) < 2:
            ctk.CTkLabel(
                self._evo_scroll,
                text="Se necesitan al menos 2 sesiones registradas para mostrar evolución.",
                font=ctk.CTkFont(size=13), text_color="gray"
            ).grid(row=0, column=0, pady=40, columnspan=2)
            return

        # Build BMI series
        bmi_vals = [
            calc.bmi(r["weight_kg"], r["height_cm"])
            if r.get("weight_kg") and r.get("height_cm") else None
            for r in records
        ]
        date_labels = []
        for r in records:
            d = _rec_date(r)
            date_labels.append(
                f"{d[8:10]}/{d[5:7]}\n'{d[2:4]}" if len(d) >= 10 else d
            )

        charts = [
            ("Peso (kg)",          [r.get("weight_kg")      for r in records], "#4b7c60"),
            ("% Masa grasa",       [r.get("fat_mass_pct")   for r in records], "#0d6efd"),
            ("Masa grasa (kg)",    [r.get("fat_mass_kg")    for r in records], "#c13333"),
            ("Masa magra (kg)",    [r.get("lean_mass_kg")   for r in records], "#4b7c60"),
            ("Σ 6 pliegues (mm)",  [r.get("sum_6_skinfolds") for r in records], "#c06c52"),
            ("Cintura (cm)",       [r.get("waist_cm")        for r in records], "#ca8a04"),
            ("IMC (kg/m²)",        bmi_vals,                                    "#0891b2"),
        ]

        goal_map = {
            "Peso (kg)":       "goal_weight_kg",
            "% Masa grasa":    "goal_fat_pct",
            "Masa grasa (kg)": "goal_fat_kg",
            "Masa magra (kg)": "goal_lean_kg",
        }

        self._evo_scroll.grid_columnconfigure((0, 1), weight=1)
        dark = ctk.get_appearance_mode() == "Dark"
        bg_fig = "#1e1e1e" if dark else "#ffffff"
        bg_ax  = "#2a2a2a" if dark else "#fafafa"
        tc     = "#e5e7eb" if dark else "#374151"
        gc     = "#4b5563" if dark else "#e5e7eb"

        for i, (title, values, color) in enumerate(charts):
            r_pos, c_pos = divmod(i, 2)
            paired = [(d, v) for d, v in zip(date_labels, values) if v is not None]

            card = ctk.CTkFrame(self._evo_scroll, corner_radius=10,
                                fg_color=("#f8f8f8", "#1e1e1e"))
            card.grid(row=r_pos, column=c_pos, padx=8, pady=8, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            card.grid_rowconfigure(1, weight=1)

            ctk.CTkLabel(
                card, text=title,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=color
            ).grid(row=0, column=0, padx=12, pady=(10, 0), sticky="w")

            if len(paired) < 2:
                ctk.CTkLabel(
                    card, text="Datos insuficientes (< 2 sesiones con valores)",
                    text_color="gray", font=ctk.CTkFont(size=11)
                ).grid(row=1, column=0, pady=20)
                continue

            ds, vs = zip(*paired)
            xs = list(range(len(ds)))

            fig = Figure(figsize=(5.5, 3.0), dpi=90)
            fig.patch.set_facecolor(bg_fig)
            ax = fig.add_subplot(111)
            ax.set_facecolor(bg_ax)

            ax.plot(xs, vs, "o-", color=color, linewidth=2, markersize=7,
                    markerfacecolor="white", markeredgecolor=color, markeredgewidth=2,
                    zorder=3)

            # Value annotations above each point
            y_range = max(vs) - min(vs) if max(vs) != min(vs) else 1
            for xi, val in enumerate(vs):
                ax.annotate(
                    str(round(val, 1)),
                    xy=(xi, val),
                    textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=8, fontweight="bold",
                    color=color, zorder=4
                )

            ax.set_xticks(xs)
            ax.set_xticklabels(ds, fontsize=7.5, color=tc)
            ax.tick_params(axis="y", labelsize=7.5, colors=tc)
            ax.spines[["top", "right"]].set_visible(False)
            ax.spines["left"].set_color(gc)
            ax.spines["bottom"].set_color(gc)
            ax.grid(axis="y", color=gc, linewidth=0.5, linestyle="--", alpha=0.8)
            # Pad y so annotations don't clip
            y_pad = y_range * 0.15
            ax.set_ylim(min(vs) - y_pad, max(vs) + y_pad * 2)

            # Goal line
            goal_key = goal_map.get(title)
            if goal_key:
                goal_val = patient.get(goal_key)
                if goal_val is not None:
                    ax.axhline(goal_val, color="#dc2626", linestyle="--",
                               linewidth=1.5, alpha=0.8, zorder=2)
                    ax.text(xs[-1], goal_val, f" Meta: {goal_val}",
                            va="bottom", ha="right", fontsize=8,
                            color="#dc2626", fontweight="bold")

            fig.tight_layout(pad=0.8)

            canvas = FigureCanvasTkAgg(fig, master=card)
            canvas.get_tk_widget().grid(
                row=1, column=0, sticky="nsew", padx=6, pady=(4, 10)
            )
            canvas.draw()
            self._evo_figures.append(fig)

    def _export_evolution_pdf(self):
        pid = self.app.get_patient_id()
        if not pid:
            messagebox.showwarning("Sin paciente", "Selecciona un paciente primero.")
            return
        patient = db.get_patient(pid)
        records = db.get_anthropometrics(pid)
        if len(records) < 2:
            messagebox.showinfo("Sin datos",
                                "Se necesitan al menos 2 sesiones para exportar.")
            return

        safe = patient["name"].replace(" ", "_")
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Evolucion_{safe}.pdf",
            title="Guardar reporte de evolución..."
        )
        if not path:
            return
        try:
            from utils import pdf_generator
            pdf_generator.generate_evolution_report(patient, records, path)
            messagebox.showinfo("OK", f"PDF guardado correctamente.")
            import os
            try:
                os.startfile(path)
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Error al generar PDF", str(e))
