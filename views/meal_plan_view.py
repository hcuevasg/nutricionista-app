import customtkinter as ctk
from tkinter import messagebox
from datetime import date
import database.db_manager as db
import utils.calculations as calc


MEAL_TYPES = ["Desayuno", "Media mañana", "Almuerzo",
              "Merienda", "Cena", "Colación"]
UNITS = ["g", "ml", "taza", "cdta", "cda", "unidad", "porción", "rebanada"]
GOALS = ["Pérdida de peso", "Mantenimiento", "Ganancia muscular",
         "Control glucémico", "Salud cardiovascular", "Otro"]


class MealPlanFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app
        self._selected_plan_id: int | None = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Planes Alimenticios",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self._patient_lbl = ctk.CTkLabel(
            header, text="Ningún paciente seleccionado",
            font=ctk.CTkFont(size=13), text_color="gray"
        )
        self._patient_lbl.grid(row=0, column=1, padx=16, sticky="w")

        # Main pane: left=plan list, right=plan detail
        panes = ctk.CTkFrame(self, fg_color="transparent")
        panes.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        panes.grid_columnconfigure(1, weight=1)
        panes.grid_rowconfigure(0, weight=1)

        # ── Left panel: plan list ─────────────────────────────────────────────
        left = ctk.CTkFrame(panes, width=260)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            left, text="+ Nuevo Plan", height=36,
            command=self._new_plan
        ).grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self._plan_scroll = ctk.CTkScrollableFrame(left, label_text="Planes")
        self._plan_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 8))
        self._plan_scroll.grid_columnconfigure(0, weight=1)

        # ── Right panel: plan detail/editor ──────────────────────────────────
        self._right = ctk.CTkFrame(panes)
        self._right.grid(row=0, column=1, sticky="nsew")
        self._right.grid_columnconfigure(0, weight=1)
        self._right.grid_rowconfigure(1, weight=1)

        self._detail_placeholder = ctk.CTkLabel(
            self._right,
            text="Selecciona un plan o crea uno nuevo.",
            font=ctk.CTkFont(size=14), text_color="gray"
        )
        self._detail_placeholder.grid(row=0, column=0, pady=60)

        # Plan editor (hidden until a plan is selected/created)
        self._editor = ctk.CTkFrame(self._right, fg_color="transparent")
        self._editor.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self._editor.grid_rowconfigure(5, weight=1)

        self._plan_vars: dict[str, ctk.StringVar] = {}
        self._build_plan_editor()

    def _build_plan_editor(self):
        ed = self._editor

        # Plan name
        ctk.CTkLabel(ed, text="Nombre del plan", text_color="gray",
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, padx=8, pady=(12, 0), sticky="w")
        self._plan_vars["name"] = ctk.StringVar()
        ctk.CTkEntry(ed, textvariable=self._plan_vars["name"], height=34).grid(
            row=1, column=0, columnspan=2, padx=8, pady=(0, 4), sticky="ew")

        # Date
        ctk.CTkLabel(ed, text="Fecha", text_color="gray",
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, padx=8, pady=(12, 0), sticky="w")
        self._plan_vars["date"] = ctk.StringVar(value=date.today().isoformat())
        ctk.CTkEntry(ed, textvariable=self._plan_vars["date"], height=34).grid(
            row=1, column=2, padx=8, pady=(0, 4), sticky="ew")

        # Goal
        ctk.CTkLabel(ed, text="Objetivo", text_color="gray",
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=3, padx=8, pady=(12, 0), sticky="w")
        self._goal_var = ctk.StringVar(value=GOALS[0])
        ctk.CTkOptionMenu(ed, values=GOALS, variable=self._goal_var,
                          height=34).grid(
            row=1, column=3, padx=8, pady=(0, 4), sticky="ew")

        # Macros
        macro_labels = [
            ("Calorías (kcal)", "calories", 2, 0),
            ("Proteínas (g)",   "protein_g", 2, 1),
            ("Carbohidratos (g)", "carbs_g", 2, 2),
            ("Grasas (g)",      "fat_g",    2, 3),
        ]
        for label, key, row, col in macro_labels:
            ctk.CTkLabel(ed, text=label, text_color="gray",
                         font=ctk.CTkFont(size=12)).grid(
                row=row, column=col, padx=8, pady=(10, 0), sticky="w")
            self._plan_vars[key] = ctk.StringVar()
            ctk.CTkEntry(ed, textvariable=self._plan_vars[key], height=34).grid(
                row=row + 1, column=col, padx=8, pady=(0, 4), sticky="ew")

        # Auto-fill macros button
        ctk.CTkButton(
            ed, text="Auto-calcular macros", height=32,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self._auto_macros
        ).grid(row=4, column=0, columnspan=2, padx=8, pady=4, sticky="ew")

        # Save plan header button
        ctk.CTkButton(
            ed, text="Guardar cabecera", height=32,
            command=self._save_plan_header
        ).grid(row=4, column=2, columnspan=2, padx=8, pady=4, sticky="ew")

        # Notes
        ctk.CTkLabel(ed, text="Notas del plan", text_color="gray",
                     font=ctk.CTkFont(size=12)).grid(
            row=5, column=0, columnspan=4, padx=8, pady=(8, 0), sticky="w")
        self._plan_notes = ctk.CTkTextbox(ed, height=55)
        self._plan_notes.grid(row=6, column=0, columnspan=4,
                               padx=8, pady=(0, 8), sticky="ew")

        # ── Meal items section ────────────────────────────────────────────────
        ctk.CTkLabel(
            ed, text="Alimentos del Plan",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=7, column=0, columnspan=4, padx=8, pady=(8, 4), sticky="w")

        # Add item row
        add_row = ctk.CTkFrame(ed, fg_color="transparent")
        add_row.grid(row=8, column=0, columnspan=4, padx=8, pady=4, sticky="ew")
        add_row.grid_columnconfigure(1, weight=1)

        self._item_meal_var = ctk.StringVar(value=MEAL_TYPES[0])
        ctk.CTkOptionMenu(add_row, values=MEAL_TYPES,
                          variable=self._item_meal_var, width=150, height=32
                          ).grid(row=0, column=0, padx=(0, 6))

        self._item_food_var = ctk.StringVar()
        ctk.CTkEntry(add_row, textvariable=self._item_food_var,
                     placeholder_text="Alimento", height=32
                     ).grid(row=0, column=1, padx=(0, 6), sticky="ew")

        self._item_qty_var = ctk.StringVar()
        ctk.CTkEntry(add_row, textvariable=self._item_qty_var,
                     placeholder_text="Cant.", width=60, height=32
                     ).grid(row=0, column=2, padx=(0, 6))

        self._item_unit_var = ctk.StringVar(value=UNITS[0])
        ctk.CTkOptionMenu(add_row, values=UNITS,
                          variable=self._item_unit_var, width=90, height=32
                          ).grid(row=0, column=3, padx=(0, 6))

        # Nutrient entries
        self._item_kcal_var  = ctk.StringVar()
        self._item_prot_var  = ctk.StringVar()
        self._item_carb_var  = ctk.StringVar()
        self._item_fat_var   = ctk.StringVar()

        for i, (var, ph) in enumerate([
            (self._item_kcal_var, "kcal"),
            (self._item_prot_var, "Prot"),
            (self._item_carb_var, "HC"),
            (self._item_fat_var,  "Gras"),
        ]):
            ctk.CTkEntry(add_row, textvariable=var, placeholder_text=ph,
                         width=55, height=32
                         ).grid(row=0, column=4 + i, padx=(0, 4))

        ctk.CTkButton(
            add_row, text="Agregar", width=80, height=32,
            command=self._add_item
        ).grid(row=0, column=8, padx=(4, 0))

        # Items list
        self._items_scroll = ctk.CTkScrollableFrame(ed, height=220)
        self._items_scroll.grid(row=9, column=0, columnspan=4,
                                 padx=8, pady=(4, 8), sticky="ew")
        self._items_scroll.grid_columnconfigure(1, weight=1)

    # ── Events ────────────────────────────────────────────────────────────────
    def on_show(self):
        pid = self.app.get_patient_id()
        if pid:
            p = db.get_patient(pid)
            if p:
                self._patient_lbl.configure(text=f"Paciente: {p['name']}")
                self._load_plans()
                return
        self._patient_lbl.configure(text="Ningún paciente seleccionado")

    def _load_plans(self):
        for w in self._plan_scroll.winfo_children():
            w.destroy()

        pid = self.app.get_patient_id()
        if not pid:
            return

        plans = db.get_meal_plans(pid)
        if not plans:
            ctk.CTkLabel(self._plan_scroll, text="Sin planes.",
                         text_color="gray").pack(pady=20)
            return

        for plan in plans:
            mid = plan["id"]
            frame = ctk.CTkFrame(self._plan_scroll, fg_color="transparent")
            frame.pack(fill="x", pady=3)

            ctk.CTkButton(
                frame, text=f"{plan['name']}\n{plan['date']}",
                height=48, anchor="w",
                font=ctk.CTkFont(size=12),
                fg_color=("#e8f5ee", "#1a2e22"),
                hover_color=("#d1fae5", "#14532d"),
                text_color=("gray10", "gray90"),
                command=lambda m=mid: self._select_plan(m)
            ).pack(side="left", expand=True, fill="x", padx=(0, 4))

            ctk.CTkButton(
                frame, text="✕", width=28, height=48,
                fg_color="#dc2626", hover_color="#991b1b",
                command=lambda m=mid: self._delete_plan(m)
            ).pack(side="right")

    def _new_plan(self):
        pid = self.app.get_patient_id()
        if not pid:
            messagebox.showwarning("Sin paciente",
                                   "Selecciona un paciente primero.")
            return
        self._selected_plan_id = None
        self._clear_plan_editor()
        self._show_editor()

    def _select_plan(self, mid: int):
        self._selected_plan_id = mid
        plan = db.get_meal_plan(mid)
        if not plan:
            return
        self._clear_plan_editor()
        self._plan_vars["name"].set(plan.get("name", ""))
        self._plan_vars["date"].set(plan.get("date", ""))
        self._goal_var.set(plan.get("goal") or GOALS[0])
        self._plan_vars["calories"].set(str(plan.get("calories") or ""))
        self._plan_vars["protein_g"].set(str(plan.get("protein_g") or ""))
        self._plan_vars["carbs_g"].set(str(plan.get("carbs_g") or ""))
        self._plan_vars["fat_g"].set(str(plan.get("fat_g") or ""))
        notes = plan.get("notes") or ""
        self._plan_notes.delete("1.0", "end")
        self._plan_notes.insert("1.0", notes)
        self._show_editor()
        self._load_items()

    def _show_editor(self):
        self._detail_placeholder.grid_remove()
        self._editor.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def _clear_plan_editor(self):
        for v in self._plan_vars.values():
            v.set("")
        self._plan_vars["date"].set(date.today().isoformat())
        self._goal_var.set(GOALS[0])
        self._plan_notes.delete("1.0", "end")
        for w in self._items_scroll.winfo_children():
            w.destroy()

    def _auto_macros(self):
        pid = self.app.get_patient_id()
        if not pid:
            return
        records = db.get_anthropometrics(pid)
        if not records:
            messagebox.showinfo("Sin datos",
                                "No hay evaluaciones antropométricas.\n"
                                "Ingresa una evaluación primero.")
            return
        latest = records[0]
        tdee_val = latest.get("tdee")
        if not tdee_val:
            messagebox.showinfo("Sin TDER",
                                "No se encontró TDER en la última evaluación.")
            return
        goal = self._goal_var.get()
        if "Pérdida" in goal:
            cals = round(tdee_val * 0.8)
        elif "Ganancia" in goal:
            cals = round(tdee_val * 1.15)
        else:
            cals = round(tdee_val)
        macros = calc.macro_distribution(cals)
        self._plan_vars["calories"].set(str(cals))
        self._plan_vars["protein_g"].set(str(macros["protein_g"]))
        self._plan_vars["carbs_g"].set(str(macros["carbs_g"]))
        self._plan_vars["fat_g"].set(str(macros["fat_g"]))

    def _save_plan_header(self):
        pid = self.app.get_patient_id()
        if not pid:
            return
        name = self._plan_vars["name"].get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre del plan es obligatorio.")
            return

        def _float(k):
            try:
                return float(self._plan_vars[k].get())
            except ValueError:
                return None

        data = {
            "patient_id": pid,
            "name":       name,
            "date":       self._plan_vars["date"].get().strip(),
            "goal":       self._goal_var.get(),
            "calories":   _float("calories"),
            "protein_g":  _float("protein_g"),
            "carbs_g":    _float("carbs_g"),
            "fat_g":      _float("fat_g"),
            "notes":      self._plan_notes.get("1.0", "end").strip() or None,
        }

        if self._selected_plan_id is None:
            mid = db.insert_meal_plan(data)
            self._selected_plan_id = mid
        else:
            db.update_meal_plan(self._selected_plan_id, data)

        messagebox.showinfo("Guardado", "Plan guardado.")
        self._load_plans()

    def _delete_plan(self, mid: int):
        if messagebox.askyesno("Eliminar plan",
                               "¿Eliminar este plan y todos sus alimentos?"):
            db.delete_meal_plan(mid)
            if self._selected_plan_id == mid:
                self._selected_plan_id = None
                self._editor.grid_remove()
                self._detail_placeholder.grid(row=0, column=0, pady=60)
            self._load_plans()

    # ── Items ─────────────────────────────────────────────────────────────────
    def _add_item(self):
        if self._selected_plan_id is None:
            messagebox.showwarning("Sin plan",
                                   "Guarda primero la cabecera del plan.")
            return
        food = self._item_food_var.get().strip()
        if not food:
            messagebox.showerror("Error", "El nombre del alimento es obligatorio.")
            return

        def _f(var):
            try:
                return float(var.get())
            except ValueError:
                return None

        data = {
            "plan_id":   self._selected_plan_id,
            "meal_type": self._item_meal_var.get(),
            "food_name": food,
            "quantity":  _f(self._item_qty_var),
            "unit":      self._item_unit_var.get(),
            "calories":  _f(self._item_kcal_var),
            "protein_g": _f(self._item_prot_var),
            "carbs_g":   _f(self._item_carb_var),
            "fat_g":     _f(self._item_fat_var),
        }
        db.insert_meal_item(data)
        self._item_food_var.set("")
        self._item_qty_var.set("")
        self._item_kcal_var.set("")
        self._item_prot_var.set("")
        self._item_carb_var.set("")
        self._item_fat_var.set("")
        self._load_items()

    def _load_items(self):
        for w in self._items_scroll.winfo_children():
            w.destroy()

        if not self._selected_plan_id:
            return

        items = db.get_meal_items(self._selected_plan_id)
        if not items:
            ctk.CTkLabel(self._items_scroll,
                         text="Sin alimentos aún.", text_color="gray"
                         ).pack(pady=12)
            return

        headers = ["Tiempo", "Alimento", "Cant.", "Unid.",
                   "kcal", "Prot", "HC", "Gras", ""]
        for col, h in enumerate(headers):
            ctk.CTkLabel(
                self._items_scroll, text=h,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="gray"
            ).grid(row=0, column=col, padx=4, pady=(4, 6), sticky="w")

        self._items_scroll.grid_columnconfigure(1, weight=1)

        for i, item in enumerate(items, start=1):
            vals = [
                item.get("meal_type", "—"),
                item.get("food_name", "—"),
                str(item.get("quantity") or "—"),
                item.get("unit", "—"),
                str(item.get("calories") or "—"),
                str(item.get("protein_g") or "—"),
                str(item.get("carbs_g") or "—"),
                str(item.get("fat_g") or "—"),
            ]
            for col, val in enumerate(vals):
                ctk.CTkLabel(
                    self._items_scroll, text=val,
                    font=ctk.CTkFont(size=11)
                ).grid(row=i, column=col, padx=4, pady=3, sticky="w")

            iid = item["id"]
            ctk.CTkButton(
                self._items_scroll, text="✕", width=26, height=26,
                fg_color="#dc2626", hover_color="#991b1b",
                font=ctk.CTkFont(size=10),
                command=lambda ii=iid: self._delete_item(ii)
            ).grid(row=i, column=8, padx=4, pady=3)

    def _delete_item(self, iid: int):
        db.delete_meal_item(iid)
        self._load_items()
