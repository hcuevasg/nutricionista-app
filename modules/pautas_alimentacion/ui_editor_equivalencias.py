"""
Editor de Tablas de Equivalencias — NutriApp.
Permite editar, agregar, eliminar y reordenar grupos y alimentos
de las tablas de equivalencias, con persistencia en SQLite.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Optional
import database.db_manager as db

_NAVY       = "#4b7c60"
_NAVY_LIGHT = "#3d6b50"
_NAVY_PALE  = "#e8f2ed"
_ORANGE     = "#c06c52"
_GREEN      = "#4b7c60"
_RED        = "#DC2626"
_GRAY       = "#6B7280"
_BG         = "#F7F5F2"

_TIPOS = [
    ("omnivoro",     "Omnívoro"),
    ("ovolacto",     "Ovo-lacto Vegetariano"),
    ("vegano",       "Vegano"),
    ("pescetariano", "Pescetariano"),
    ("sin_gluten",   "Sin Gluten"),
]
_TIPOS_KEYS   = [t[0] for t in _TIPOS]
_TIPOS_LABELS = [t[1] for t in _TIPOS]


def _lbl(parent, text, size=11, bold=False, color=None, **kw):
    font = ctk.CTkFont(size=size, weight="bold" if bold else "normal")
    kw.setdefault("text_color", color or _NAVY)
    return ctk.CTkLabel(parent, text=text, font=font, **kw)


class EditorEquivalenciasFrame(ctk.CTkFrame):
    """Frame principal del editor de tablas de equivalencias."""

    def __init__(self, master, app, **kw):
        super().__init__(master, corner_radius=0, fg_color=_BG, **kw)
        self._app = app
        self._tipo_actual = _TIPOS_KEYS[0]
        self._grupo_seleccionado: Optional[int] = None   # id del grupo activo
        self._grupo_nombre_actual: str = ""
        self._edit_mode: Optional[int] = None            # id del alimento en edición
        self._grupos_widgets: dict = {}                  # {grupo_id: frame}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()

    # ──────────────────────────────────────────────────────────────────────
    # HEADER
    # ──────────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=("white", "#1a2620"),
                           corner_radius=0,
                           border_width=1, border_color=("#E5EAE7", "#2a3d30"))
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)

        _lbl(hdr, "≡  Editor de Tablas de Equivalencias",
             size=15, bold=True, color=_NAVY).grid(
            row=0, column=0, padx=20, pady=14, sticky="w")

        # Selector tipo de pauta
        sel_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        sel_frame.grid(row=0, column=1, padx=20, sticky="e")

        _lbl(sel_frame, "Tipo de pauta:", size=11, color=_GRAY).pack(
            side="left", padx=(0, 8), pady=12)

        self._combo_tipo = ctk.CTkComboBox(
            sel_frame, values=_TIPOS_LABELS, width=220,
            font=ctk.CTkFont(size=11),
            command=self._on_tipo_changed
        )
        self._combo_tipo.pack(side="left", pady=12)
        self._combo_tipo.set(_TIPOS_LABELS[0])

    # ──────────────────────────────────────────────────────────────────────
    # BODY (dos paneles)
    # ──────────────────────────────────────────────────────────────────────
    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=_BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # ── Panel izquierdo: lista de grupos ──────────────────────────────
        left = ctk.CTkFrame(body, fg_color="white", corner_radius=10,
                            border_width=1, border_color="#E2E8F0",
                            width=280)
        left.grid(row=0, column=0, padx=(12, 6), pady=12, sticky="nsew")
        left.grid_propagate(False)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        _lbl(left, "Grupos", size=12, bold=True, color=_NAVY).grid(
            row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self._scroll_grupos = ctk.CTkScrollableFrame(
            left, fg_color="transparent")
        self._scroll_grupos.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._scroll_grupos.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            left, text="＋  Nuevo grupo",
            height=36, corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color=_ORANGE, hover_color=_ORANGE,
            command=self._nuevo_grupo
        ).grid(row=2, column=0, padx=12, pady=(4, 12), sticky="ew")

        # ── Panel derecho: alimentos del grupo ────────────────────────────
        right = ctk.CTkFrame(body, fg_color="white", corner_radius=10,
                             border_width=1, border_color="#E2E8F0")
        right.grid(row=0, column=1, padx=(6, 12), pady=12, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        # Header del panel derecho
        rhdr = ctk.CTkFrame(right, fg_color=_NAVY_PALE, corner_radius=0)
        rhdr.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        rhdr.grid_columnconfigure(0, weight=1)

        self._lbl_grupo_activo = _lbl(
            rhdr, "Selecciona un grupo",
            size=12, bold=True, color=_NAVY)
        self._lbl_grupo_activo.grid(row=0, column=0, padx=14, pady=10, sticky="w")

        self._btn_renombrar = ctk.CTkButton(
            rhdr, text="✏  Renombrar", width=110, height=28,
            font=ctk.CTkFont(size=10),
            fg_color=_NAVY_LIGHT, hover_color=_NAVY,
            command=self._renombrar_grupo
        )
        self._btn_renombrar.grid(row=0, column=1, padx=(4, 12), pady=8)
        self._btn_renombrar.configure(state="disabled")

        # Lista scrollable de alimentos
        self._scroll_alimentos = ctk.CTkScrollableFrame(
            right, fg_color="transparent")
        self._scroll_alimentos.grid(row=1, column=0, sticky="nsew",
                                    padx=8, pady=4)
        self._scroll_alimentos.grid_columnconfigure(0, weight=1)

        # Fila agregar
        add_row = ctk.CTkFrame(right, fg_color=_NAVY_PALE, corner_radius=0)
        add_row.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        add_row.grid_columnconfigure(1, weight=1)

        _lbl(add_row, "Gramaje:", size=10, color=_GRAY).grid(
            row=0, column=0, padx=(12, 4), pady=8)
        self._var_add_gram = tk.StringVar()
        self._entry_add_gram = ctk.CTkEntry(
            add_row, textvariable=self._var_add_gram,
            width=85, placeholder_text="ej: 160g",
            font=ctk.CTkFont(size=10), height=30)
        self._entry_add_gram.grid(row=0, column=1, padx=(0, 6), pady=8, sticky="w")

        _lbl(add_row, "Descripción:", size=10, color=_GRAY).grid(
            row=0, column=2, padx=(0, 4), pady=8)
        self._var_add_desc = tk.StringVar()
        self._entry_add_desc = ctk.CTkEntry(
            add_row, textvariable=self._var_add_desc,
            placeholder_text="ej: Choclo (1 T.)",
            font=ctk.CTkFont(size=10), height=30)
        self._entry_add_desc.grid(row=0, column=3, padx=(0, 6), pady=8, sticky="ew")
        add_row.grid_columnconfigure(3, weight=1)

        self._btn_agregar = ctk.CTkButton(
            add_row, text="Agregar", width=80, height=30,
            font=ctk.CTkFont(size=11),
            fg_color=_ORANGE, hover_color=_ORANGE,
            command=self._agregar_alimento
        )
        self._btn_agregar.grid(row=0, column=4, padx=(0, 12), pady=8)
        self._btn_agregar.configure(state="disabled")

    # ──────────────────────────────────────────────────────────────────────
    # EVENTOS TIPO PAUTA
    # ──────────────────────────────────────────────────────────────────────
    def _on_tipo_changed(self, label: str):
        if label in _TIPOS_LABELS:
            idx = _TIPOS_LABELS.index(label)
            self._tipo_actual = _TIPOS_KEYS[idx]
        self._grupo_seleccionado = None
        self._grupo_nombre_actual = ""
        self._lbl_grupo_activo.configure(text="Selecciona un grupo")
        self._btn_renombrar.configure(state="disabled")
        self._btn_agregar.configure(state="disabled")
        self._refresh_grupos()
        self._refresh_alimentos()

    # ──────────────────────────────────────────────────────────────────────
    # GRUPOS
    # ──────────────────────────────────────────────────────────────────────
    def _refresh_grupos(self):
        for w in self._scroll_grupos.winfo_children():
            w.destroy()
        self._grupos_widgets = {}
        grupos = db.eq_get_grupos(self._tipo_actual)
        for g in grupos:
            self._render_grupo_row(g)

    def _render_grupo_row(self, g: dict):
        gid  = g["id"]
        nombre = g["nombre_grupo"]
        is_sel = (gid == self._grupo_seleccionado)

        fg_row = _NAVY if is_sel else "white"
        fg_txt = "white" if is_sel else _NAVY

        row = ctk.CTkFrame(
            self._scroll_grupos,
            fg_color=fg_row, corner_radius=6,
            border_width=1, border_color="#E2E8F0"
        )
        row.pack(fill="x", padx=4, pady=2)
        row.grid_columnconfigure(0, weight=1)

        btn = ctk.CTkButton(
            row, text=nombre, anchor="w",
            height=32, corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=_NAVY_PALE if not is_sel else _NAVY_LIGHT,
            text_color=fg_txt,
            command=lambda gid2=gid, nom=nombre: self._seleccionar_grupo(gid2, nom)
        )
        btn.grid(row=0, column=0, sticky="ew", padx=(4, 0), pady=2)

        # Botones acción
        btns_frame = ctk.CTkFrame(row, fg_color="transparent")
        btns_frame.grid(row=0, column=1, padx=(0, 4), pady=2)

        for symbol, cmd in [
            ("↑", lambda gid2=gid: self._mover_grupo(gid2, "arriba")),
            ("↓", lambda gid2=gid: self._mover_grupo(gid2, "abajo")),
            ("🗑", lambda gid2=gid, nom=nombre: self._eliminar_grupo(gid2, nom)),
        ]:
            ctk.CTkButton(
                btns_frame, text=symbol, width=26, height=26,
                font=ctk.CTkFont(size=11),
                fg_color=_NAVY_PALE if not is_sel else _NAVY_LIGHT,
                hover_color=_NAVY,
                text_color=_NAVY if not is_sel else "white",
                corner_radius=4,
                command=cmd
            ).pack(side="left", padx=1)

        self._grupos_widgets[gid] = row

    def _seleccionar_grupo(self, grupo_id: int, nombre: str):
        self._grupo_seleccionado = grupo_id
        self._grupo_nombre_actual = nombre
        self._lbl_grupo_activo.configure(text=nombre)
        self._btn_renombrar.configure(state="normal")
        self._btn_agregar.configure(state="normal")
        self._refresh_grupos()
        self._refresh_alimentos()

    def _nuevo_grupo(self):
        dlg = _SimpleInputDialog(self, "Nuevo grupo",
                                 "Nombre del nuevo grupo:")
        self.wait_window(dlg)
        nombre = dlg.result
        if not nombre:
            return
        gid = db.eq_agregar_grupo(self._tipo_actual, nombre)
        self._seleccionar_grupo(gid, nombre)
        self._app.show_toast("Grupo agregado ✓", color=_GREEN)

    def _renombrar_grupo(self):
        if not self._grupo_seleccionado:
            return
        dlg = _SimpleInputDialog(self, "Renombrar grupo",
                                 "Nuevo nombre:",
                                 default=self._grupo_nombre_actual)
        self.wait_window(dlg)
        nuevo = dlg.result
        if not nuevo or nuevo == self._grupo_nombre_actual:
            return
        db.eq_renombrar_grupo(self._grupo_seleccionado, nuevo)
        self._grupo_nombre_actual = nuevo
        self._lbl_grupo_activo.configure(text=nuevo)
        self._refresh_grupos()
        self._app.show_toast("Grupo renombrado ✓", color=_GREEN)

    def _eliminar_grupo(self, grupo_id: int, nombre: str):
        if not messagebox.askyesno(
            "Eliminar grupo",
            f"¿Eliminar el grupo '{nombre}' y todos sus alimentos?\n"
            "Esta acción no se puede deshacer."
        ):
            return
        db.eq_eliminar_grupo(grupo_id)
        if self._grupo_seleccionado == grupo_id:
            self._grupo_seleccionado = None
            self._grupo_nombre_actual = ""
            self._lbl_grupo_activo.configure(text="Selecciona un grupo")
            self._btn_renombrar.configure(state="disabled")
            self._btn_agregar.configure(state="disabled")
        self._refresh_grupos()
        self._refresh_alimentos()
        self._app.show_toast("Grupo eliminado ✓", color=_NAVY)

    def _mover_grupo(self, grupo_id: int, direccion: str):
        db.eq_mover_grupo(grupo_id, direccion)
        self._refresh_grupos()
        self._app.show_toast("Orden actualizado ✓", color=_GREEN)

    # ──────────────────────────────────────────────────────────────────────
    # ALIMENTOS
    # ──────────────────────────────────────────────────────────────────────
    def _refresh_alimentos(self):
        for w in self._scroll_alimentos.winfo_children():
            w.destroy()
        self._edit_mode = None
        if not self._grupo_seleccionado:
            _lbl(self._scroll_alimentos,
                 "← Selecciona un grupo para ver sus alimentos",
                 size=11, color=_GRAY).pack(pady=30)
            return
        alimentos = db.eq_get_alimentos(self._grupo_seleccionado)
        if not alimentos:
            _lbl(self._scroll_alimentos,
                 "Sin alimentos. Agrega uno abajo.",
                 size=11, color=_GRAY).pack(pady=20)
            return
        for i, alim in enumerate(alimentos):
            self._render_alimento_row(alim, i, len(alimentos))

    def _render_alimento_row(self, alim: dict, idx: int, total: int):
        aid = alim["id"]
        bg = "#F7F5F2" if idx % 2 == 0 else "white"

        row = ctk.CTkFrame(self._scroll_alimentos, fg_color=bg,
                           corner_radius=4, border_width=0)
        row.pack(fill="x", padx=4, pady=1)
        row.grid_columnconfigure(1, weight=1)

        if self._edit_mode == aid:
            # Modo edición
            var_gram = tk.StringVar(value=alim["gramaje"])
            var_desc = tk.StringVar(value=alim["descripcion"])

            e_gram = ctk.CTkEntry(row, textvariable=var_gram, width=90,
                                  font=ctk.CTkFont(size=10), height=28)
            e_gram.grid(row=0, column=0, padx=(6, 4), pady=4)
            e_desc = ctk.CTkEntry(row, textvariable=var_desc,
                                  font=ctk.CTkFont(size=10), height=28)
            e_desc.grid(row=0, column=1, padx=(0, 4), pady=4, sticky="ew")

            def _confirmar(aid2=aid, vg=var_gram, vd=var_desc):
                db.eq_editar_alimento(aid2, vg.get().strip(), vd.get().strip())
                self._edit_mode = None
                self._refresh_alimentos()
                self._app.show_toast("Alimento actualizado ✓", color=_GREEN)

            def _cancelar():
                self._edit_mode = None
                self._refresh_alimentos()

            ctk.CTkButton(row, text="✓", width=28, height=28,
                          fg_color=_GREEN, hover_color=_GREEN,
                          font=ctk.CTkFont(size=12),
                          command=_confirmar).grid(row=0, column=2, padx=2, pady=4)
            ctk.CTkButton(row, text="✗", width=28, height=28,
                          fg_color=_RED, hover_color=_RED,
                          font=ctk.CTkFont(size=12),
                          command=_cancelar).grid(row=0, column=3, padx=2, pady=4)
        else:
            # Modo lectura
            ctk.CTkLabel(row, text=alim["gramaje"],
                         font=ctk.CTkFont(size=10), text_color=_NAVY,
                         fg_color="transparent", anchor="e", width=90).grid(
                row=0, column=0, padx=(6, 4), pady=4)
            ctk.CTkLabel(row, text=alim["descripcion"],
                         font=ctk.CTkFont(size=10), text_color="#2C2C2C",
                         fg_color="transparent", anchor="w").grid(
                row=0, column=1, padx=(0, 4), pady=4, sticky="ew")

            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.grid(row=0, column=2, padx=(0, 6), pady=2)

            for sym, cmd, fc in [
                ("↑", lambda aid2=aid: self._mover_alim(aid2, "arriba"), _NAVY_PALE),
                ("↓", lambda aid2=aid: self._mover_alim(aid2, "abajo"), _NAVY_PALE),
                ("✏", lambda aid2=aid: self._activar_edicion(aid2), _NAVY_PALE),
                ("🗑", lambda aid2=aid: self._eliminar_alim(aid2), "#FEE2E2"),
            ]:
                ctk.CTkButton(
                    btns, text=sym, width=26, height=26,
                    font=ctk.CTkFont(size=10),
                    fg_color=fc, hover_color=_NAVY_PALE,
                    text_color=_NAVY if fc != "#FEE2E2" else _RED,
                    corner_radius=4,
                    command=cmd
                ).pack(side="left", padx=1)

    def _activar_edicion(self, alimento_id: int):
        self._edit_mode = alimento_id
        self._refresh_alimentos()

    def _eliminar_alim(self, alimento_id: int):
        if not messagebox.askyesno("Eliminar", "¿Eliminar este alimento?"):
            return
        db.eq_eliminar_alimento(alimento_id)
        self._refresh_alimentos()
        self._app.show_toast("Alimento eliminado ✓", color=_NAVY)

    def _mover_alim(self, alimento_id: int, direccion: str):
        db.eq_mover_alimento(alimento_id, direccion)
        self._refresh_alimentos()
        self._app.show_toast("Orden actualizado ✓", color=_GREEN)

    def _agregar_alimento(self):
        if not self._grupo_seleccionado:
            return
        gram = self._var_add_gram.get().strip()
        desc = self._var_add_desc.get().strip()
        if not desc:
            messagebox.showwarning("Aviso", "La descripción no puede estar vacía.")
            return
        db.eq_agregar_alimento(self._grupo_seleccionado, gram, desc)
        self._var_add_gram.set("")
        self._var_add_desc.set("")
        self._refresh_alimentos()
        self._app.show_toast("Alimento agregado ✓", color=_GREEN)

    # ──────────────────────────────────────────────────────────────────────
    # ON SHOW (llamado por la navegación)
    # ──────────────────────────────────────────────────────────────────────
    def on_show(self):
        db.migrar_tablas_equivalencias()
        self._refresh_grupos()
        self._refresh_alimentos()


# ── Diálogo simple de texto ───────────────────────────────────────────────────

class _SimpleInputDialog(ctk.CTkToplevel):
    """Diálogo modal simple para pedir un string."""

    def __init__(self, parent, title: str, prompt: str, default: str = ""):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.result: Optional[str] = None

        ctk.CTkLabel(self, text=prompt,
                     font=ctk.CTkFont(size=12)).pack(padx=24, pady=(18, 6))
        self._var = tk.StringVar(value=default)
        entry = ctk.CTkEntry(self, textvariable=self._var,
                             width=280, font=ctk.CTkFont(size=12), height=34)
        entry.pack(padx=24, pady=(0, 12))
        entry.focus_set()
        entry.select_range(0, "end")
        entry.bind("<Return>", lambda _: self._ok())

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(padx=24, pady=(0, 18))
        ctk.CTkButton(btns, text="Cancelar", width=100,
                      fg_color="#9CA3AF", hover_color="#6B7280",
                      command=self.destroy).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="Guardar", width=100,
                      fg_color="#4b7c60", hover_color="#3d6b50",
                      command=self._ok).pack(side="left")

    def _ok(self):
        val = self._var.get().strip()
        if val:
            self.result = val
        self.destroy()
