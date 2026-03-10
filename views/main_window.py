import customtkinter as ctk
from views.patient_list import PatientListFrame
from views.patient_form import PatientFormFrame
from views.anthropometric_view import AnthropometricFrame
from views.meal_plan_view import MealPlanFrame
from views.reports_view import ReportsFrame
import database.db_manager as db
from utils.image_helpers import get_initials, make_circle_image

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NutriApp — Gestión Nutricional")
        self.geometry("1280x760")
        self.minsize(1100, 680)

        self._selected_patient_id: int | None = None
        self._build_ui()
        self._show_frame("patients")

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0,
                                fg_color="#1a6b3c")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(7, weight=1)   # spacer row
        sidebar.grid_columnconfigure(0, weight=1)

        # Logo
        ctk.CTkLabel(
            sidebar, text="NutriApp",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        ).grid(row=0, column=0, padx=20, pady=(28, 2))

        ctk.CTkLabel(
            sidebar, text="Gestión Nutricional",
            font=ctk.CTkFont(size=11), text_color="#a7f3c8"
        ).grid(row=1, column=0, padx=20, pady=(0, 20))

        # Nav buttons
        nav_items = [
            ("patients",        "Pacientes",          "👤"),
            ("anthropometrics", "Antropometría",      "📏"),
            ("meal_plans",      "Planes Alimenticios", "🥗"),
            ("reports",         "Reportes",           "📄"),
        ]
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        for i, (key, label, icon) in enumerate(nav_items):
            btn = ctk.CTkButton(
                sidebar,
                text=f"  {icon}  {label}",
                anchor="w", height=42, corner_radius=8,
                font=ctk.CTkFont(size=13),
                fg_color="transparent", hover_color="#145730",
                text_color="white",
                command=lambda k=key: self._show_frame(k)
            )
            btn.grid(row=i + 2, column=0, padx=12, pady=4, sticky="ew")
            self._nav_buttons[key] = btn

        # ── Active patient card ───────────────────────────────────────────────
        sep = ctk.CTkFrame(sidebar, height=1, fg_color="#2d8a56")
        sep.grid(row=6, column=0, sticky="ew", padx=16, pady=(12, 0))

        self._patient_card = ctk.CTkFrame(
            sidebar, corner_radius=10,
            fg_color="#145730"
        )
        self._patient_card.grid(row=7, column=0, padx=12, pady=12, sticky="sew")
        self._patient_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._patient_card,
            text="Paciente activo",
            font=ctk.CTkFont(size=10), text_color="#a7f3c8"
        ).grid(row=0, column=0, padx=12, pady=(10, 2), sticky="w")

        self._card_photo_lbl = ctk.CTkLabel(
            self._patient_card, text="", width=64, height=64
        )
        self._card_photo_lbl.grid(row=1, column=0, padx=12, pady=(4, 2))

        self._card_name = ctk.CTkLabel(
            self._patient_card,
            text="Ninguno seleccionado",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white", wraplength=180, justify="left"
        )
        self._card_name.grid(row=2, column=0, padx=12, pady=(0, 2), sticky="w")

        self._card_info = ctk.CTkLabel(
            self._patient_card,
            text="",
            font=ctk.CTkFont(size=11), text_color="#a7f3c8"
        )
        self._card_info.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="w")

        ctk.CTkButton(
            self._patient_card,
            text="Cambiar paciente",
            height=30, corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color="#1a6b3c", hover_color="#0d3d20",
            text_color="white",
            command=lambda: self._show_frame("patients")
        ).grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Theme toggle
        ctk.CTkButton(
            sidebar, text="Cambiar tema",
            height=32, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="#0d3d20", hover_color="#092b16",
            text_color="#a7f3c8",
            command=self._toggle_theme
        ).grid(row=8, column=0, padx=12, pady=(0, 16), sticky="ew")

        # ── Content area ──────────────────────────────────────────────────────
        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        # Frames
        self._frames: dict[str, ctk.CTkFrame] = {}
        for key, cls in [
            ("patients",        PatientListFrame),
            ("patient_form",    PatientFormFrame),
            ("anthropometrics", AnthropometricFrame),
            ("meal_plans",      MealPlanFrame),
            ("reports",         ReportsFrame),
        ]:
            f = cls(self._content, app=self)
            f.grid(row=0, column=0, sticky="nsew")
            self._frames[key] = f

    # ── Navigation ────────────────────────────────────────────────────────────
    def _show_frame(self, key: str):
        frame = self._frames.get(key)
        if frame:
            frame.tkraise()
            if hasattr(frame, "on_show"):
                frame.on_show()
        for k, btn in self._nav_buttons.items():
            btn.configure(fg_color="#0d3d20" if k == key else "transparent")

    # ── Patient management ────────────────────────────────────────────────────
    def set_patient(self, patient_id: int | None):
        self._selected_patient_id = patient_id
        self._refresh_patient_card()

    def get_patient_id(self) -> int | None:
        return self._selected_patient_id

    def _refresh_patient_card(self):
        pid = self._selected_patient_id
        if not pid:
            self._card_name.configure(text="Ninguno seleccionado")
            self._card_info.configure(text="")
            self._card_photo_lbl.configure(image=None, text="")
            return
        p = db.get_patient(pid)
        if not p:
            self._card_name.configure(text="Ninguno seleccionado")
            self._card_info.configure(text="")
            self._card_photo_lbl.configure(image=None, text="")
            return
        self._card_name.configure(text=p["name"])
        age = f"{p['age']} años" if p.get("age") else "—"
        sex = p.get("sex") or "—"
        self._card_info.configure(text=f"{age}  ·  {sex}")
        # Update photo
        initials = get_initials(p["name"])
        img = make_circle_image(p.get("photo_path"), 64, initials)
        if img:
            self._card_photo_lbl.configure(image=img, text="")
            self._card_photo_lbl._photo_img = img  # prevent GC
        else:
            self._card_photo_lbl.configure(image=None, text=initials,
                                            font=ctk.CTkFont(size=20, weight="bold"),
                                            text_color="white")

    def open_patient_form(self, patient_id: int | None = None):
        self._frames["patient_form"].load_patient(patient_id)
        self._show_frame("patient_form")

    def _toggle_theme(self):
        mode = ctk.get_appearance_mode()
        ctk.set_appearance_mode("dark" if mode == "Light" else "light")
