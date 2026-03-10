"""
BackupView — pantalla de Backup y Restauración.
"""
from __future__ import annotations
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import utils.backup_manager as bm


class BackupView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self._app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="💾  Backup y Restauración",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        # Action buttons (top-right)
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            btn_frame, text="➕  Crear backup ahora",
            height=44, corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#059669", hover_color="#047857",
            command=self._create_backup
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="📤  Exportar backup",
            height=44, corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self._export_backup
        ).grid(row=0, column=1, padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="📥  Importar backup",
            height=44, corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#7c3aed", hover_color="#6d28d9",
            command=self._import_backup
        ).grid(row=0, column=2)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=("gray85", "gray30")).grid(
            row=1, column=0, sticky="ew", padx=28, pady=(12, 0)
        )

        # List area
        list_container = ctk.CTkFrame(self, fg_color="transparent")
        list_container.grid(row=2, column=0, sticky="nsew", padx=28, pady=(12, 24))
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            list_container, text="Backups disponibles",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        self._scroll = ctk.CTkScrollableFrame(list_container, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        self._empty_lbl = ctk.CTkLabel(
            self._scroll, text="No hay backups todavía.",
            font=ctk.CTkFont(size=13), text_color="gray"
        )

        self._refresh_list()

    # ── List ──────────────────────────────────────────────────────────────────

    def _refresh_list(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        backups = bm.list_backups()
        if not backups:
            self._empty_lbl = ctk.CTkLabel(
                self._scroll, text="No hay backups todavía.",
                font=ctk.CTkFont(size=13), text_color="gray"
            )
            self._empty_lbl.grid(row=0, column=0, pady=20)
            return

        for i, b in enumerate(backups):
            self._build_backup_row(i, b)

    def _build_backup_row(self, row_idx: int, b: dict):
        from datetime import datetime
        row = ctk.CTkFrame(self._scroll, corner_radius=8, fg_color=("#f9fafb", "#1e2a20"))
        row.grid(row=row_idx, column=0, sticky="ew", pady=4)
        row.grid_columnconfigure(1, weight=1)

        # Icon
        ctk.CTkLabel(row, text="💾", font=ctk.CTkFont(size=20)).grid(
            row=0, column=0, padx=(12, 8), pady=10
        )

        # Info
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w", pady=8)

        # Parse date from filename: nutriapp_backup_YYYY-MM-DD_HH-MM.db
        name = b["name"]
        try:
            ts_str = name.replace("nutriapp_backup_", "").replace(".db", "")
            dt = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M")
            date_str = dt.strftime("%d/%m/%Y  %H:%M")
        except ValueError:
            date_str = name

        ctk.CTkLabel(
            info, text=date_str,
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            info, text=f"{b['size_kb']} KB  •  {name}",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).grid(row=1, column=0, sticky="w")

        # Buttons
        btn_box = ctk.CTkFrame(row, fg_color="transparent")
        btn_box.grid(row=0, column=2, padx=12, pady=8)

        ctk.CTkButton(
            btn_box, text="Exportar",
            width=90, height=34, corner_radius=7,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=lambda p=b["path"]: self._export_specific(p)
        ).grid(row=0, column=0, padx=(0, 6))

        ctk.CTkButton(
            btn_box, text="Restaurar",
            width=90, height=34, corner_radius=7,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#dc2626", hover_color="#b91c1c",
            command=lambda p=b["path"], d=date_str: self._restore_backup(p, d)
        ).grid(row=0, column=1)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _create_backup(self):
        try:
            path = bm.create_backup()
            self._refresh_list()
            self._app.show_toast("Backup creado correctamente ✓")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el backup:\n{e}")

    def _restore_backup(self, path: str, date_str: str):
        ok = messagebox.askyesno(
            "Restaurar backup",
            f"¿Seguro que deseas restaurar el backup del {date_str}?\n\n"
            "Se perderán los datos actuales.",
            icon="warning"
        )
        if not ok:
            return
        try:
            bm.restore_backup(path)
            messagebox.showinfo(
                "Restauración completa",
                "El backup fue restaurado correctamente.\n"
                "Reinicia la app para ver los cambios."
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restaurar:\n{e}")

    def _export_specific(self, backup_path: str):
        dest = filedialog.asksaveasfilename(
            title="Guardar backup como…",
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("Todos los archivos", "*.*")],
            initialfile=os.path.basename(backup_path),
        )
        if not dest:
            return
        try:
            bm.export_backup(backup_path, dest)
            self._app.show_toast("Backup exportado correctamente ✓")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

    def _export_backup(self):
        """Exporta el backup más reciente (o pide crear uno si no hay)."""
        backups = bm.list_backups()
        if not backups:
            messagebox.showinfo("Sin backups", "No hay backups disponibles. Crea uno primero.")
            return
        self._export_specific(backups[0]["path"])

    def _import_backup(self):
        src = filedialog.askopenfilename(
            title="Seleccionar backup a importar",
            filetypes=[("SQLite DB", "*.db"), ("Todos los archivos", "*.*")],
        )
        if not src:
            return
        ok = messagebox.askyesno(
            "Importar backup",
            "¿Seguro que deseas importar y restaurar este archivo?\n\n"
            "Se perderán los datos actuales.",
            icon="warning"
        )
        if not ok:
            return
        try:
            bm.import_and_restore(src)
            self._refresh_list()
            messagebox.showinfo(
                "Importación completa",
                "El backup fue importado y restaurado correctamente.\n"
                "Reinicia la app para ver los cambios."
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar:\n{e}")

    def on_show(self):
        self._refresh_list()
