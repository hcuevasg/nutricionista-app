import customtkinter as ctk
from tkinter import messagebox
import database.db_manager as db
from utils.image_helpers import get_initials, make_circle_image


class PatientListFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Top bar ──────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top, text="Pacientes",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(
            top, placeholder_text="Buscar por nombre, teléfono o correo...",
            textvariable=self._search_var, width=320, height=36
        ).grid(row=0, column=1, padx=16, sticky="w")
        self._search_var.trace_add("write", lambda *_: self._filter())

        ctk.CTkButton(
            top, text="+ Nuevo Paciente", height=44, width=170,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.app.open_patient_form(None)
        ).grid(row=0, column=2)

        # Header separator
        ctk.CTkFrame(self, height=1, fg_color=("gray85", "gray30")
                     ).grid(row=1, column=0, sticky="ew", padx=24, pady=(12, 0))

        # ── List ─────────────────────────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(self, label_text="")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(8, 20))
        self._scroll.grid_columnconfigure(0, weight=1)

    # ── Data ─────────────────────────────────────────────────────────────────
    def on_show(self):
        self._load()

    def _load(self, query: str = ""):
        patients = db.search_patients(query) if query else db.get_all_patients()
        self._render(patients)

    def _filter(self):
        self._load(self._search_var.get().strip())

    def _render(self, patients: list):
        for w in self._scroll.winfo_children():
            w.destroy()

        if not patients:
            search_text = self._search_var.get().strip()
            if search_text:
                icon, msg = "🔍", "No se encontraron pacientes\ncon ese criterio de búsqueda."
            else:
                icon, msg = "👤", "No hay pacientes registrados.\nHaz clic en '+ Nuevo Paciente' para agregar uno."
            empty_card = ctk.CTkFrame(self._scroll, fg_color=("gray95", "gray17"),
                                      corner_radius=12)
            empty_card.pack(fill="x", padx=8, pady=40)
            ctk.CTkLabel(
                empty_card, text=icon,
                font=ctk.CTkFont(size=36)
            ).pack(pady=(28, 4))
            ctk.CTkLabel(
                empty_card, text=msg,
                font=ctk.CTkFont(size=14), text_color="gray", justify="center"
            ).pack(pady=(0, 28))
            return

        active_pid = self.app.get_patient_id()

        for p in patients:
            pid = p["id"]
            is_active = (pid == active_pid)
            self._build_patient_row(p, is_active)

    def _build_patient_row(self, p: dict, is_active: bool):
        pid = p["id"]

        # Row card — highlighted if active
        card = ctk.CTkFrame(
            self._scroll,
            corner_radius=10,
            fg_color=("#e8f2ed", "#2f5a40") if is_active else ("white", "#1a2620"),
            border_width=2 if is_active else 1,
            border_color="#4b7c60" if is_active else ("#E5EAE7", "#1a2e22")
        )
        card.pack(fill="x", padx=4, pady=4)
        card.grid_columnconfigure(2, weight=1)

        # Active badge
        if is_active:
            badge = ctk.CTkFrame(card, width=6, corner_radius=3,
                                  fg_color="#4b7c60")
            badge.grid(row=0, column=0, rowspan=2, padx=(10, 0),
                       pady=12, sticky="ns")
        else:
            ctk.CTkFrame(card, width=6, fg_color="transparent"
                         ).grid(row=0, column=0, rowspan=2, padx=(10, 0), pady=12)

        # Photo avatar
        initials = get_initials(p.get("name", "?"))
        avatar_img = make_circle_image(p.get("photo_path"), 44, initials)
        avatar_lbl = ctk.CTkLabel(card, text="", width=44, height=44)
        if avatar_img:
            avatar_lbl.configure(image=avatar_img)
        else:
            avatar_lbl.configure(
                text=initials[:2],
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#4b7c60" if not is_active else "#3d6b50",
                corner_radius=22,
                text_color="white",
            )
        avatar_lbl.grid(row=0, column=1, rowspan=2, padx=(8, 0), pady=8)
        # Keep reference to prevent GC
        avatar_lbl._avatar_img = avatar_img

        # Name + active label
        name_frame = ctk.CTkFrame(card, fg_color="transparent")
        name_frame.grid(row=0, column=2, padx=12, pady=(12, 2), sticky="w")

        ctk.CTkLabel(
            name_frame,
            text=p["name"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#3d6b50" if is_active else ("gray10", "gray90"))
        ).pack(side="left")

        if is_active:
            ctk.CTkLabel(
                name_frame,
                text="  ACTIVO",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#4b7c60"
            ).pack(side="left", padx=(6, 0))

        # Age / sex / contact
        age_str = f"{p.get('age')} años" if p.get("age") else "—"
        sex_str = p.get("sex") or "—"
        contact = p.get("phone") or p.get("email") or "—"

        ctk.CTkLabel(
            card,
            text=f"{age_str}  ·  {sex_str}  ·  {contact}",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=1, column=2, padx=12, pady=(0, 12), sticky="w")

        # Action buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=0, column=3, rowspan=2, padx=12, pady=8)

        # Seleccionar button — only shown when NOT active
        if not is_active:
            ctk.CTkButton(
                btn_frame,
                text="Seleccionar",
                width=120, height=36,
                corner_radius=8,
                fg_color="#4b7c60", hover_color="#3d6b50",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda i=pid: self._select(i)
            ).pack(pady=(0, 4))
        else:
            ctk.CTkButton(
                btn_frame,
                text="✓ Seleccionado",
                width=120, height=36,
                corner_radius=8,
                fg_color="#e0ede8", hover_color="#b8d8cc",
                text_color="#3d6b50",
                font=ctk.CTkFont(size=12, weight="bold"),
                state="disabled"
            ).pack(pady=(0, 4))

        ctk.CTkButton(
            btn_frame, text="Editar",
            width=120, height=36,
            corner_radius=8,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=lambda i=pid: self._edit(i)
        ).pack(pady=(0, 4))

        ctk.CTkButton(
            btn_frame, text="Eliminar",
            width=120, height=36,
            corner_radius=8,
            fg_color="#c13333", hover_color="#a32828",
            command=lambda i=pid: self._delete(i)
        ).pack()

    # ── Actions ───────────────────────────────────────────────────────────────
    def _select(self, pid: int):
        self.app.set_patient(pid)
        self._load(self._search_var.get().strip())   # re-render to update highlight

    def _edit(self, pid: int):
        self.app.open_patient_form(pid)

    def _delete(self, pid: int):
        p = db.get_patient(pid)
        if not p:
            return
        if messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar a {p['name']} y todos sus datos?\nEsta acción no se puede deshacer.",
            icon="warning"
        ):
            db.delete_patient(pid)
            if self.app.get_patient_id() == pid:
                self.app.set_patient(None)
            self._load()
