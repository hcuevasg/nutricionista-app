import customtkinter as ctk
from tkinter import messagebox
from datetime import date
import database.db_manager as db


SEX_OPTIONS = ["Masculino", "Femenino"]


def _calc_age(birth_date_str: str) -> int | None:
    """Return age in years from a YYYY-MM-DD string, or None if invalid."""
    try:
        bd = date.fromisoformat(birth_date_str.strip())
        today = date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except ValueError:
        return None


class PatientFormFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app
        self._patient_id: int | None = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        header.grid_columnconfigure(1, weight=1)

        self._title_lbl = ctk.CTkLabel(
            header, text="Nuevo Paciente",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self._title_lbl.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header, text="← Volver a lista", width=150, height=32,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=lambda: self.app._show_frame("patients")
        ).grid(row=0, column=2)

        # Scrollable form
        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        scroll.grid_columnconfigure((1, 3), weight=1)
        self._form = scroll

        self._vars: dict[str, ctk.StringVar] = {}

        # Fields that are simple editable entries
        simple_fields = [
            # (label, key, row, col, colspan)
            ("Nombre completo *", "name",       0, 0, 3),
            ("Teléfono",          "phone",       2, 0, 1),
            ("Correo electrónico","email",       2, 2, 1),
            ("Dirección",         "address",     3, 0, 3),
            ("Ocupación",         "occupation",  4, 0, 1),
        ]

        for label, key, row, col, colspan in simple_fields:
            ctk.CTkLabel(
                scroll, text=label,
                font=ctk.CTkFont(size=12), text_color="gray",
                anchor="w"
            ).grid(row=row * 2, column=col * 2,
                   columnspan=colspan * 2, padx=(8, 4), pady=(12, 0), sticky="w")

            var = ctk.StringVar()
            self._vars[key] = var
            ctk.CTkEntry(scroll, textvariable=var, height=36).grid(
                row=row * 2 + 1, column=col * 2,
                columnspan=colspan * 2, padx=(8, 4), pady=(0, 2), sticky="ew")

        # Fecha de nacimiento — triggers auto age calculation
        ctk.CTkLabel(
            scroll, text="Fecha de nacimiento (YYYY-MM-DD)",
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w"
        ).grid(row=2, column=0, columnspan=2, padx=(8, 4), pady=(12, 0), sticky="w")

        self._vars["birth_date"] = ctk.StringVar()
        self._vars["birth_date"].trace_add("write", self._on_birth_date_change)
        ctk.CTkEntry(scroll, textvariable=self._vars["birth_date"], height=36).grid(
            row=3, column=0, columnspan=2, padx=(8, 4), pady=(0, 2), sticky="ew")

        # Edad — readonly, auto-calculated
        ctk.CTkLabel(
            scroll, text="Edad (años)",
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w"
        ).grid(row=2, column=4, padx=(8, 4), pady=(12, 0), sticky="w")

        self._vars["age"] = ctk.StringVar()
        self._age_entry = ctk.CTkEntry(
            scroll, textvariable=self._vars["age"], height=36,
            state="disabled", fg_color=("#f0f9f4", "#1a2e22")
        )
        self._age_entry.grid(row=3, column=4, padx=(8, 4), pady=(0, 2), sticky="ew")

        # Sex selector
        ctk.CTkLabel(
            scroll, text="Sexo", font=ctk.CTkFont(size=12),
            text_color="gray", anchor="w"
        ).grid(row=9, column=4, padx=(8, 4), pady=(12, 0), sticky="w")

        self._sex_var = ctk.StringVar(value=SEX_OPTIONS[0])
        sex_menu = ctk.CTkOptionMenu(
            scroll, values=SEX_OPTIONS,
            variable=self._sex_var, height=36
        )
        sex_menu.grid(row=10, column=4, padx=(8, 4), pady=(0, 2), sticky="ew")

        # Height / Weight (read-only mirror from last anthro)
        ctk.CTkLabel(
            scroll, text="Talla (cm)", font=ctk.CTkFont(size=12),
            text_color="gray", anchor="w"
        ).grid(row=11, column=0, padx=(8, 4), pady=(12, 0), sticky="w")
        self._vars["height_cm"] = ctk.StringVar()
        ctk.CTkEntry(
            scroll, textvariable=self._vars["height_cm"], height=36
        ).grid(row=12, column=0, padx=(8, 4), pady=(0, 2), sticky="ew")

        ctk.CTkLabel(
            scroll, text="Peso (kg)", font=ctk.CTkFont(size=12),
            text_color="gray", anchor="w"
        ).grid(row=11, column=2, padx=(8, 4), pady=(12, 0), sticky="w")
        self._vars["weight_kg"] = ctk.StringVar()
        ctk.CTkEntry(
            scroll, textvariable=self._vars["weight_kg"], height=36
        ).grid(row=12, column=2, padx=(8, 4), pady=(0, 2), sticky="ew")

        # Notes
        ctk.CTkLabel(
            scroll, text="Notas / Antecedentes",
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w"
        ).grid(row=13, column=0, columnspan=6, padx=(8, 4), pady=(14, 0), sticky="w")

        self._notes_box = ctk.CTkTextbox(scroll, height=110)
        self._notes_box.grid(row=14, column=0, columnspan=6,
                              padx=(8, 4), pady=(0, 16), sticky="ew")

        # Save button
        self._save_btn = ctk.CTkButton(
            scroll, text="Guardar Paciente", height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save
        )
        self._save_btn.grid(row=15, column=0, columnspan=3,
                            padx=(8, 4), pady=(8, 4), sticky="ew")

        ctk.CTkButton(
            scroll, text="Cancelar", height=42,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=lambda: self.app._show_frame("patients")
        ).grid(row=15, column=3, columnspan=3,
               padx=(4, 8), pady=(8, 4), sticky="ew")

    # ── Age auto-calculation ──────────────────────────────────────────────────
    def _on_birth_date_change(self, *_):
        bd = self._vars["birth_date"].get()
        age = _calc_age(bd)
        self._vars["age"].set(str(age) if age is not None else "")

    # ── Load / Save ───────────────────────────────────────────────────────────
    def load_patient(self, patient_id: int | None):
        self._patient_id = patient_id
        self._clear()

        if patient_id is None:
            self._title_lbl.configure(text="Nuevo Paciente")
            return

        self._title_lbl.configure(text="Editar Paciente")
        p = db.get_patient(patient_id)
        if not p:
            return

        mapping = {
            "name": "name", "birth_date": "birth_date", "age": "age",
            "phone": "phone", "email": "email", "address": "address",
            "occupation": "occupation", "height_cm": "height_cm",
            "weight_kg": "weight_kg"
        }
        for var_key, db_key in mapping.items():
            val = p.get(db_key)
            self._vars[var_key].set(str(val) if val is not None else "")

        if p.get("sex") in SEX_OPTIONS:
            self._sex_var.set(p["sex"])

        notes = p.get("notes") or ""
        self._notes_box.delete("1.0", "end")
        self._notes_box.insert("1.0", notes)

    def _clear(self):
        for v in self._vars.values():
            v.set("")
        self._sex_var.set(SEX_OPTIONS[0])
        self._notes_box.delete("1.0", "end")

    def _save(self):
        name = self._vars["name"].get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre es obligatorio.")
            return

        def _float(key):
            try:
                return float(self._vars[key].get().strip())
            except ValueError:
                return None

        def _int(key):
            try:
                return int(self._vars[key].get().strip())
            except ValueError:
                return None

        data = {
            "name":        name,
            "birth_date":  self._vars["birth_date"].get().strip() or None,
            "age":         _calc_age(self._vars["birth_date"].get()) or _int("age"),
            "sex":         self._sex_var.get(),
            "height_cm":   _float("height_cm"),
            "weight_kg":   _float("weight_kg"),
            "phone":       self._vars["phone"].get().strip() or None,
            "email":       self._vars["email"].get().strip() or None,
            "address":     self._vars["address"].get().strip() or None,
            "occupation":  self._vars["occupation"].get().strip() or None,
            "notes":       self._notes_box.get("1.0", "end").strip() or None,
        }

        if self._patient_id is None:
            pid = db.insert_patient(data)
            self.app.set_patient(pid)
            messagebox.showinfo("Guardado", f"Paciente '{name}' creado correctamente.")
        else:
            db.update_patient(self._patient_id, data)
            messagebox.showinfo("Guardado", f"Paciente '{name}' actualizado.")

        self.app._show_frame("patients")
