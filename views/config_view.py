"""
Pantalla de Configuración — NutriApp.
API key de Anthropic + gestión de plantillas de menú de referencia.
"""
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from typing import Optional
import database.db_manager as db

_NAVY       = "#1B3A6B"
_NAVY_LIGHT = "#2E5BA8"
_ORANGE     = "#E87722"
_GREEN      = "#16A34A"
_RED        = "#DC2626"
_GRAY       = "#6B7280"
_BG         = "#F8FAFC"
_NAVY_PALE  = "#EEF2FA"


def _lbl(parent, text, size=11, bold=False, color=None, **kw):
    font = ctk.CTkFont(size=size, weight="bold" if bold else "normal")
    kw.setdefault("text_color", color or _NAVY)
    return ctk.CTkLabel(parent, text=text, font=font, **kw)


class ConfigView(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, corner_radius=0, fg_color=_BG, **kw)
        self._app = app
        self._show_key = False
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_body()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=_NAVY, corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        _lbl(hdr, "⚙  Configuración", size=15, bold=True,
             color="white").grid(row=0, column=0, padx=20, pady=14, sticky="w")

    def _build_body(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=_BG)
        scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        # ── Card API Key ──────────────────────────────────────────────────
        card = ctk.CTkFrame(scroll, fg_color="white", corner_radius=10,
                            border_width=1, border_color="#E2E8F0")
        card.grid(row=0, column=0, padx=24, pady=(20, 10), sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        _lbl(card, "API Key de Anthropic (Claude)",
             size=13, bold=True, color=_NAVY).grid(
            row=0, column=0, padx=16, pady=(14, 4), sticky="w")
        _lbl(card,
             "Necesaria para la generacion automatica de ideas de menu con IA.\n"
             "Obtén tu key en: console.anthropic.com",
             size=10, color=_GRAY).grid(
            row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        key_row = ctk.CTkFrame(card, fg_color="transparent")
        key_row.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")
        key_row.grid_columnconfigure(0, weight=1)

        self._var_api_key = tk.StringVar()
        self._entry_key = ctk.CTkEntry(
            key_row, textvariable=self._var_api_key,
            show="•", font=ctk.CTkFont(size=11), height=36
        )
        self._entry_key.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            key_row, text="👁", width=36, height=36,
            fg_color=_NAVY_PALE, hover_color=_NAVY_PALE,
            text_color=_NAVY,
            command=self._toggle_show_key
        ).grid(row=0, column=1, padx=(0, 6))

        ctk.CTkButton(
            key_row, text="Guardar", width=90, height=36,
            fg_color=_NAVY, hover_color=_NAVY_LIGHT,
            font=ctk.CTkFont(size=11),
            command=self._guardar_key
        ).grid(row=0, column=2)

        self._lbl_key_status = _lbl(card, "", size=10, color=_GRAY)
        self._lbl_key_status.grid(row=3, column=0, padx=16, pady=(0, 14), sticky="w")

        ctk.CTkButton(
            card, text="Probar conexion",
            height=32, corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color=_NAVY_PALE, hover_color=_NAVY_PALE,
            text_color=_NAVY,
            command=self._probar_conexion
        ).grid(row=4, column=0, padx=16, pady=(0, 14), sticky="w")

        # ── Card Plantillas de referencia ─────────────────────────────────
        card2 = ctk.CTkFrame(scroll, fg_color="white", corner_radius=10,
                             border_width=1, border_color="#E2E8F0")
        card2.grid(row=1, column=0, padx=24, pady=(10, 20), sticky="ew")
        card2.grid_columnconfigure(0, weight=1)

        _lbl(card2, "Plantillas de Menú de Referencia",
             size=13, bold=True, color=_NAVY).grid(
            row=0, column=0, padx=16, pady=(14, 4), sticky="w")
        _lbl(card2,
             "Plantillas de menus de la nutricionista usadas como ejemplos para la IA.\n"
             "Importacion desde Excel disponible en proxima version.",
             size=10, color=_GRAY).grid(
            row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        self._scroll_plantillas = ctk.CTkScrollableFrame(
            card2, fg_color="transparent", height=160)
        self._scroll_plantillas.grid(row=2, column=0, padx=12,
                                      pady=(0, 12), sticky="ew")
        self._scroll_plantillas.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            card2, text="Importar Excel (próximamente)",
            height=32, corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color="#9CA3AF", hover_color="#9CA3AF",
            state="disabled"
        ).grid(row=3, column=0, padx=16, pady=(0, 14), sticky="w")

    def _toggle_show_key(self):
        self._show_key = not self._show_key
        self._entry_key.configure(show="" if self._show_key else "•")

    def _guardar_key(self):
        from utils.config_manager import guardar_api_key
        key = self._var_api_key.get().strip()
        if not key:
            messagebox.showwarning("Aviso", "Ingresa una API key válida.")
            return
        guardar_api_key(key)
        self._lbl_key_status.configure(
            text="✓ API key guardada correctamente", text_color=_GREEN)
        self._app.show_toast("API key guardada", color=_GREEN)

    def _probar_conexion(self):
        from utils.config_manager import cargar_api_key
        key = cargar_api_key()
        if not key:
            self._lbl_key_status.configure(
                text="✗ No hay API key configurada", text_color=_RED)
            return
        self._lbl_key_status.configure(
            text="Probando conexion...", text_color=_GRAY)
        self.update()
        try:
            import anthropic
            cliente = anthropic.Anthropic(api_key=key)
            cliente.models.list()
            self._lbl_key_status.configure(
                text="✓ Conexion exitosa con Anthropic", text_color=_GREEN)
        except Exception as e:
            self._lbl_key_status.configure(
                text=f"✗ Error: {str(e)[:60]}", text_color=_RED)

    def _refresh_plantillas(self):
        for w in self._scroll_plantillas.winfo_children():
            w.destroy()
        plantillas = db.get_plantillas_ref()
        if not plantillas:
            _lbl(self._scroll_plantillas,
                 "Sin plantillas importadas.",
                 size=10, color=_GRAY).pack(pady=10)
            return
        for p in plantillas:
            row = ctk.CTkFrame(self._scroll_plantillas, fg_color=_NAVY_PALE,
                               corner_radius=6)
            row.pack(fill="x", padx=4, pady=2)
            row.grid_columnconfigure(0, weight=1)
            _lbl(row,
                 f"• {p.get('descripcion', p['tipo_pauta'])} "
                 f"({p.get('kcal_objetivo', '?')} kcal)",
                 size=10, color=_NAVY).grid(
                row=0, column=0, padx=8, pady=4, sticky="w")
            ctk.CTkButton(
                row, text="🗑", width=26, height=24,
                fg_color="#FEE2E2", hover_color="#FCA5A5",
                text_color=_RED, corner_radius=4,
                command=lambda pid=p["id"]: self._eliminar_plantilla(pid)
            ).grid(row=0, column=1, padx=4, pady=2)

    def _eliminar_plantilla(self, plantilla_id: int):
        if messagebox.askyesno("Eliminar", "¿Eliminar esta plantilla de referencia?"):
            db.delete_plantilla_ref(plantilla_id)
            self._refresh_plantillas()
            self._app.show_toast("Plantilla eliminada", color=_NAVY)

    def on_show(self):
        from utils.config_manager import cargar_api_key
        key = cargar_api_key()
        if key:
            # Mostrar solo los últimos 4 caracteres
            self._var_api_key.set(key)
            self._lbl_key_status.configure(
                text=f"✓ API key configurada (termina en ...{key[-4:]})",
                text_color=_GREEN)
        self._refresh_plantillas()
