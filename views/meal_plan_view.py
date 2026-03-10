import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from typing import Optional
import database.db_manager as db
import utils.calculations as calc
from views.custom_food_dialog import CustomFoodDialog
from views.templates_view import (
    SaveAsTemplateDialog, TemplatePickerDialog, NewPlanChoiceDialog
)


MEAL_TYPES = ["Desayuno", "Media mañana", "Almuerzo",
              "Merienda", "Cena", "Colación"]
UNITS = ["g", "ml", "taza", "cdta", "cda", "unidad", "porción", "rebanada"]
GOALS = ["Pérdida de peso", "Mantenimiento", "Ganancia muscular",
         "Control glucémico", "Salud cardiovascular", "Otro"]

# Color por tiempo de comida
_MEAL_COLORS = {
    "Desayuno":     ("#fef3c7", "#78350f"),
    "Media mañana": ("#d1fae5", "#065f46"),
    "Almuerzo":     ("#dbeafe", "#1e3a5f"),
    "Merienda":     ("#fce7f3", "#831843"),
    "Cena":         ("#ede9fe", "#4c1d95"),
    "Colación":     ("#f1f5f9", "#334155"),
}
_MEAL_COLORS_DARK = {
    "Desayuno":     ("#78350f", "#fef3c7"),
    "Media mañana": ("#065f46", "#d1fae5"),
    "Almuerzo":     ("#1e3a5f", "#dbeafe"),
    "Merienda":     ("#831843", "#fce7f3"),
    "Cena":         ("#4c1d95", "#ede9fe"),
    "Colación":     ("#334155", "#f1f5f9"),
}


def _meal_color(meal_type: str) -> tuple[str, str]:
    """Returns (light_bg, dark_bg) for the meal type."""
    return _MEAL_COLORS.get(meal_type, ("#f8fafc", "#1e293b"))


class MealPlanFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app
        self._selected_plan_id: Optional[int] = None
        self._build_ui()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
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

        ctk.CTkFrame(self, height=1, fg_color=("gray85", "gray30")
                     ).grid(row=1, column=0, sticky="ew", padx=24, pady=(12, 0))

        # Main split: left list + right detail
        panes = ctk.CTkFrame(self, fg_color="transparent")
        panes.grid(row=2, column=0, sticky="nsew", padx=24, pady=(8, 20))
        panes.grid_columnconfigure(1, weight=1)
        panes.grid_rowconfigure(0, weight=1)

        self._build_left_panel(panes)
        self._build_right_panel(panes)

    def _build_left_panel(self, parent):
        left = ctk.CTkFrame(parent, width=240)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            left, text="+ Nuevo Plan", height=42,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._new_plan
        ).grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self._plan_scroll = ctk.CTkScrollableFrame(left, label_text="Mis planes")
        self._plan_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 8))
        self._plan_scroll.grid_columnconfigure(0, weight=1)

    def _build_right_panel(self, parent):
        self._right = ctk.CTkFrame(parent)
        self._right.grid(row=0, column=1, sticky="nsew")
        self._right.grid_columnconfigure(0, weight=1)
        self._right.grid_rowconfigure(0, weight=1)

        # Placeholder frame (shown when no plan is open)
        self._placeholder = ctk.CTkFrame(self._right, fg_color="transparent")
        self._placeholder.grid(row=0, column=0)
        self._placeholder.grid_columnconfigure(0, weight=1)

        self._placeholder_icon = ctk.CTkLabel(
            self._placeholder, text="🥗",
            font=ctk.CTkFont(size=48)
        )
        self._placeholder_icon.grid(row=0, column=0, pady=(40, 8))

        self._placeholder_title = ctk.CTkLabel(
            self._placeholder, text="Sin paciente seleccionado",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self._placeholder_title.grid(row=1, column=0, pady=(0, 6))

        self._placeholder_desc = ctk.CTkLabel(
            self._placeholder,
            text="Ve a la lista de pacientes y selecciona uno\npara ver o crear sus planes alimenticios.",
            font=ctk.CTkFont(size=13), text_color="gray", justify="center"
        )
        self._placeholder_desc.grid(row=2, column=0, pady=(0, 20))

        self._placeholder_btn = ctk.CTkButton(
            self._placeholder, text="Ir a lista de pacientes",
            height=36, width=200,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            command=lambda: self.app._show_frame("patients")
        )
        self._placeholder_btn.grid(row=3, column=0)

        # Tab view (hidden until a plan is loaded)
        self._tabs = ctk.CTkTabview(self._right, anchor="nw",
                                    command=self._on_tab_change)
        self._tabs.grid_columnconfigure(0, weight=1)

        self._tab_info = self._tabs.add("  Información  ")
        self._tab_items = self._tabs.add("  Alimentos  ")
        self._tabs.set("  Información  ")

        self._build_info_tab()
        self._build_items_tab()

    # ── Tab: Información ──────────────────────────────────────────────────────

    def _build_info_tab(self):
        tab = self._tab_info
        tab.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._plan_vars: dict[str, ctk.StringVar] = {}

        # Row 0: Name + Date + Goal
        ctk.CTkLabel(tab, text="Nombre del plan", text_color="gray",
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, columnspan=2, padx=8, pady=(12, 0), sticky="w")
        self._plan_vars["name"] = ctk.StringVar()
        ctk.CTkEntry(tab, textvariable=self._plan_vars["name"], height=36
                     ).grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(tab, text="Fecha", text_color="gray",
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, padx=8, pady=(12, 0), sticky="w")
        self._plan_vars["date"] = ctk.StringVar(value=date.today().isoformat())
        ctk.CTkEntry(tab, textvariable=self._plan_vars["date"], height=36
                     ).grid(row=1, column=2, padx=8, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(tab, text="Objetivo", text_color="gray",
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=3, padx=8, pady=(12, 0), sticky="w")
        self._goal_var = ctk.StringVar(value=GOALS[0])
        ctk.CTkOptionMenu(tab, values=GOALS, variable=self._goal_var, height=36
                          ).grid(row=1, column=3, padx=8, pady=(0, 8), sticky="ew")

        # Divider
        ctk.CTkFrame(tab, height=1, fg_color=("gray85", "gray30")
                     ).grid(row=2, column=0, columnspan=4, sticky="ew", padx=8, pady=4)

        # Row 1: Macro targets
        ctk.CTkLabel(
            tab, text="Objetivos nutricionales del plan",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="gray"
        ).grid(row=3, column=0, columnspan=4, padx=8, pady=(4, 2), sticky="w")

        macro_defs = [
            ("Calorías (kcal)", "calories"),
            ("Proteínas (g)",   "protein_g"),
            ("Carbohidratos (g)", "carbs_g"),
            ("Grasas (g)",      "fat_g"),
        ]
        for col, (label, key) in enumerate(macro_defs):
            ctk.CTkLabel(tab, text=label, text_color="gray",
                         font=ctk.CTkFont(size=11)).grid(
                row=4, column=col, padx=8, pady=(6, 0), sticky="w")
            self._plan_vars[key] = ctk.StringVar()
            ctk.CTkEntry(tab, textvariable=self._plan_vars[key], height=36
                         ).grid(row=5, column=col, padx=8, pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            tab, text="Auto-calcular desde TDER", height=34,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self._auto_macros
        ).grid(row=6, column=0, columnspan=2, padx=8, pady=4, sticky="ew")

        ctk.CTkButton(
            tab, text="Guardar plan", height=34,
            command=self._save_plan_header
        ).grid(row=6, column=2, columnspan=2, padx=8, pady=4, sticky="ew")

        ctk.CTkButton(
            tab, text="★  Guardar como plantilla", height=30,
            fg_color="transparent", border_width=1,
            text_color=("#059669", "#34d399"),
            font=ctk.CTkFont(size=11),
            command=self._save_as_template
        ).grid(row=7, column=2, columnspan=2, padx=8, pady=(0, 4), sticky="ew")

        # Template source badge
        self._template_badge = ctk.CTkLabel(
            tab, text="", text_color="#059669",
            font=ctk.CTkFont(size=11), anchor="w"
        )
        self._template_badge.grid(row=7, column=0, columnspan=2,
                                   padx=8, pady=(0, 4), sticky="w")

        # Notes
        ctk.CTkLabel(tab, text="Notas", text_color="gray",
                     font=ctk.CTkFont(size=12)).grid(
            row=8, column=0, columnspan=4, padx=8, pady=(8, 0), sticky="w")
        self._plan_notes = ctk.CTkTextbox(tab, height=80)
        self._plan_notes.grid(row=9, column=0, columnspan=4,
                               padx=8, pady=(0, 12), sticky="ew")

    # ── Tab: Alimentos ────────────────────────────────────────────────────────

    def _build_items_tab(self):
        tab = self._tab_items
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # ── Add item form ─────────────────────────────────────────────────────
        add_frame = ctk.CTkFrame(tab, fg_color=("gray95", "gray17"), corner_radius=8)
        add_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=(8, 4))
        add_frame.grid_columnconfigure(1, weight=1)

        # Row 0: header + personalizado button
        ctk.CTkLabel(add_frame, text="Agregar alimento",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray"
                     ).grid(row=0, column=0, columnspan=3, padx=10, pady=(8, 2), sticky="w")

        ctk.CTkButton(
            add_frame, text="+ Personalizado", height=26, width=130,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            command=self._open_custom_food
        ).grid(row=0, column=3, padx=(4, 8), pady=(8, 2), sticky="e")

        # Row 1: labels
        for col, txt in enumerate(["Tiempo de comida", "Buscar alimento", "Cant. (g)"]):
            ctk.CTkLabel(add_frame, text=txt, text_color="gray",
                         font=ctk.CTkFont(size=11)
                         ).grid(row=1, column=col, padx=(8 if col == 0 else 4, 4),
                                pady=(4, 0), sticky="w")

        # Row 2: meal type + search entry + qty
        self._item_meal_var = ctk.StringVar(value=MEAL_TYPES[0])
        ctk.CTkOptionMenu(add_frame, values=MEAL_TYPES,
                          variable=self._item_meal_var, width=140, height=32
                          ).grid(row=2, column=0, padx=(8, 4), pady=(0, 2))

        self._search_suppress = False
        self._selected_food: Optional[dict] = None
        self._item_food_var = ctk.StringVar()
        self._item_food_var.trace_add("write", self._on_food_search)
        self._search_entry = ctk.CTkEntry(
            add_frame, textvariable=self._item_food_var,
            placeholder_text="Ej: pollo, arroz, manzana…", height=32)
        self._search_entry.grid(row=2, column=1, padx=4, pady=(0, 2), sticky="ew")

        self._item_qty_var = ctk.StringVar(value="100")
        self._item_qty_var.trace_add("write", lambda *_: self._update_macro_preview())
        ctk.CTkEntry(add_frame, textvariable=self._item_qty_var,
                     width=72, height=32
                     ).grid(row=2, column=2, padx=4, pady=(0, 2))

        # Row 3: search results (hidden by default)
        self._search_results = ctk.CTkScrollableFrame(add_frame, height=130,
                                                       fg_color=("white", "gray15"))
        self._search_results.grid(row=3, column=1, padx=4, pady=(0, 2), sticky="ew")
        self._search_results.grid_columnconfigure(0, weight=1)
        self._search_results.grid_remove()   # hidden initially

        # Row 4: macro preview bar
        self._preview_bar = ctk.CTkFrame(add_frame, fg_color=("gray88", "gray22"),
                                          corner_radius=6)
        self._preview_bar.grid(row=4, column=0, columnspan=4,
                                sticky="ew", padx=8, pady=(2, 2))
        self._preview_bar.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._preview_labels: dict[str, ctk.CTkLabel] = {}
        for col, (key, txt) in enumerate([
            ("kcal", "Calorías"),
            ("prot", "Proteínas"),
            ("carb", "Carbohidr."),
            ("fat",  "Grasas"),
            ("fiber","Fibra"),
        ]):
            ctk.CTkLabel(self._preview_bar, text=txt, text_color="gray",
                         font=ctk.CTkFont(size=9)).grid(
                row=0, column=col, padx=6, pady=(4, 0))
            lbl = ctk.CTkLabel(self._preview_bar, text="—",
                               font=ctk.CTkFont(size=11, weight="bold"))
            lbl.grid(row=1, column=col, padx=6, pady=(0, 6))
            self._preview_labels[key] = lbl

        # Row 5: add button
        ctk.CTkButton(
            add_frame, text="+ Agregar al plan", height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._add_item
        ).grid(row=5, column=0, columnspan=4, padx=8, pady=(4, 10), sticky="e")

        # ── Items list (scrollable, grouped) ─────────────────────────────────
        self._items_scroll = ctk.CTkScrollableFrame(tab)
        self._items_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(4, 0))
        self._items_scroll.grid_columnconfigure(1, weight=1)

        # ── Macro totals bar ──────────────────────────────────────────────────
        self._totals_bar = ctk.CTkFrame(tab, fg_color=("gray90", "gray20"),
                                        corner_radius=8)
        self._totals_bar.grid(row=2, column=0, sticky="ew", padx=4, pady=(6, 8))
        self._totals_bar.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._total_labels: dict[str, ctk.CTkLabel] = {}
        for col, (key, icon) in enumerate([
            ("calories",  "Calorías"),
            ("protein_g", "Proteínas"),
            ("carbs_g",   "Carbohidr."),
            ("fat_g",     "Grasas"),
            ("fiber_g",   "Fibra"),
        ]):
            ctk.CTkLabel(self._totals_bar, text=icon, text_color="gray",
                         font=ctk.CTkFont(size=10)).grid(
                row=0, column=col, padx=10, pady=(6, 0))
            lbl = ctk.CTkLabel(self._totals_bar, text="—",
                               font=ctk.CTkFont(size=12, weight="bold"))
            lbl.grid(row=1, column=col, padx=10, pady=(0, 8))
            self._total_labels[key] = lbl

    # ── Navigation & refresh ──────────────────────────────────────────────────

    def on_show(self):
        pid = self.app.get_patient_id()
        if pid:
            p = db.get_patient(pid)
            if p:
                self._patient_lbl.configure(text=f"Paciente: {p['name']}")
                self._load_plans()
                # Handle plan pre-selected from template application
                pending = getattr(self.app, "_pending_plan_id", None)
                if pending:
                    self.app._pending_plan_id = None
                    self._select_plan(pending)
                return
        # No patient selected
        self._patient_lbl.configure(text="Ningún paciente seleccionado")
        self._selected_plan_id = None
        self._hide_tabs()
        self._set_placeholder(
            title="Sin paciente seleccionado",
            desc="Ve a la lista de pacientes y selecciona uno\npara ver o crear sus planes alimenticios.",
            show_btn=True
        )
        for w in self._plan_scroll.winfo_children():
            w.destroy()

    def _on_tab_change(self):
        """Auto-save header when user switches to Alimentos tab."""
        tab_name = self._tabs.get()
        if "Alimentos" in tab_name and self._selected_plan_id is not None:
            self._save_plan_header(silent=True)
        if "Alimentos" in tab_name:
            self._load_items()

    def _set_placeholder(self, title: str, desc: str, show_btn: bool = False):
        self._placeholder_title.configure(text=title)
        self._placeholder_desc.configure(text=desc)
        if show_btn:
            self._placeholder_btn.grid(row=3, column=0, pady=(0, 20))
        else:
            self._placeholder_btn.grid_remove()

    def _show_tabs(self):
        self._placeholder.grid_remove()
        self._tabs.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def _hide_tabs(self):
        self._tabs.grid_remove()
        self._placeholder.grid(row=0, column=0)

    # ── Plan list ─────────────────────────────────────────────────────────────

    def _load_plans(self):
        for w in self._plan_scroll.winfo_children():
            w.destroy()

        pid = self.app.get_patient_id()
        if not pid:
            return

        plans = db.get_meal_plans(pid)
        if not plans:
            ctk.CTkLabel(self._plan_scroll,
                         text="Este paciente aún\nno tiene planes.\n\nPresiona\n«+ Nuevo Plan»\npara crear uno.",
                         text_color="gray", font=ctk.CTkFont(size=12),
                         justify="center").pack(pady=20)
            self._hide_tabs()
            self._set_placeholder(
                title="Sin planes alimenticios",
                desc=f"Crea el primer plan para este paciente\nusando el botón «+ Nuevo Plan» a la izquierda.",
                show_btn=False
            )
            return

        for plan in plans:
            mid = plan["id"]
            is_selected = (mid == self._selected_plan_id)

            frame = ctk.CTkFrame(self._plan_scroll, fg_color="transparent")
            frame.pack(fill="x", pady=2)

            btn_color = ("#d1fae5", "#14532d") if is_selected else ("#e8f5ee", "#1a2e22")
            ctk.CTkButton(
                frame,
                text=f"{plan['name']}\n{plan['date']}  •  {plan.get('goal') or ''}",
                height=52, anchor="w",
                font=ctk.CTkFont(size=11),
                fg_color=btn_color,
                hover_color=("#bbf7d0", "#166534"),
                text_color=("gray10", "gray90"),
                command=lambda m=mid: self._select_plan(m)
            ).pack(side="left", expand=True, fill="x", padx=(0, 4))

            ctk.CTkButton(
                frame, text="✕", width=28, height=52,
                fg_color="#dc2626", hover_color="#991b1b",
                command=lambda m=mid: self._delete_plan(m)
            ).pack(side="right")

    # ── Plan CRUD ─────────────────────────────────────────────────────────────

    def _new_plan(self):
        pid = self.app.get_patient_id()
        if not pid:
            messagebox.showwarning("Sin paciente",
                                   "Selecciona un paciente primero.")
            return
        NewPlanChoiceDialog(
            self,
            on_scratch=self._new_plan_from_scratch,
            on_template=self._new_plan_pick_template,
        )

    def _new_plan_from_scratch(self):
        self._selected_plan_id = None
        self._clear_editor()
        self._show_tabs()
        self._tabs.set("  Información  ")

    def _new_plan_pick_template(self):
        TemplatePickerDialog(self, on_pick=self._new_plan_from_template)

    def _new_plan_from_template(self, template_id: int):
        pid = self.app.get_patient_id()
        if not pid:
            return
        t = db.get_template(template_id)

        self._selected_plan_id = None
        self._clear_editor()

        # Pre-fill from template
        self._plan_vars["name"].set(t.get("name", ""))
        self._plan_vars["date"].set(date.today().isoformat())
        goal = t.get("goal") or GOALS[0]
        if goal in GOALS:
            self._goal_var.set(goal)
        self._plan_vars["calories"].set(str(t.get("calories") or ""))
        self._plan_vars["protein_g"].set(str(t.get("protein_g") or ""))
        self._plan_vars["carbs_g"].set(str(t.get("carbs_g") or ""))
        self._plan_vars["fat_g"].set(str(t.get("fat_g") or ""))
        if t.get("notes"):
            self._plan_notes.insert("1.0", t["notes"])

        # Auto-save plan then import items
        data = {
            "patient_id": pid,
            "name": t.get("name", "Plan desde plantilla"),
            "date": date.today().isoformat(),
            "goal": goal,
            "calories": t.get("calories"),
            "protein_g": t.get("protein_g"),
            "carbs_g": t.get("carbs_g"),
            "fat_g": t.get("fat_g"),
            "notes": t.get("notes"),
            "template_id": template_id,
        }
        plan_id = db.insert_meal_plan(data)
        self._selected_plan_id = plan_id
        db.apply_template_to_plan(template_id, plan_id)
        db.record_template_usage(template_id, pid, plan_id)

        self._show_tabs()
        self._load_plans()
        self._tabs.set("  Alimentos  ")
        self._load_items()
        self._update_template_badge(plan_id)
        self.app.show_toast(f"Plan creado desde plantilla «{t['name']}».")

    def _select_plan(self, mid: int):
        self._selected_plan_id = mid
        plan = db.get_meal_plan(mid)
        if not plan:
            return
        self._clear_editor()
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
        self._update_template_badge(mid)
        self._show_tabs()
        self._tabs.set("  Información  ")
        self._load_plans()  # refresh highlight

    def _clear_editor(self):
        for v in self._plan_vars.values():
            v.set("")
        self._plan_vars["date"].set(date.today().isoformat())
        self._goal_var.set(GOALS[0])
        self._plan_notes.delete("1.0", "end")
        self._template_badge.configure(text="")
        for w in self._items_scroll.winfo_children():
            w.destroy()
        self._reset_totals_bar()
        self._selected_food = None
        self._search_suppress = True
        self._item_food_var.set("")
        self._item_qty_var.set("100")
        self._search_suppress = False
        self._search_results.grid_remove()
        for lbl in self._preview_labels.values():
            lbl.configure(text="—")

    def _save_plan_header(self, silent: bool = False):
        pid = self.app.get_patient_id()
        if not pid:
            return
        name = self._plan_vars["name"].get().strip()
        if not name:
            if not silent:
                messagebox.showerror("Error", "El nombre del plan es obligatorio.")
            return False

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

        if not silent:
            messagebox.showinfo("Guardado", "Plan guardado correctamente.")
        self._load_plans()
        return True

    def _delete_plan(self, mid: int):
        if messagebox.askyesno("Eliminar plan",
                               "¿Eliminar este plan y todos sus alimentos?"):
            db.delete_meal_plan(mid)
            if self._selected_plan_id == mid:
                self._selected_plan_id = None
                self._hide_tabs()
            self._load_plans()

    def _save_as_template(self):
        if self._selected_plan_id is None:
            if not self._save_plan_header(silent=False):
                return
            if self._selected_plan_id is None:
                return
        plan = db.get_meal_plan(self._selected_plan_id)
        plan_name = plan.get("name", "") if plan else ""

        def _on_saved(tid: int):
            t = db.get_template(tid)
            self.app.show_toast(f"Plantilla «{t['name']}» guardada en la biblioteca.")

        SaveAsTemplateDialog(self, self._selected_plan_id, plan_name, _on_saved)

    def _update_template_badge(self, plan_id: int):
        plan = db.get_meal_plan(plan_id)
        tid = plan.get("template_id") if plan else None
        if tid:
            t = db.get_template(tid)
            name = t["name"] if t else "plantilla eliminada"
            self._template_badge.configure(text=f"★ Creado desde: «{name}»")
        else:
            self._template_badge.configure(text="")

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
        latest = records[-1]  # most recent
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

    # ── Food search ───────────────────────────────────────────────────────────

    def _on_food_search(self, *_):
        if self._search_suppress:
            return
        query = self._item_food_var.get().strip()
        if len(query) < 2:
            self._search_results.grid_remove()
            return
        results = db.search_foods(query, limit=12)
        for w in self._search_results.winfo_children():
            w.destroy()
        if results:
            for food in results:
                name = food["nombre_es"]
                kcal = food["calorias"]
                ctk.CTkButton(
                    self._search_results,
                    text=f"{name}  —  {kcal:.0f} kcal/100 g",
                    anchor="w",
                    height=28,
                    fg_color="transparent",
                    hover_color=("#d1fae5", "#14532d"),
                    text_color=("gray10", "gray90"),
                    font=ctk.CTkFont(size=11),
                    command=lambda f=food: self._select_food(f)
                ).pack(fill="x", pady=1, padx=2)
            self._search_results.grid()
        else:
            self._search_results.grid_remove()

    def _select_food(self, food: dict):
        self._search_suppress = True
        self._item_food_var.set(food["nombre_es"])
        self._search_suppress = False
        self._selected_food = food
        self._search_results.grid_remove()
        self._update_macro_preview()

    def _update_macro_preview(self):
        food = self._selected_food
        if not food:
            for lbl in self._preview_labels.values():
                lbl.configure(text="—")
            return
        try:
            qty = float(self._item_qty_var.get() or "100")
        except ValueError:
            qty = 100.0
        factor = qty / 100.0
        kcal  = (food.get("calorias")        or 0) * factor
        prot  = (food.get("proteinas_g")     or 0) * factor
        carb  = (food.get("carbohidratos_g") or 0) * factor
        fat   = (food.get("grasas_g")        or 0) * factor
        fiber = (food.get("fibra_g")         or 0) * factor
        self._preview_labels["kcal"].configure( text=f"{kcal:.0f} kcal")
        self._preview_labels["prot"].configure( text=f"{prot:.1f} g")
        self._preview_labels["carb"].configure( text=f"{carb:.1f} g")
        self._preview_labels["fat"].configure(  text=f"{fat:.1f} g")
        self._preview_labels["fiber"].configure(text=f"{fiber:.1f} g")

    def _open_custom_food(self):
        def _on_saved(food: dict):
            self._select_food(food)
        CustomFoodDialog(self, on_save=_on_saved)

    # ── Items ─────────────────────────────────────────────────────────────────

    def _add_item(self):
        if self._selected_plan_id is None:
            if not self._save_plan_header(silent=False):
                return
            if self._selected_plan_id is None:
                return

        food_name = self._item_food_var.get().strip()
        if not food_name:
            messagebox.showerror("Error", "Escribe o busca un alimento primero.")
            return

        try:
            qty = float(self._item_qty_var.get() or "0") or None
        except ValueError:
            qty = None

        # Calculate macros from selected DB food or leave None
        food = self._selected_food
        if food and qty:
            factor = qty / 100.0
            calories  = round((food.get("calorias")        or 0) * factor, 1)
            protein_g = round((food.get("proteinas_g")     or 0) * factor, 1)
            carbs_g   = round((food.get("carbohidratos_g") or 0) * factor, 1)
            fat_g     = round((food.get("grasas_g")        or 0) * factor, 1)
            fiber_g   = round((food.get("fibra_g")         or 0) * factor, 1)
        else:
            calories = protein_g = carbs_g = fat_g = fiber_g = None

        db.insert_meal_item({
            "plan_id":   self._selected_plan_id,
            "meal_type": self._item_meal_var.get(),
            "food_name": food_name,
            "quantity":  qty,
            "unit":      "g",
            "calories":  calories,
            "protein_g": protein_g,
            "carbs_g":   carbs_g,
            "fat_g":     fat_g,
            "fiber_g":   fiber_g,
        })
        # Reset form
        self._search_suppress = True
        self._item_food_var.set("")
        self._search_suppress = False
        self._item_qty_var.set("100")
        self._selected_food = None
        for lbl in self._preview_labels.values():
            lbl.configure(text="—")
        self._search_results.grid_remove()
        self._load_items()

    def _load_items(self):
        for w in self._items_scroll.winfo_children():
            w.destroy()

        if not self._selected_plan_id:
            self._reset_totals_bar()
            return

        items = db.get_meal_items(self._selected_plan_id)
        if not items:
            ctk.CTkLabel(self._items_scroll,
                         text="Aún no hay alimentos en este plan.",
                         text_color="gray", font=ctk.CTkFont(size=13)
                         ).pack(pady=24)
            self._reset_totals_bar()
            return

        # Group items by meal type preserving MEAL_TYPES order
        groups: dict[str, list] = {m: [] for m in MEAL_TYPES}
        for item in items:
            mt = item.get("meal_type", "Colación")
            groups.setdefault(mt, []).append(item)

        totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0}

        for meal_type in MEAL_TYPES:
            group = groups.get(meal_type, [])
            if not group:
                continue

            # Section header
            light_bg, dark_bg = _meal_color(meal_type)
            section_hdr = ctk.CTkFrame(
                self._items_scroll,
                fg_color=(light_bg, dark_bg),
                corner_radius=6
            )
            section_hdr.pack(fill="x", pady=(6, 2), padx=4)
            section_hdr.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                section_hdr, text=meal_type,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("gray15", "gray95")
            ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

            # Sub-totals for this meal
            mt_kcal = sum(i.get("calories") or 0 for i in group)
            ctk.CTkLabel(
                section_hdr,
                text=f"{mt_kcal:.0f} kcal",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).grid(row=0, column=1, padx=8, sticky="e")

            # Column headers
            hdr_row = ctk.CTkFrame(self._items_scroll, fg_color="transparent")
            hdr_row.pack(fill="x", padx=8)
            hdr_row.grid_columnconfigure(0, weight=1)

            for col, (h, w) in enumerate([
                ("Alimento", 0), ("Cant.", 48), ("Unid.", 48),
                ("kcal", 52), ("Prot g", 52), ("HC g", 52), ("Gras g", 52), ("Fibra g", 52), ("", 30)
            ]):
                kw = {"width": w} if w else {}
                ctk.CTkLabel(
                    hdr_row, text=h,
                    font=ctk.CTkFont(size=9, weight="bold"),
                    text_color="gray",
                    **kw
                ).grid(row=0, column=col, padx=4, pady=(2, 0),
                       sticky="w" if col == 0 else "e")
            if not any(w == 0 for _, w in [("Alimento", 0)]):
                hdr_row.grid_columnconfigure(0, weight=1)
            hdr_row.grid_columnconfigure(0, weight=1)

            # Item rows
            for item in group:
                row_frame = ctk.CTkFrame(
                    self._items_scroll,
                    fg_color=("gray97", "gray18"),
                    corner_radius=4
                )
                row_frame.pack(fill="x", padx=8, pady=1)
                row_frame.grid_columnconfigure(0, weight=1)

                vals = [
                    item.get("food_name", "—"),
                    str(item.get("quantity") or "—"),
                    item.get("unit", "—"),
                    _fmt(item.get("calories")),
                    _fmt(item.get("protein_g")),
                    _fmt(item.get("carbs_g")),
                    _fmt(item.get("fat_g")),
                    _fmt(item.get("fiber_g")),
                ]
                widths = [0, 48, 48, 52, 52, 52, 52, 52]
                for col, (val, w) in enumerate(zip(vals, widths)):
                    kw = {"width": w} if w else {}
                    ctk.CTkLabel(
                        row_frame, text=val,
                        font=ctk.CTkFont(size=11),
                        **kw
                    ).grid(row=0, column=col, padx=4, pady=3,
                           sticky="w" if col == 0 else "e")

                iid = item["id"]
                ctk.CTkButton(
                    row_frame, text="✕", width=28, height=24,
                    fg_color="transparent",
                    hover_color=("#fee2e2", "#7f1d1d"),
                    text_color=("#dc2626", "#f87171"),
                    font=ctk.CTkFont(size=10),
                    command=lambda ii=iid: self._delete_item(ii)
                ).grid(row=0, column=8, padx=(2, 4), pady=2)

                # Accumulate totals
                for key in totals:
                    v = item.get(key)
                    if v:
                        totals[key] += v

        self._update_totals_bar(totals)

    def _delete_item(self, iid: int):
        db.delete_meal_item(iid)
        self._load_items()

    # ── Totals bar ────────────────────────────────────────────────────────────

    def _reset_totals_bar(self):
        for lbl in self._total_labels.values():
            lbl.configure(text="—", text_color=("gray40", "gray60"))

    def _update_totals_bar(self, totals: dict):
        plan = db.get_meal_plan(self._selected_plan_id) if self._selected_plan_id else None

        defs = [
            ("calories",  "calories",  "kcal"),
            ("protein_g", "protein_g", "g"),
            ("carbs_g",   "carbs_g",   "g"),
            ("fat_g",     "fat_g",     "g"),
            ("fiber_g",   None,        "g"),
        ]
        for total_key, plan_key, unit in defs:
            actual = totals.get(total_key, 0)
            target = plan.get(plan_key) if (plan and plan_key) else None
            if target:
                pct = actual / target
                color = _progress_color(pct)
                text = f"{actual:.0f} / {target:.0f} {unit}"
            else:
                color = ("gray40", "gray60")
                text = f"{actual:.1f} {unit}" if unit == "g" else f"{actual:.0f} {unit}"
            self._total_labels[total_key].configure(text=text, text_color=color)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt(val) -> str:
    if val is None:
        return "—"
    try:
        f = float(val)
        return f"{f:.1f}" if f != int(f) else str(int(f))
    except (TypeError, ValueError):
        return "—"


def _progress_color(pct: float) -> tuple[str, str]:
    """Green if on target (85–110 %), yellow if low, red if over."""
    if pct < 0.75:
        return ("#b45309", "#fbbf24")   # yellow
    elif pct > 1.15:
        return ("#dc2626", "#f87171")   # red
    else:
        return ("#15803d", "#4ade80")   # green
