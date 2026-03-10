import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from typing import Optional, Callable
import database.db_manager as db

CATEGORIES = [
    "Todas", "Pérdida de peso", "Mantención", "Aumento de masa",
    "Deportista", "Vegetariana", "Vegana", "Sin gluten", "Otra",
]
MEAL_TYPES = ["Desayuno", "Media mañana", "Almuerzo",
              "Merienda", "Cena", "Colación"]


# ── Main Frame ────────────────────────────────────────────────────────────────

class TemplatesFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app
        self._selected_tid: Optional[int] = None
        self._search_var = ctk.StringVar()
        self._cat_var = ctk.StringVar(value="Todas")
        self._build_ui()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hdr, text="Biblioteca de Plantillas",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            hdr, text="+ Nueva plantilla",
            height=36, width=160, corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._new_template
        ).grid(row=0, column=2, sticky="e")

        ctk.CTkFrame(self, height=1, fg_color=("gray85", "gray30")
                     ).grid(row=1, column=0, sticky="ew", padx=24, pady=(12, 0))

        panes = ctk.CTkFrame(self, fg_color="transparent")
        panes.grid(row=2, column=0, sticky="nsew", padx=24, pady=(8, 20))
        panes.grid_columnconfigure(1, weight=1)
        panes.grid_rowconfigure(0, weight=1)

        self._build_left(panes)
        self._build_right(panes)

    def _build_left(self, parent):
        left = ctk.CTkFrame(parent, width=270)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._search_var.trace_add("write", lambda *_: self._load_templates())
        ctk.CTkEntry(
            left, textvariable=self._search_var,
            placeholder_text="Buscar plantilla…", height=34
        ).grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        ctk.CTkOptionMenu(
            left, values=CATEGORIES, variable=self._cat_var, height=32,
            command=lambda _: self._load_templates()
        ).grid(row=1, column=0, padx=8, pady=(0, 4), sticky="ew")

        self._tpl_scroll = ctk.CTkScrollableFrame(left, label_text="Plantillas")
        self._tpl_scroll.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0, 8))
        self._tpl_scroll.grid_columnconfigure(0, weight=1)

    def _build_right(self, parent):
        self._right = ctk.CTkFrame(parent)
        self._right.grid(row=0, column=1, sticky="nsew")
        self._right.grid_columnconfigure(0, weight=1)
        self._right.grid_rowconfigure(1, weight=1)

        # Action toolbar
        self._action_bar = ctk.CTkFrame(self._right, fg_color="transparent")
        self._action_bar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))

        self._btn_apply = ctk.CTkButton(
            self._action_bar, text="Aplicar a paciente",
            height=36, width=170, corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._apply_to_patient
        )
        self._btn_apply.pack(side="left", padx=(4, 6))

        self._btn_edit = ctk.CTkButton(
            self._action_bar, text="Editar",
            height=36, width=80, corner_radius=8,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self._edit_template
        )
        self._btn_edit.pack(side="left", padx=3)

        self._btn_dup = ctk.CTkButton(
            self._action_bar, text="Duplicar",
            height=36, width=90, corner_radius=8,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self._duplicate_template
        )
        self._btn_dup.pack(side="left", padx=3)

        self._btn_del = ctk.CTkButton(
            self._action_bar, text="Eliminar",
            height=36, width=80, corner_radius=8,
            fg_color="#dc2626", hover_color="#991b1b",
            command=self._delete_template
        )
        self._btn_del.pack(side="left", padx=3)

        self._action_bar.grid_remove()

        # Detail area
        self._detail_scroll = ctk.CTkScrollableFrame(
            self._right, fg_color="transparent"
        )
        self._detail_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._detail_scroll.grid_columnconfigure(0, weight=1)

        self._show_empty_detail()

    # ── Navigation ────────────────────────────────────────────────────────────

    def on_show(self):
        self._load_templates()

    # ── Template List ─────────────────────────────────────────────────────────

    def _load_templates(self):
        for w in self._tpl_scroll.winfo_children():
            w.destroy()

        query = self._search_var.get().strip().lower()
        cat = self._cat_var.get()
        templates = db.get_all_templates()

        filtered = [
            t for t in templates
            if (cat == "Todas" or t.get("category") == cat)
            and (not query or query in t["name"].lower()
                 or query in (t.get("description") or "").lower())
        ]

        if not filtered:
            ctk.CTkLabel(
                self._tpl_scroll, text="Sin resultados.",
                text_color="gray", font=ctk.CTkFont(size=12)
            ).pack(pady=16)
            return

        for t in filtered:
            is_sel = (t["id"] == self._selected_tid)
            fg = ("#d1fae5", "#14532d") if is_sel else ("gray92", "gray17")
            hover = ("#bbf7d0", "#166534")

            badge = "★" if t.get("is_predefined") else "▸"
            cal_txt = f"  ·  {t['calories']:.0f} kcal" if t.get("calories") else ""
            uses = t.get("use_count") or 0
            uses_txt = f"  ·  ×{uses}" if uses else ""
            text = (
                f"{badge}  {t['name']}\n"
                f"{t.get('category','')}{cal_txt}{uses_txt}"
            )
            ctk.CTkButton(
                self._tpl_scroll, text=text,
                anchor="w", height=54, corner_radius=8,
                fg_color=fg, hover_color=hover,
                text_color=("gray10", "gray90"),
                font=ctk.CTkFont(size=11),
                command=lambda tid=t["id"]: self._select_template(tid)
            ).pack(fill="x", pady=2, padx=2)

    # ── Template Detail ───────────────────────────────────────────────────────

    def _select_template(self, tid: int):
        self._selected_tid = tid
        t = db.get_template(tid)
        items = db.get_template_items(tid)
        usage = db.get_template_usage(tid)
        self._show_detail(t, items, usage)
        self._load_templates()
        self._action_bar.grid()

    def _show_empty_detail(self):
        for w in self._detail_scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._detail_scroll, text="📋",
            font=ctk.CTkFont(size=48)
        ).pack(pady=(50, 8))
        ctk.CTkLabel(
            self._detail_scroll, text="Selecciona una plantilla",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack()
        ctk.CTkLabel(
            self._detail_scroll,
            text="Elige una plantilla de la lista para ver su contenido\ny aplicarla a un paciente.",
            text_color="gray", font=ctk.CTkFont(size=13), justify="center"
        ).pack(pady=4)

    def _show_detail(self, t: dict, items: list, usage: list):
        for w in self._detail_scroll.winfo_children():
            w.destroy()

        # ── Header card ───────────────────────────────────────────────────────
        hdr_card = ctk.CTkFrame(self._detail_scroll, corner_radius=10)
        hdr_card.pack(fill="x", padx=4, pady=(4, 8))

        top_row = ctk.CTkFrame(hdr_card, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=(10, 0))

        ctk.CTkLabel(
            top_row, text=t["name"],
            font=ctk.CTkFont(size=17, weight="bold"), anchor="w"
        ).pack(side="left")

        badge_txt = "★ Predefinida" if t.get("is_predefined") else "● Personalizada"
        ctk.CTkLabel(
            top_row, text=badge_txt,
            font=ctk.CTkFont(size=11), text_color="#059669"
        ).pack(side="right", padx=8)

        ctk.CTkLabel(
            hdr_card, text=f"Categoría: {t.get('category','—')}",
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w"
        ).pack(fill="x", padx=12, pady=(2, 0))

        if t.get("description"):
            ctk.CTkLabel(
                hdr_card, text=t["description"],
                font=ctk.CTkFont(size=12), wraplength=560,
                justify="left", anchor="w"
            ).pack(fill="x", padx=12, pady=(4, 0))

        created = (t.get("created_at") or "")[:10]
        uses = t.get("use_count") or 0
        ctk.CTkLabel(
            hdr_card,
            text=f"Creada: {created}  ·  Usada {uses} {'vez' if uses == 1 else 'veces'}",
            font=ctk.CTkFont(size=11), text_color="gray", anchor="w"
        ).pack(fill="x", padx=12, pady=(4, 10))

        # ── Macros bar ────────────────────────────────────────────────────────
        macro_bar = ctk.CTkFrame(
            self._detail_scroll, fg_color=("gray90", "gray20"), corner_radius=8
        )
        macro_bar.pack(fill="x", padx=4, pady=(0, 8))
        macro_bar.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        macro_defs = [
            ("Calorías",  t.get("calories"),  "kcal"),
            ("Proteínas", t.get("protein_g"), "g"),
            ("Carbohid.", t.get("carbs_g"),   "g"),
            ("Grasas",    t.get("fat_g"),     "g"),
            ("Fibra",     t.get("fiber_g"),   "g"),
        ]
        for col, (label, val, unit) in enumerate(macro_defs):
            ctk.CTkLabel(
                macro_bar, text=label, text_color="gray",
                font=ctk.CTkFont(size=10)
            ).grid(row=0, column=col, padx=10, pady=(6, 0))
            txt = f"{val:.0f} {unit}" if val else "—"
            ctk.CTkLabel(
                macro_bar, text=txt,
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=1, column=col, padx=10, pady=(0, 8))

        # ── Items by meal ─────────────────────────────────────────────────────
        if items:
            ctk.CTkLabel(
                self._detail_scroll,
                text=f"Alimentos incluidos ({len(items)} en total)",
                font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
            ).pack(fill="x", padx=4, pady=(0, 4))

            groups: dict[str, list] = {m: [] for m in MEAL_TYPES}
            for item in items:
                groups.setdefault(item["meal_type"], []).append(item)

            for meal_type in MEAL_TYPES:
                group = groups.get(meal_type, [])
                if not group:
                    continue

                sect = ctk.CTkFrame(
                    self._detail_scroll, corner_radius=6,
                    fg_color=("gray92", "gray22")
                )
                sect.pack(fill="x", padx=4, pady=2)

                # Section header with subtotal
                mt_kcal = sum(i.get("calories") or 0 for i in group)
                sh = ctk.CTkFrame(sect, fg_color="transparent")
                sh.pack(fill="x", padx=10, pady=(6, 2))
                ctk.CTkLabel(
                    sh, text=meal_type,
                    font=ctk.CTkFont(size=11, weight="bold"), anchor="w"
                ).pack(side="left")
                ctk.CTkLabel(
                    sh, text=f"{mt_kcal:.0f} kcal",
                    font=ctk.CTkFont(size=10), text_color="gray"
                ).pack(side="right")

                for item in group:
                    row_f = ctk.CTkFrame(sect, fg_color="transparent")
                    row_f.pack(fill="x", padx=10, pady=1)
                    row_f.grid_columnconfigure(0, weight=1)

                    name_txt = f"• {item['food_name']}"
                    if item.get("quantity"):
                        name_txt += f"  {item['quantity']:.0f} {item.get('unit','g')}"
                    ctk.CTkLabel(
                        row_f, text=name_txt,
                        font=ctk.CTkFont(size=11), anchor="w"
                    ).grid(row=0, column=0, sticky="w")

                    if item.get("calories"):
                        ctk.CTkLabel(
                            row_f,
                            text=f"{item['calories']:.0f} kcal  P:{item.get('protein_g',0):.1f}g  "
                                 f"HC:{item.get('carbs_g',0):.1f}g  G:{item.get('fat_g',0):.1f}g",
                            font=ctk.CTkFont(size=10), text_color="gray"
                        ).grid(row=0, column=1, padx=8)

                ctk.CTkFrame(sect, height=4, fg_color="transparent").pack()

        # ── Usage history ─────────────────────────────────────────────────────
        if usage:
            ctk.CTkLabel(
                self._detail_scroll,
                text=f"Historial de uso ({len(usage)} {'aplicación' if len(usage) == 1 else 'aplicaciones'})",
                font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
            ).pack(fill="x", padx=4, pady=(8, 4))

            for u in usage[:10]:
                row_f = ctk.CTkFrame(
                    self._detail_scroll,
                    fg_color=("gray92", "gray22"), corner_radius=6
                )
                row_f.pack(fill="x", padx=4, pady=1)
                row_f.grid_columnconfigure(0, weight=1)
                ctk.CTkLabel(
                    row_f, text=u["patient_name"],
                    font=ctk.CTkFont(size=11), anchor="w"
                ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(
                    row_f, text=(u.get("used_at") or "")[:10],
                    font=ctk.CTkFont(size=10), text_color="gray"
                ).grid(row=0, column=1, padx=10)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _apply_to_patient(self):
        if not self._selected_tid:
            return
        pid = self.app.get_patient_id()
        if not pid:
            messagebox.showwarning(
                "Sin paciente",
                "Selecciona un paciente primero desde la lista de pacientes."
            )
            return

        t = db.get_template(self._selected_tid)
        patient = db.get_patient(pid)
        if not messagebox.askyesno(
            "Aplicar plantilla",
            f"¿Aplicar la plantilla\n\n"
            f"  «{t['name']}»\n\n"
            f"al paciente {patient['name']}?\n\n"
            "Se creará un nuevo plan alimenticio con todos\n"
            "los alimentos de esta plantilla."
        ):
            return

        plan_data = {
            "patient_id": pid,
            "name": t["name"],
            "date": date.today().isoformat(),
            "goal": t.get("goal") or "Otro",
            "calories": t.get("calories"),
            "protein_g": t.get("protein_g"),
            "carbs_g": t.get("carbs_g"),
            "fat_g": t.get("fat_g"),
            "notes": t.get("notes"),
            "template_id": self._selected_tid,
        }
        plan_id = db.insert_meal_plan(plan_data)
        db.apply_template_to_plan(self._selected_tid, plan_id)
        db.record_template_usage(self._selected_tid, pid, plan_id)

        # Refresh detail to update use_count
        self._select_template(self._selected_tid)

        # Navigate to meal plans with this plan pre-selected
        self.app._pending_plan_id = plan_id
        self.app._show_frame("meal_plans")
        self.app.show_toast(
            f"Plantilla aplicada a {patient['name']} correctamente."
        )

    def _edit_template(self):
        if not self._selected_tid:
            return
        t = db.get_template(self._selected_tid)
        TemplateFormDialog(
            self, mode="edit", template=t,
            on_save=lambda tid: self._select_template(tid)
        )

    def _duplicate_template(self):
        if not self._selected_tid:
            return
        new_tid = db.duplicate_template(self._selected_tid)
        self._load_templates()
        self._select_template(new_tid)
        self.app.show_toast("Plantilla duplicada correctamente.")

    def _delete_template(self):
        if not self._selected_tid:
            return
        t = db.get_template(self._selected_tid)
        if t.get("is_predefined"):
            messagebox.showwarning(
                "No permitido",
                "Las plantillas predefinidas no se pueden eliminar.\n"
                "Puedes duplicarla y luego eliminar la copia."
            )
            return
        if messagebox.askyesno(
            "Eliminar plantilla",
            f"¿Eliminar «{t['name']}»?\nEsta acción no se puede deshacer."
        ):
            db.delete_template(self._selected_tid)
            self._selected_tid = None
            self._action_bar.grid_remove()
            self._show_empty_detail()
            self._load_templates()

    def _new_template(self):
        TemplateFormDialog(
            self, mode="create", template=None,
            on_save=lambda tid: (self._load_templates(), self._select_template(tid))
        )


# ── Dialogs ───────────────────────────────────────────────────────────────────

class TemplateFormDialog(ctk.CTkToplevel):
    """Create or edit a template's metadata (name, category, description)."""

    def __init__(self, parent, mode: str,
                 template: Optional[dict], on_save: Callable):
        super().__init__(parent)
        self._mode = mode
        self._template = template
        self._on_save = on_save
        self.title("Nueva plantilla" if mode == "create" else "Editar plantilla")
        self.geometry("500x420")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self.after(80, self.lift)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Nueva plantilla" if self._mode == "create" else "Editar plantilla",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 12), sticky="w")

        ctk.CTkLabel(self, text="Nombre *", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=1, column=0, padx=20, sticky="w")
        self._name_var = ctk.StringVar(
            value=self._template.get("name", "") if self._template else ""
        )
        ctk.CTkEntry(self, textvariable=self._name_var, height=36
                     ).grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(self, text="Categoría", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=3, column=0, padx=20, sticky="w")
        self._cat_var = ctk.StringVar(
            value=self._template.get("category", "Otra") if self._template else "Otra"
        )
        ctk.CTkOptionMenu(
            self, values=CATEGORIES[1:], variable=self._cat_var, height=36
        ).grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(self, text="Descripción (opcional)", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=5, column=0, padx=20, sticky="w")
        self._desc_box = ctk.CTkTextbox(self, height=110)
        self._desc_box.grid(row=6, column=0, padx=20, pady=(0, 16), sticky="ew")
        if self._template and self._template.get("description"):
            self._desc_box.insert("1.0", self._template["description"])

        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")
        btn_f.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_f, text="Cancelar", height=36,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self.destroy
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            btn_f, text="Guardar", height=36,
            command=self._save
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _save(self):
        name = self._name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre es obligatorio.", parent=self)
            return
        cat = self._cat_var.get()
        desc = self._desc_box.get("1.0", "end").strip() or None

        if self._mode == "create":
            tid = db.insert_template({"name": name, "category": cat, "description": desc})
        else:
            t = self._template
            db.update_template(t["id"], {
                "name": name, "category": cat, "description": desc,
                "calories": t.get("calories"), "protein_g": t.get("protein_g"),
                "carbs_g": t.get("carbs_g"), "fat_g": t.get("fat_g"),
                "fiber_g": t.get("fiber_g"), "goal": t.get("goal"),
                "notes": t.get("notes"),
            })
            tid = t["id"]

        self.destroy()
        self._on_save(tid)


class SaveAsTemplateDialog(ctk.CTkToplevel):
    """Save an existing meal plan as a reusable template."""

    def __init__(self, parent, plan_id: int, plan_name: str, on_save: Callable):
        super().__init__(parent)
        self._plan_id = plan_id
        self._on_save = on_save
        self.title("Guardar como plantilla")
        self.geometry("500x400")
        self.resizable(False, False)
        self.grab_set()
        self._build(plan_name)
        self.after(80, self.lift)

    def _build(self, plan_name: str):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Guardar plan como plantilla",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 2), sticky="w")
        ctk.CTkLabel(
            self,
            text="La plantilla quedará disponible para aplicar a cualquier paciente.",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 14), sticky="w")

        ctk.CTkLabel(self, text="Nombre de la plantilla *", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=2, column=0, padx=20, sticky="w")
        self._name_var = ctk.StringVar(value=plan_name)
        ctk.CTkEntry(self, textvariable=self._name_var, height=36
                     ).grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(self, text="Categoría", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=4, column=0, padx=20, sticky="w")
        self._cat_var = ctk.StringVar(value="Otra")
        ctk.CTkOptionMenu(
            self, values=CATEGORIES[1:], variable=self._cat_var, height=36
        ).grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(self, text="Descripción (opcional)", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=6, column=0, padx=20, sticky="w")
        self._desc_box = ctk.CTkTextbox(self, height=90)
        self._desc_box.grid(row=7, column=0, padx=20, pady=(0, 16), sticky="ew")

        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="ew")
        btn_f.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_f, text="Cancelar", height=36,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self.destroy
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            btn_f, text="Guardar como plantilla", height=36,
            command=self._save
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _save(self):
        name = self._name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre es obligatorio.", parent=self)
            return
        tid = db.save_plan_as_template(
            self._plan_id, name,
            self._cat_var.get(),
            self._desc_box.get("1.0", "end").strip() or None
        )
        self.destroy()
        self._on_save(tid)


