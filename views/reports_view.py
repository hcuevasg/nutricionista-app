import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import database.db_manager as db
from utils import pdf_generator


class ReportsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Reportes PDF",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self._patient_lbl = ctk.CTkLabel(
            header, text="Ningún paciente seleccionado",
            font=ctk.CTkFont(size=13), text_color="gray"
        )
        self._patient_lbl.grid(row=0, column=1, padx=16, sticky="w")

        # Cards
        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        scroll.grid_columnconfigure((0, 1, 2), weight=1)

        self._build_card(
            scroll, row=0, col=0,
            title="Reporte Completo",
            description=(
                "Genera un PDF con toda la información del paciente:\n"
                "datos personales, historial antropométrico y todos\n"
                "los planes alimenticios registrados."
            ),
            button_text="Generar reporte completo",
            command=self._full_report,
            color="#1a6b3c"
        )

        self._build_card(
            scroll, row=0, col=1,
            title="Informe ISAK Comparativo",
            description=(
                "Genera el informe ISAK 1 o ISAK 2 según las\n"
                "sesiones registradas. ISAK 2 incluye somatocarta\n"
                "de Heath & Carter y medidas completas."
            ),
            button_text="Generar informe ISAK",
            command=self._anthro_report,
            color="#0d6efd"
        )

        self._build_card(
            scroll, row=0, col=2,
            title="Plan Alimenticio",
            description=(
                "Exporta el plan alimenticio más reciente en formato\n"
                "PDF para entregar al paciente, con el detalle\n"
                "de alimentos por tiempo de comida."
            ),
            button_text="Exportar plan más reciente",
            command=self._meal_plan_report,
            color="#7c3aed"
        )

        # Status log
        ctk.CTkLabel(
            scroll, text="Historial de exportaciones",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=1, column=0, columnspan=3, padx=8, pady=(24, 4), sticky="w")

        self._log = ctk.CTkTextbox(scroll, height=160, state="disabled")
        self._log.grid(row=2, column=0, columnspan=3, padx=8, pady=(0, 12), sticky="ew")

    def _build_card(self, parent, row, col, title, description,
                    button_text, command, color):
        card = ctk.CTkFrame(parent, corner_radius=12,
                             fg_color=(f"#f8f8f8", "#1e1e1e"))
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        accent = ctk.CTkFrame(card, height=4, fg_color=color, corner_radius=2)
        accent.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 0))

        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=color
        ).grid(row=1, column=0, padx=16, pady=(14, 6), sticky="w")

        ctk.CTkLabel(
            card, text=description,
            font=ctk.CTkFont(size=11),
            text_color="gray", justify="left", anchor="w"
        ).grid(row=2, column=0, padx=16, pady=(0, 16), sticky="w")

        ctk.CTkButton(
            card, text=button_text, height=36,
            fg_color=color,
            hover_color=self._darken(color),
            command=command
        ).grid(row=3, column=0, padx=16, pady=(0, 16), sticky="ew")

    @staticmethod
    def _darken(hex_color: str) -> str:
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r, g, b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def on_show(self):
        pid = self.app.get_patient_id()
        if pid:
            p = db.get_patient(pid)
            if p:
                self._patient_lbl.configure(text=f"Paciente: {p['name']}")
                return
        self._patient_lbl.configure(text="Ningún paciente seleccionado")

    def _get_patient_or_warn(self):
        pid = self.app.get_patient_id()
        if not pid:
            messagebox.showwarning(
                "Sin paciente",
                "Selecciona un paciente primero desde la sección Pacientes."
            )
            return None, None
        p = db.get_patient(pid)
        return pid, p

    def _ask_save_path(self, default_name: str) -> str | None:
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
            title="Guardar reporte como..."
        )
        return path if path else None

    def _log_append(self, msg: str):
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.configure(state="disabled")
        self._log.see("end")

    # ── Report generators ─────────────────────────────────────────────────────
    def _full_report(self):
        pid, patient = self._get_patient_or_warn()
        if not patient:
            return

        safe_name = patient["name"].replace(" ", "_")
        path = self._ask_save_path(f"Reporte_{safe_name}.pdf")
        if not path:
            return

        anthros     = db.get_anthropometrics(pid)
        plans       = db.get_meal_plans(pid)
        items_map   = {p["id"]: db.get_meal_items(p["id"]) for p in plans}

        try:
            pdf_generator.generate_patient_report(
                patient, anthros, plans, items_map, path
            )
            self._log_append(f"[OK] Reporte completo: {path}")
            self._open_pdf(path)
        except Exception as e:
            messagebox.showerror("Error al generar PDF", str(e))
            self._log_append(f"[ERROR] {e}")

    def _anthro_report(self):
        pid, patient = self._get_patient_or_warn()
        if not patient:
            return

        records = db.get_anthropometrics(pid)
        if not records:
            messagebox.showinfo("Sin datos",
                                "No hay evaluaciones antropométricas para este paciente.")
            return

        has_isak2 = any(r.get("isak_level") == "ISAK 2" for r in records)
        level_tag = "ISAK2" if has_isak2 else "ISAK1"
        safe_name = patient["name"].replace(" ", "_")
        last_date = records[-1]["date"]
        path = self._ask_save_path(f"{level_tag}_{safe_name}_{last_date}.pdf")
        if not path:
            return

        try:
            if has_isak2:
                pdf_generator.generate_isak2_report(patient, records, path)
            else:
                pdf_generator.generate_isak_report(patient, records, path)
            self._log_append(f"[OK] Informe {level_tag}: {path}")
            self._open_pdf(path)
        except Exception as e:
            messagebox.showerror("Error al generar PDF", str(e))
            self._log_append(f"[ERROR] {e}")

    def _meal_plan_report(self):
        pid, patient = self._get_patient_or_warn()
        if not patient:
            return

        plans = db.get_meal_plans(pid)
        if not plans:
            messagebox.showinfo("Sin planes",
                                "No hay planes alimenticios para este paciente.")
            return

        latest    = plans[0]
        items     = db.get_meal_items(latest["id"])
        safe_name = patient["name"].replace(" ", "_")
        plan_name = latest["name"].replace(" ", "_")
        path = self._ask_save_path(f"Plan_{safe_name}_{plan_name}.pdf")
        if not path:
            return

        try:
            pdf_generator.generate_meal_plan_report(patient, latest, items, path)
            self._log_append(f"[OK] Plan alimenticio: {path}")
            self._open_pdf(path)
        except Exception as e:
            messagebox.showerror("Error al generar PDF", str(e))
            self._log_append(f"[ERROR] {e}")

    @staticmethod
    def _open_pdf(path: str):
        """Open the generated PDF with the default system viewer."""
        try:
            os.startfile(path)   # Windows
        except AttributeError:
            import subprocess, sys
            if sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
