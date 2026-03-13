import customtkinter as ctk
from typing import Optional
from views.dashboard_view import DashboardFrame
from views.patient_list import PatientListFrame
from views.patient_form import PatientFormFrame
from views.anthropometric_view import AnthropometricFrame
from views.reports_view import ReportsFrame
from views.backup_view import BackupView
from views.templates_view import TemplatesFrame
from views.config_view import ConfigView
from modules.pautas_alimentacion.ui_pautas import PautasFrame as PautasAlimFrame
from modules.pautas_alimentacion.ui_editor_equivalencias import EditorEquivalenciasFrame
import database.db_manager as db
from utils.image_helpers import get_initials, make_circle_image

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# ── Paleta de colores (Stitch 2026-03) ───────────────────────────────────────
_C_PRIMARY       = "#4b7c60"   # Forest green — sidebar, botones principales
_C_PRIMARY_DARK  = "#3d6b50"   # Primary dark — hover, card activo
_C_PRIMARY_DEEP  = "#2f5a40"   # Primary deep — activo nav
_C_TERRACOTTA    = "#c06c52"   # Terracotta — accent
_C_SAGE          = "#8da399"   # Sage — separadores, detalles
_C_ACCENT        = "#8da399"   # Sage — separadores, detalles claros
_C_TEXT_MUTED    = "#d1fae5"   # Verde muy claro — texto secundario en sidebar
_C_NAV_INACTIVE  = "#c8e6d8"   # Texto inactivo nav
_C_BG_LIGHT      = "#F7F5F2"   # Fondo content light mode
_C_BG_DARK       = "#161c19"   # Fondo content dark mode


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NutriApp — Gestión Nutricional")
        self.geometry("1280x760")
        self.minsize(1100, 680)

        self._selected_patient_id: Optional[int] = None
        self._pending_plan_id: Optional[int] = None
        self._build_ui()
        self._show_frame("dashboard")

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, width=240, corner_radius=0,
                               fg_color=_C_PRIMARY)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(12, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        # Logo
        ctk.CTkLabel(
            sidebar, text="NutriApp",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        ).grid(row=0, column=0, padx=20, pady=(28, 2))

        ctk.CTkLabel(
            sidebar, text="Gestión Nutricional",
            font=ctk.CTkFont(size=11), text_color=_C_TEXT_MUTED
        ).grid(row=1, column=0, padx=20, pady=(0, 20))

        # Nav buttons
        nav_items = [
            ("dashboard",       "Inicio",              "⊞"),
            ("patients",        "Pacientes",           "👤"),
            ("anthropometrics", "Antropometría",       "📏"),
            ("pautas_alim",     "Pautas Alimentación", "🍽️"),
            ("eq_editor",       "Tablas Equiv.",       "≡"),
            ("templates",       "Plantillas",          "📋"),
            ("reports",         "Reportes",            "📄"),
            ("backup",          "Backup",              "💾"),
            ("config",          "Configuración",       "⚙"),
        ]
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        for i, (key, label, icon) in enumerate(nav_items):
            btn = ctk.CTkButton(
                sidebar,
                text=f"  {icon}  {label}",
                anchor="w", height=44, corner_radius=8,
                font=ctk.CTkFont(size=13),
                fg_color="transparent", hover_color=_C_PRIMARY_DARK,
                text_color=_C_NAV_INACTIVE,
                command=lambda k=key: self._show_frame(k)
            )
            btn.grid(row=i + 2, column=0, padx=12, pady=3, sticky="ew")
            self._nav_buttons[key] = btn

        # ── Active patient card ───────────────────────────────────────────────
        sep = ctk.CTkFrame(sidebar, height=1, fg_color=_C_SAGE)
        sep.grid(row=11, column=0, sticky="ew", padx=16, pady=(12, 0))

        self._patient_card = ctk.CTkFrame(
            sidebar, corner_radius=10,
            fg_color=_C_PRIMARY_DARK
        )
        self._patient_card.grid(row=12, column=0, padx=12, pady=12, sticky="sew")
        self._patient_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._patient_card,
            text="Paciente activo",
            font=ctk.CTkFont(size=10), text_color=_C_TEXT_MUTED
        ).grid(row=0, column=0, padx=12, pady=(10, 2), sticky="w")

        self._card_photo_lbl = ctk.CTkLabel(
            self._patient_card, text="", width=64, height=64
        )
        self._card_photo_lbl.grid(row=1, column=0, padx=12, pady=(4, 2))

        self._card_name = ctk.CTkLabel(
            self._patient_card,
            text="Ninguno seleccionado",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white", wraplength=196, justify="left"
        )
        self._card_name.grid(row=2, column=0, padx=12, pady=(0, 2), sticky="w")

        self._card_info = ctk.CTkLabel(
            self._patient_card,
            text="",
            font=ctk.CTkFont(size=11), text_color=_C_TEXT_MUTED
        )
        self._card_info.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="w")

        ctk.CTkButton(
            self._patient_card,
            text="Cambiar paciente",
            height=32, corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color=_C_PRIMARY, hover_color=_C_PRIMARY_DEEP,
            text_color="white",
            command=lambda: self._show_frame("patients")
        ).grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Theme toggle
        ctk.CTkButton(
            sidebar, text="☀  Cambiar tema",
            height=34, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color=_C_PRIMARY_DEEP, hover_color="#25472f",
            text_color=_C_TEXT_MUTED,
            command=self._toggle_theme
        ).grid(row=13, column=0, padx=12, pady=(0, 16), sticky="ew")

        # ── Content area ──────────────────────────────────────────────────────
        self._content = ctk.CTkFrame(
            self, corner_radius=0,
            fg_color=(_C_BG_LIGHT, _C_BG_DARK)
        )
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        # Frames
        self._frames: dict[str, ctk.CTkFrame] = {}
        for key, cls in [
            ("dashboard",       DashboardFrame),
            ("patients",        PatientListFrame),
            ("patient_form",    PatientFormFrame),
            ("anthropometrics", AnthropometricFrame),
            ("pautas_alim",     PautasAlimFrame),
            ("eq_editor",       EditorEquivalenciasFrame),
            ("templates",       TemplatesFrame),
            ("reports",         ReportsFrame),
            ("backup",          BackupView),
            ("config",          ConfigView),
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
            if k == key:
                btn.configure(
                    fg_color=_C_PRIMARY_DEEP,
                    text_color="white",
                    font=ctk.CTkFont(size=13, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=_C_NAV_INACTIVE,
                    font=ctk.CTkFont(size=13),
                )

    # ── Patient management ────────────────────────────────────────────────────
    def set_patient(self, patient_id: Optional[int]):
        self._selected_patient_id = patient_id
        self._refresh_patient_card()

    def get_patient_id(self) -> Optional[int]:
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
        initials = get_initials(p["name"])
        img = make_circle_image(p.get("photo_path"), 64, initials)
        if img:
            self._card_photo_lbl.configure(image=img, text="")
            self._card_photo_lbl._photo_img = img
        else:
            self._card_photo_lbl.configure(image=None, text=initials,
                                            font=ctk.CTkFont(size=20, weight="bold"),
                                            text_color="white")

    def open_patient_form(self, patient_id: Optional[int] = None):
        self._frames["patient_form"].load_patient(patient_id)
        self._show_frame("patient_form")

    def _toggle_theme(self):
        mode = ctk.get_appearance_mode()
        ctk.set_appearance_mode("dark" if mode == "Light" else "light")

    # ── Toast notification ────────────────────────────────────────────────────
    def show_toast(self, message: str, duration_ms: int = 3000,
                   color: str = _C_PRIMARY):
        """Muestra un mensaje discreto en la esquina inferior derecha."""
        toast = ctk.CTkFrame(self, corner_radius=10, fg_color=color,
                             border_width=1, border_color=_C_SAGE)
        ctk.CTkLabel(
            toast, text=message,
            font=ctk.CTkFont(size=12), text_color="white"
        ).pack(padx=18, pady=11)

        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        toast.place(x=w - 360, y=h - 72)
        toast.lift()
        self.after(duration_ms, toast.destroy)