class TemplatePickerDialog(ctk.CTkToplevel):
    """Pick a template when creating a new meal plan."""

    def __init__(self, parent, on_pick: Callable):
        super().__init__(parent)
        self._on_pick = on_pick
        self._selected_tid: Optional[int] = None
        self.title("Seleccionar plantilla")
        self.geometry("780x580")
        self.resizable(True, True)
        self.grab_set()
        self._build()
        self.after(80, self.lift)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="Selecciona una plantilla",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(16, 0), sticky="w")

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        main.grid_columnconfigure(0, weight=2)
        main.grid_columnconfigure(1, weight=3)
        main.grid_rowconfigure(0, weight=1)

        # Left: list
        left = ctk.CTkFrame(main)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load_list())
        ctk.CTkEntry(
            left, textvariable=self._search_var,
            placeholder_text="Buscar…", height=32
        ).grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self._list_scroll = ctk.CTkScrollableFrame(left)
        self._list_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._list_scroll.grid_columnconfigure(0, weight=1)

        # Right: preview
        right = ctk.CTkFrame(main)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        self._preview_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self._preview_scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._preview_scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._preview_scroll,
            text="Selecciona una plantilla\npara ver su contenido.",
            text_color="gray", font=ctk.CTkFont(size=12), justify="center"
        ).pack(pady=40)

        # Bottom buttons
        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="ew")
        btn_f.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_f, text="Cancelar", height=36, width=100,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self.destroy
        ).grid(row=0, column=0, padx=(0, 8))

        self._use_btn = ctk.CTkButton(
            btn_f, text="Usar esta plantilla", height=36,
            state="disabled", command=self._use
        )
        self._use_btn.grid(row=0, column=2)

        self._load_list()

    def _load_list(self):
        for w in self._list_scroll.winfo_children():
            w.destroy()

        query = self._search_var.get().strip().lower()
        templates = db.get_all_templates()
        filtered = [t for t in templates
                    if not query or query in t["name"].lower()]

        for t in filtered:
            is_sel = (t["id"] == self._selected_tid)
            fg = ("#d1fae5", "#14532d") if is_sel else ("gray92", "gray18")
            badge = "★" if t.get("is_predefined") else "▸"
            cal = f"  ·  {t['calories']:.0f} kcal" if t.get("calories") else ""
            ctk.CTkButton(
                self._list_scroll,
                text=f"{badge}  {t['name']}\n{t.get('category','')}{cal}",
                anchor="w", height=52,
                fg_color=fg, hover_color=("#bbf7d0", "#166534"),
                text_color=("gray10", "gray90"),
                font=ctk.CTkFont(size=11),
                command=lambda tid=t["id"]: self._pick(tid)
            ).pack(fill="x", pady=2, padx=4)

    def _pick(self, tid: int):
        self._selected_tid = tid
        self._use_btn.configure(state="normal")
        self._load_list()
        self._show_preview(tid)

    def _show_preview(self, tid: int):
        for w in self._preview_scroll.winfo_children():
            w.destroy()

        t = db.get_template(tid)
        items = db.get_template_items(tid)

        ctk.CTkLabel(
            self._preview_scroll, text=t["name"],
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x", padx=4, pady=(4, 0))
        ctk.CTkLabel(
            self._preview_scroll, text=t.get("category", "—"),
            font=ctk.CTkFont(size=11), text_color="#059669", anchor="w"
        ).pack(fill="x", padx=4)

        if t.get("description"):
            ctk.CTkLabel(
                self._preview_scroll, text=t["description"],
                font=ctk.CTkFont(size=11), text_color="gray",
                wraplength=360, justify="left", anchor="w"
            ).pack(fill="x", padx=4, pady=(2, 4))

        if t.get("calories"):
            ctk.CTkLabel(
                self._preview_scroll,
                text=(f"{t['calories']:.0f} kcal  ·  "
                      f"P:{t.get('protein_g',0):.0f}g  "
                      f"HC:{t.get('carbs_g',0):.0f}g  "
                      f"G:{t.get('fat_g',0):.0f}g"),
                font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
            ).pack(fill="x", padx=4, pady=(0, 8))

        if items:
            ctk.CTkLabel(
                self._preview_scroll,
                text=f"{len(items)} alimentos incluidos:",
                font=ctk.CTkFont(size=11), text_color="gray", anchor="w"
            ).pack(fill="x", padx=4)

            groups: dict[str, list] = {m: [] for m in MEAL_TYPES}
            for item in items:
                groups.setdefault(item["meal_type"], []).append(item)

            for mt in MEAL_TYPES:
                group = groups.get(mt, [])
                if not group:
                    continue
                ctk.CTkLabel(
                    self._preview_scroll,
                    text=f"  ▸ {mt} ({len(group)} alimentos)",
                    font=ctk.CTkFont(size=11, weight="bold"), anchor="w"
                ).pack(fill="x", padx=4, pady=(4, 0))
                for item in group:
                    qty = f" {item['quantity']:.0f}{item.get('unit','g')}" \
                          if item.get("quantity") else ""
                    ctk.CTkLabel(
                        self._preview_scroll,
                        text=f"      • {item['food_name']}{qty}",
                        font=ctk.CTkFont(size=10), text_color="gray", anchor="w"
                    ).pack(fill="x", padx=4)

    def _use(self):
        if self._selected_tid:
            tid = self._selected_tid
            self.destroy()
            self._on_pick(tid)


class NewPlanChoiceDialog(ctk.CTkToplevel):
    """Ask user whether to create a plan from scratch or from a template."""

    def __init__(self, parent, on_scratch: Callable, on_template: Callable):
        super().__init__(parent)
        self._on_scratch = on_scratch
        self._on_template = on_template
        self.title("Nuevo Plan Alimenticio")
        self.geometry("420x240")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self.after(80, self.lift)

    def _build(self):
        ctk.CTkLabel(
            self, text="¿Cómo deseas crear el plan?",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=24, pady=(22, 14))

        ctk.CTkButton(
            self, text="📝   Crear desde cero",
            height=58, corner_radius=10,
            font=ctk.CTkFont(size=14),
            command=self._pick_scratch
        ).pack(fill="x", padx=24, pady=(0, 8))

        ctk.CTkButton(
            self, text="📋   Usar plantilla existente",
            height=58, corner_radius=10,
            font=ctk.CTkFont(size=14),
            fg_color="transparent", border_width=2,
            text_color=("gray10", "gray90"),
            hover_color=("gray90", "gray25"),
            command=self._pick_template
        ).pack(fill="x", padx=24, pady=(0, 8))

        ctk.CTkButton(
            self, text="Cancelar", height=30,
            fg_color="transparent", text_color="gray",
            hover_color=("gray90", "gray25"),
            command=self.destroy
        ).pack()

    def _pick_scratch(self):
        self.destroy()
        self._on_scratch()

    def _pick_template(self):
        self.destroy()
        self._on_template()
