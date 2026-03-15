"""RecetasFrame — Gestión de recetas personalizadas con ingredientes,
aporte nutricional y equivalencias por grupo alimentario."""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional

import database.db_manager as db
from modules.pautas_alimentacion.grupos_alimentos import GRUPOS_MACROS, NOMBRES_GRUPOS

# ── Paleta (coherente con main_window) ───────────────────────────────────────
_C_PRIMARY      = "#4b7c60"
_C_PRIMARY_DARK = "#3d6b50"
_C_PRIMARY_DEEP = "#2f5a40"
_C_TERRACOTTA   = "#c06c52"
_C_SAGE         = "#8da399"

# Categorías disponibles para recetas
CATEGORIAS = [
    "General", "Desayuno", "Almuerzo", "Cena", "Colación",
    "Postre", "Snack", "Bebida", "Vegetariano", "Vegano",
]


class RecetasFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app
        self._selected_recipe_id: Optional[int] = None
        self._selected_food: Optional[dict] = None
        self._ing_suppress = False
        self._build_ui()

    # ── Layout principal ──────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Recetas",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Crea recetas con ingredientes, aporte nutricional y equivalencias por porción",
            font=ctk.CTkFont(size=13), text_color="gray"
        ).grid(row=0, column=1, padx=16, sticky="w")

        ctk.CTkFrame(self, height=1, fg_color=("gray85", "gray30")
                     ).grid(row=1, column=0, sticky="ew", padx=24, pady=(12, 0))

        # Main split
        panes = ctk.CTkFrame(self, fg_color="transparent")
        panes.grid(row=2, column=0, sticky="nsew", padx=24, pady=(8, 20))
        panes.grid_columnconfigure(1, weight=1)
        panes.grid_rowconfigure(0, weight=1)

        self._build_left_panel(panes)
        self._build_right_panel(panes)

    # ── Panel izquierdo: lista de recetas ─────────────────────────────────────

    def _build_left_panel(self, parent):
        left = ctk.CTkFrame(parent, width=260)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)
        left.grid_propagate(False)

        ctk.CTkButton(
            left, text="+ Nueva Receta", height=42,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._new_recipe
        ).grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load_recipe_list())
        ctk.CTkEntry(
            left, textvariable=self._search_var,
            placeholder_text="Buscar receta…", height=32
        ).grid(row=1, column=0, padx=8, pady=(0, 4), sticky="ew")

        self._recipe_scroll = ctk.CTkScrollableFrame(left, label_text="Mis recetas")
        self._recipe_scroll.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0, 8))
        self._recipe_scroll.grid_columnconfigure(0, weight=1)

    # ── Panel derecho: detalle / editor ───────────────────────────────────────

    def _build_right_panel(self, parent):
        self._right = ctk.CTkFrame(parent)
        self._right.grid(row=0, column=1, sticky="nsew")
        self._right.grid_columnconfigure(0, weight=1)
        self._right.grid_rowconfigure(0, weight=1)

        # Placeholder
        self._placeholder = ctk.CTkFrame(self._right, fg_color="transparent")
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self._placeholder, text="👨‍🍳",
                     font=ctk.CTkFont(size=52)).pack(pady=(0, 8))
        ctk.CTkLabel(self._placeholder, text="Sin receta seleccionada",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 6))
        ctk.CTkLabel(
            self._placeholder,
            text="Selecciona una receta de la lista\no crea una nueva con el botón '+ Nueva Receta'.",
            font=ctk.CTkFont(size=13), text_color="gray", justify="center"
        ).pack()

        # Tabs (ocultos hasta que se seleccione/cree una receta)
        self._tabs = ctk.CTkTabview(self._right, anchor="nw")
        self._tab_info  = self._tabs.add("  Información  ")
        self._tab_ingr  = self._tabs.add("  Ingredientes  ")
        self._tab_nutr  = self._tabs.add("  Aporte Nutricional  ")
        self._tab_equiv = self._tabs.add("  Equivalencias  ")
        self._tabs.set("  Información  ")

        self._build_info_tab()
        self._build_ingredients_tab()
        self._build_nutrition_tab()
        self._build_equivalencias_tab()

    # ── Tab 1: Información ────────────────────────────────────────────────────

    def _build_info_tab(self):
        tab = self._tab_info
        tab.grid_columnconfigure((0, 1), weight=1)

        # Nombre
        ctk.CTkLabel(tab, text="Nombre de la receta", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, columnspan=2, padx=8, pady=(12, 0), sticky="w")
        self._nombre_var = ctk.StringVar()
        ctk.CTkEntry(tab, textvariable=self._nombre_var, height=36,
                     placeholder_text="Ej: Queque de zanahoria"
                     ).grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")

        # Categoría + Porciones
        ctk.CTkLabel(tab, text="Categoría", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=2, column=0, padx=8, pady=(4, 0), sticky="w")
        self._cat_var = ctk.StringVar(value=CATEGORIAS[0])
        ctk.CTkOptionMenu(tab, values=CATEGORIAS, variable=self._cat_var, height=34
                          ).grid(row=3, column=0, padx=8, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(tab, text="Porciones que rinde", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=2, column=1, padx=8, pady=(4, 0), sticky="w")
        self._porciones_var = ctk.StringVar(value="1")
        ctk.CTkEntry(tab, textvariable=self._porciones_var, height=34,
                     placeholder_text="Ej: 8"
                     ).grid(row=3, column=1, padx=8, pady=(0, 8), sticky="ew")

        # Descripción
        ctk.CTkLabel(tab, text="Descripción corta", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=4, column=0, columnspan=2, padx=8, pady=(4, 0), sticky="w")
        self._desc_text = ctk.CTkTextbox(tab, height=60)
        self._desc_text.grid(row=5, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")

        # Preparación / Notas
        ctk.CTkLabel(tab, text="Notas / Preparación", text_color="gray",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=6, column=0, columnspan=2, padx=8, pady=(4, 0), sticky="w")
        self._notas_text = ctk.CTkTextbox(tab, height=120)
        self._notas_text.grid(row=7, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")

        ctk.CTkFrame(tab, height=1, fg_color=("gray85", "gray30")
                     ).grid(row=8, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        ctk.CTkButton(
            tab, text="Guardar receta", height=36,
            command=self._save_recipe_info
        ).grid(row=9, column=0, padx=8, pady=8, sticky="ew")

        self._delete_btn = ctk.CTkButton(
            tab, text="Eliminar receta", height=36,
            fg_color=_C_TERRACOTTA, hover_color="#a85a43",
            command=self._delete_recipe
        )
        self._delete_btn.grid(row=9, column=1, padx=8, pady=8, sticky="ew")

    # ── Tab 2: Ingredientes ───────────────────────────────────────────────────

    def _build_ingredients_tab(self):
        tab = self._tab_ingr
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Formulario para agregar
        add_frame = ctk.CTkFrame(tab, fg_color=("gray95", "gray17"), corner_radius=8)
        add_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=(8, 4))
        add_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(add_frame, text="Agregar ingrediente",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray"
                     ).grid(row=0, column=0, columnspan=4, padx=10, pady=(8, 2), sticky="w")

        for col, txt in enumerate(["Buscar alimento", "Gramos", "Medida casera", ""]):
            if txt:
                ctk.CTkLabel(add_frame, text=txt, text_color="gray",
                             font=ctk.CTkFont(size=11)
                             ).grid(row=1, column=col,
                                    padx=(10 if col == 0 else 4, 4),
                                    pady=(4, 0), sticky="w")

        # Búsqueda de alimento
        self._ing_food_var = ctk.StringVar()
        self._ing_food_var.trace_add("write", self._on_food_search)
        ctk.CTkEntry(
            add_frame, textvariable=self._ing_food_var,
            placeholder_text="Ej: harina, azúcar, pollo…", height=32
        ).grid(row=2, column=0, padx=(10, 4), pady=(0, 4), sticky="ew")

        self._ing_gramos_var = ctk.StringVar(value="100")
        self._ing_gramos_var.trace_add("write", lambda *_: self._update_macro_preview())
        ctk.CTkEntry(add_frame, textvariable=self._ing_gramos_var,
                     width=80, height=32
                     ).grid(row=2, column=1, padx=4, pady=(0, 4))

        self._ing_medida_var = ctk.StringVar()
        ctk.CTkEntry(add_frame, textvariable=self._ing_medida_var,
                     placeholder_text="Ej: 2 tazas", width=130, height=32
                     ).grid(row=2, column=2, padx=4, pady=(0, 4))

        ctk.CTkButton(
            add_frame, text="Agregar", height=32, width=90,
            command=self._add_ingredient
        ).grid(row=2, column=3, padx=(4, 10), pady=(0, 4))

        # Dropdown de resultados de búsqueda
        self._ing_search_results = ctk.CTkScrollableFrame(
            add_frame, height=120, fg_color=("white", "gray15"))
        self._ing_search_results.grid(row=3, column=0, columnspan=4,
                                      padx=10, pady=(0, 4), sticky="ew")
        self._ing_search_results.grid_columnconfigure(0, weight=1)
        self._ing_search_results.grid_remove()

        # Preview de macros del ingrediente
        self._macro_preview = ctk.CTkLabel(
            add_frame, text="", text_color="gray", font=ctk.CTkFont(size=11))
        self._macro_preview.grid(row=4, column=0, columnspan=4,
                                 padx=10, pady=(0, 8), sticky="w")

        # Lista de ingredientes
        self._ing_scroll = ctk.CTkScrollableFrame(tab)
        self._ing_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(4, 4))
        self._ing_scroll.grid_columnconfigure(0, weight=1)

        # Barra de totales
        self._ing_totals_bar = ctk.CTkFrame(tab, height=36, corner_radius=6,
                                            fg_color=("gray90", "gray20"))
        self._ing_totals_bar.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 4))
        self._ing_totals_lbl = ctk.CTkLabel(
            self._ing_totals_bar, text="Total receta: —",
            font=ctk.CTkFont(size=11), text_color="gray")
        self._ing_totals_lbl.pack(side="left", padx=12)

    # ── Tab 3: Aporte Nutricional ─────────────────────────────────────────────

    def _build_nutrition_tab(self):
        tab = self._tab_nutr
        tab.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            tab, text="Aporte nutricional por porción",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(16, 2), sticky="w")
        ctk.CTkLabel(
            tab,
            text="Se calcula automáticamente según los ingredientes ingresados.",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="w")

        self._nutr_labels: dict[str, ctk.CTkLabel] = {}
        cards_data = [
            ("kcal_por", "Calorías",      "kcal", "#fef3c7", "#78350f"),
            ("prot_por", "Proteínas",     "g",    "#d1fae5", "#065f46"),
            ("cho_por",  "Carbohidratos", "g",    "#dbeafe", "#1e3a5f"),
            ("fat_por",  "Grasas",        "g",    "#fce7f3", "#831843"),
            ("fib_por",  "Fibra",         "g",    "#ede9fe", "#4c1d95"),
        ]
        for idx, (key, name, unit, bg_l, fg_l) in enumerate(cards_data):
            card_row = (idx // 2) + 2
            card_col = idx % 2
            card = ctk.CTkFrame(tab, corner_radius=10, fg_color=(bg_l, "#1e293b"))
            card.grid(row=card_row, column=card_col, padx=8, pady=6, sticky="ew")
            ctk.CTkLabel(card, text=name,
                         font=ctk.CTkFont(size=11), text_color=(fg_l, "gray70")
                         ).pack(padx=14, pady=(10, 0), anchor="w")
            lbl = ctk.CTkLabel(card, text="—",
                               font=ctk.CTkFont(size=24, weight="bold"),
                               text_color=(fg_l, "white"))
            lbl.pack(padx=14, pady=(0, 2), anchor="w")
            ctk.CTkLabel(card, text=unit,
                         font=ctk.CTkFont(size=10), text_color=(fg_l, "gray60")
                         ).pack(padx=14, pady=(0, 10), anchor="w")
            self._nutr_labels[key] = lbl

        ctk.CTkFrame(tab, height=1, fg_color=("gray85", "gray30")
                     ).grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=12)
        ctk.CTkLabel(
            tab, text="Total de la receta completa",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="gray"
        ).grid(row=6, column=0, columnspan=2, padx=12, pady=(0, 4), sticky="w")
        self._nutr_total_lbl = ctk.CTkLabel(
            tab, text="—", font=ctk.CTkFont(size=12), text_color="gray")
        self._nutr_total_lbl.grid(row=7, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="w")

    # ── Tab 4: Equivalencias ──────────────────────────────────────────────────

    def _build_equivalencias_tab(self):
        tab = self._tab_equiv
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Bloque informativo
        info = ctk.CTkFrame(tab, fg_color=("gray95", "gray17"), corner_radius=8)
        info.grid(row=0, column=0, sticky="ew", padx=4, pady=(8, 4))
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info,
            text="Indica cuántas porciones de cada grupo alimentario equivale 1 porción de la receta.\n"
                 "Usa los macros de referencia por grupo para guiarte.",
            font=ctk.CTkFont(size=12), wraplength=600, justify="left"
        ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self._equiv_ref_lbl = ctk.CTkLabel(
            info, text="Receta: — kcal | — g prot | — g CHO | — g grasas  (por porción)",
            font=ctk.CTkFont(size=11), text_color="gray")
        self._equiv_ref_lbl.grid(row=1, column=0, padx=12, pady=(0, 2), sticky="w")

        self._equiv_total_lbl = ctk.CTkLabel(
            info, text="Desde equivalencias: — kcal | — g prot | — g CHO | — g grasas",
            font=ctk.CTkFont(size=11), text_color=_C_PRIMARY)
        self._equiv_total_lbl.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="w")

        # Tabla de grupos
        self._equiv_scroll = ctk.CTkScrollableFrame(tab)
        self._equiv_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._equiv_scroll.grid_columnconfigure(0, weight=1)

        # Cabecera de tabla
        hdr = ctk.CTkFrame(self._equiv_scroll, fg_color=("gray82", "gray28"),
                           corner_radius=6)
        hdr.grid(row=0, column=0, sticky="ew", padx=2, pady=(0, 2))
        for col, (txt, w) in enumerate([
            ("Grupo alimentario", 190), ("Porciones", 80),
            ("Ref. kcal", 72), ("Ref. prot", 72),
            ("Ref. CHO", 72), ("Ref. grasas", 80),
        ]):
            ctk.CTkLabel(hdr, text=txt, font=ctk.CTkFont(size=11, weight="bold"),
                         width=w, anchor="w"
                         ).grid(row=0, column=col, padx=6, pady=5, sticky="w")

        # Filas por cada grupo
        self._equiv_vars: dict[str, ctk.StringVar] = {}
        for i, (grupo, nombre) in enumerate(NOMBRES_GRUPOS.items()):
            macros = GRUPOS_MACROS[grupo]
            row_idx = i + 1
            bg = ("gray95", "gray20") if i % 2 == 0 else ("white", "gray17")
            rf = ctk.CTkFrame(self._equiv_scroll, fg_color=bg, corner_radius=4)
            rf.grid(row=row_idx, column=0, sticky="ew", padx=2, pady=1)

            ctk.CTkLabel(rf, text=nombre, font=ctk.CTkFont(size=12),
                         anchor="w", width=190
                         ).grid(row=0, column=0, padx=8, pady=4, sticky="w")

            var = ctk.StringVar(value="0")
            var.trace_add("write", lambda *_, g=grupo: self._update_equiv_totals())
            ctk.CTkEntry(rf, textvariable=var, width=72, height=28
                         ).grid(row=0, column=1, padx=4, pady=4)
            self._equiv_vars[grupo] = var

            for col_idx, (val, w) in enumerate([
                (macros["kcal"], 72), (macros["prot"], 72),
                (macros["cho"], 72),  (macros["lip"], 80),
            ]):
                ctk.CTkLabel(rf, text=str(val), font=ctk.CTkFont(size=11),
                             text_color="gray", width=w, anchor="w"
                             ).grid(row=0, column=col_idx + 2, padx=4, pady=4, sticky="w")

        ctk.CTkButton(
            tab, text="Guardar equivalencias", height=36,
            command=self._save_equivalencias
        ).grid(row=2, column=0, padx=4, pady=8, sticky="ew")

    # ── on_show ───────────────────────────────────────────────────────────────

    def on_show(self):
        self._load_recipe_list()

    # ── Lista de recetas ──────────────────────────────────────────────────────

    def _load_recipe_list(self):
        for w in self._recipe_scroll.winfo_children():
            w.destroy()

        query = self._search_var.get().strip()
        recipes = db.search_recetas(query) if query else db.get_all_recetas()

        if not recipes:
            ctk.CTkLabel(
                self._recipe_scroll,
                text="Sin recetas guardadas.\nUsa '+ Nueva Receta' para crear la primera.",
                text_color="gray", font=ctk.CTkFont(size=12), justify="center"
            ).grid(row=0, column=0, pady=20)
            return

        for i, r in enumerate(recipes):
            is_sel = r["id"] == self._selected_recipe_id
            n = r["porciones_rinde"]
            btn = ctk.CTkButton(
                self._recipe_scroll,
                text=f"  {r['nombre']}\n  {r['categoria']} · {n} porción{'es' if n != 1 else ''}",
                anchor="w", height=52, corner_radius=6,
                font=ctk.CTkFont(size=12),
                fg_color=("#d1fae5" if is_sel else "transparent"),
                text_color=("#065f46" if is_sel else ("gray10", "gray90")),
                hover_color=("#d1fae5", "#1e4a35"),
                command=lambda rid=r["id"]: self._select_recipe(rid)
            )
            btn.grid(row=i, column=0, padx=4, pady=2, sticky="ew")

    def _select_recipe(self, rid: int):
        self._selected_recipe_id = rid
        self._load_recipe_list()
        self._show_tabs()
        self._load_recipe_info(rid)
        self._load_ingredients(rid)
        self._refresh_nutrition_tab()
        self._load_equivalencias(rid)

    def _show_tabs(self):
        self._placeholder.place_forget()
        self._tabs.grid(row=0, column=0, sticky="nsew")
        self._right.grid_rowconfigure(0, weight=1)
        self._right.grid_columnconfigure(0, weight=1)

    def _hide_tabs(self):
        self._tabs.grid_forget()
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

    # ── Nueva receta ──────────────────────────────────────────────────────────

    def _new_recipe(self):
        self._selected_recipe_id = None
        self._show_tabs()
        self._tabs.set("  Información  ")

        self._nombre_var.set("")
        self._cat_var.set(CATEGORIAS[0])
        self._porciones_var.set("1")
        self._desc_text.delete("1.0", "end")
        self._notas_text.delete("1.0", "end")

        for w in self._ing_scroll.winfo_children():
            w.destroy()
        self._ing_totals_lbl.configure(text="Total receta: —")

        for lbl in self._nutr_labels.values():
            lbl.configure(text="—")
        self._nutr_total_lbl.configure(text="—")

        for var in self._equiv_vars.values():
            var.set("0")
        self._equiv_ref_lbl.configure(
            text="Receta: — kcal | — g prot | — g CHO | — g grasas  (por porción)")
        self._update_equiv_totals()
        self._load_recipe_list()

    def _load_recipe_info(self, rid: int):
        r = db.get_receta(rid)
        if not r:
            return
        self._nombre_var.set(r.get("nombre") or "")
        cat = r.get("categoria") or CATEGORIAS[0]
        self._cat_var.set(cat if cat in CATEGORIAS else CATEGORIAS[0])
        self._porciones_var.set(str(r.get("porciones_rinde") or 1))
        self._desc_text.delete("1.0", "end")
        if r.get("descripcion"):
            self._desc_text.insert("1.0", r["descripcion"])
        self._notas_text.delete("1.0", "end")
        if r.get("notas"):
            self._notas_text.insert("1.0", r["notas"])

    # ── CRUD receta ───────────────────────────────────────────────────────────

    def _save_recipe_info(self):
        nombre = self._nombre_var.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "El nombre de la receta es obligatorio.")
            return
        try:
            porciones = int(self._porciones_var.get() or 1)
            porciones = max(1, porciones)
        except ValueError:
            porciones = 1

        data = {
            "nombre": nombre,
            "descripcion": self._desc_text.get("1.0", "end").strip() or None,
            "categoria": self._cat_var.get(),
            "porciones_rinde": porciones,
            "notas": self._notas_text.get("1.0", "end").strip() or None,
        }

        if self._selected_recipe_id:
            db.update_receta(self._selected_recipe_id, data)
        else:
            rid = db.insert_receta(data)
            self._selected_recipe_id = rid

        self._load_recipe_list()
        self.app.show_toast("✓ Receta guardada")

    def _delete_recipe(self):
        if not self._selected_recipe_id:
            return
        r = db.get_receta(self._selected_recipe_id)
        nombre = r["nombre"] if r else "esta receta"
        if not messagebox.askyesno(
            "Eliminar receta",
            f"¿Eliminar '{nombre}'?\n"
            "Se eliminarán todos sus ingredientes y equivalencias."
        ):
            return
        db.delete_receta(self._selected_recipe_id)
        self._selected_recipe_id = None
        self._hide_tabs()
        self._load_recipe_list()
        self.app.show_toast("Receta eliminada", color=_C_TERRACOTTA)

    # ── Búsqueda de alimentos ─────────────────────────────────────────────────

    def _on_food_search(self, *args):
        if self._ing_suppress:
            return
        query = self._ing_food_var.get().strip()
        for w in self._ing_search_results.winfo_children():
            w.destroy()
        if len(query) < 2:
            self._ing_search_results.grid_remove()
            self._selected_food = None
            return
        results = db.search_foods(query, limit=12)
        if not results:
            self._ing_search_results.grid_remove()
            return
        self._ing_search_results.grid()
        for food in results:
            ctk.CTkButton(
                self._ing_search_results,
                text=food["nombre_es"],
                anchor="w", height=28, corner_radius=4,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda f=food: self._select_food(f)
            ).grid(sticky="ew", pady=1)

    def _select_food(self, food: dict):
        self._selected_food = food
        self._ing_suppress = True
        self._ing_food_var.set(food["nombre_es"])
        self._ing_suppress = False
        self._ing_search_results.grid_remove()
        for w in self._ing_search_results.winfo_children():
            w.destroy()
        self._update_macro_preview()

    def _update_macro_preview(self):
        if not self._selected_food:
            self._macro_preview.configure(text="")
            return
        try:
            gramos = float(self._ing_gramos_var.get() or 100)
        except ValueError:
            gramos = 100
        f = self._selected_food
        factor = gramos / 100
        kcal = (f.get("calorias") or 0) * factor
        prot = (f.get("proteinas_g") or 0) * factor
        cho  = (f.get("carbohidratos_g") or 0) * factor
        fat  = (f.get("grasas_g") or 0) * factor
        self._macro_preview.configure(
            text=f"{gramos:.0f}g → {kcal:.0f} kcal | {prot:.1f}g prot | {cho:.1f}g CHO | {fat:.1f}g grasas"
        )

    # ── Ingredientes ──────────────────────────────────────────────────────────

    def _add_ingredient(self):
        if not self._selected_recipe_id:
            messagebox.showwarning(
                "Atención",
                "Primero guarda la información básica de la receta\n"
                "(Tab 'Información' → botón 'Guardar receta')."
            )
            return
        if not self._selected_food:
            messagebox.showwarning(
                "Atención",
                "Selecciona un alimento de los resultados de búsqueda."
            )
            return
        try:
            gramos = float(self._ing_gramos_var.get() or 100)
        except ValueError:
            gramos = 100

        f = self._selected_food
        factor = gramos / 100
        data = {
            "receta_id":       self._selected_recipe_id,
            "alimento_id":     f.get("id"),
            "nombre_alimento": f["nombre_es"],
            "gramos":          gramos,
            "medida_casera":   self._ing_medida_var.get().strip() or None,
            "calorias":        round((f.get("calorias") or 0) * factor, 2),
            "proteinas_g":     round((f.get("proteinas_g") or 0) * factor, 2),
            "carbohidratos_g": round((f.get("carbohidratos_g") or 0) * factor, 2),
            "grasas_g":        round((f.get("grasas_g") or 0) * factor, 2),
            "fibra_g":         round((f.get("fibra_g") or 0) * factor, 2),
        }
        db.insert_receta_ingrediente(data)

        # Resetear formulario
        self._ing_suppress = True
        self._ing_food_var.set("")
        self._ing_suppress = False
        self._selected_food = None
        self._ing_gramos_var.set("100")
        self._ing_medida_var.set("")
        self._macro_preview.configure(text="")

        self._load_ingredients(self._selected_recipe_id)
        self._refresh_nutrition_tab()

    def _load_ingredients(self, rid: int):
        for w in self._ing_scroll.winfo_children():
            w.destroy()

        items = db.get_receta_ingredientes(rid)
        total = {"kcal": 0, "prot": 0, "cho": 0, "fat": 0, "fib": 0}

        if not items:
            ctk.CTkLabel(
                self._ing_scroll,
                text="Sin ingredientes. Busca y agrega alimentos arriba.",
                text_color="gray", font=ctk.CTkFont(size=12)
            ).grid(row=0, column=0, pady=20)
        else:
            for i, item in enumerate(items):
                self._build_ingredient_row(i, item)
                total["kcal"] += item.get("calorias") or 0
                total["prot"] += item.get("proteinas_g") or 0
                total["cho"]  += item.get("carbohidratos_g") or 0
                total["fat"]  += item.get("grasas_g") or 0
                total["fib"]  += item.get("fibra_g") or 0

        self._ing_totals_lbl.configure(
            text=(f"Total receta: {total['kcal']:.0f} kcal  ·  "
                  f"{total['prot']:.1f}g prot  ·  "
                  f"{total['cho']:.1f}g CHO  ·  "
                  f"{total['fat']:.1f}g grasas  ·  "
                  f"{total['fib']:.1f}g fibra")
        )

    def _build_ingredient_row(self, idx: int, item: dict):
        bg = ("gray95", "gray20") if idx % 2 == 0 else ("white", "gray17")
        row = ctk.CTkFrame(self._ing_scroll, fg_color=bg, corner_radius=6)
        row.grid(row=idx, column=0, sticky="ew", padx=2, pady=2)
        row.grid_columnconfigure(0, weight=1)

        medida = f"  ({item['medida_casera']})" if item.get("medida_casera") else ""
        ctk.CTkLabel(
            row,
            text=f"{item['nombre_alimento']}{medida}  ·  {item['gramos']:.0f}g",
            font=ctk.CTkFont(size=12), anchor="w"
        ).grid(row=0, column=0, padx=10, pady=(6, 0), sticky="w")

        ctk.CTkLabel(
            row,
            text=(f"{item.get('calorias', 0):.0f} kcal  ·  "
                  f"{item.get('proteinas_g', 0):.1f}g prot  ·  "
                  f"{item.get('carbohidratos_g', 0):.1f}g CHO  ·  "
                  f"{item.get('grasas_g', 0):.1f}g grasas"),
            font=ctk.CTkFont(size=11), text_color="gray", anchor="w"
        ).grid(row=1, column=0, padx=10, pady=(0, 6), sticky="w")

        ctk.CTkButton(
            row, text="✕", width=28, height=28,
            fg_color="transparent",
            text_color=(_C_TERRACOTTA, "#f87171"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda iid=item["id"]: self._delete_ingredient(iid)
        ).grid(row=0, column=1, rowspan=2, padx=8, pady=4)

    def _delete_ingredient(self, iid: int):
        db.delete_receta_ingrediente(iid)
        if self._selected_recipe_id:
            self._load_ingredients(self._selected_recipe_id)
            self._refresh_nutrition_tab()

    # ── Tab Aporte Nutricional ─────────────────────────────────────────────────

    def _refresh_nutrition_tab(self):
        if not self._selected_recipe_id:
            return
        items = db.get_receta_ingredientes(self._selected_recipe_id)
        r = db.get_receta(self._selected_recipe_id)
        porciones = max(1, (r["porciones_rinde"] if r else 1) or 1)

        total = {"kcal": 0.0, "prot": 0.0, "cho": 0.0, "fat": 0.0, "fib": 0.0}
        for item in items:
            total["kcal"] += item.get("calorias") or 0
            total["prot"] += item.get("proteinas_g") or 0
            total["cho"]  += item.get("carbohidratos_g") or 0
            total["fat"]  += item.get("grasas_g") or 0
            total["fib"]  += item.get("fibra_g") or 0

        self._nutr_labels["kcal_por"].configure(text=f"{total['kcal']/porciones:.0f}")
        self._nutr_labels["prot_por"].configure(text=f"{total['prot']/porciones:.1f}")
        self._nutr_labels["cho_por"].configure(text=f"{total['cho']/porciones:.1f}")
        self._nutr_labels["fat_por"].configure(text=f"{total['fat']/porciones:.1f}")
        self._nutr_labels["fib_por"].configure(text=f"{total['fib']/porciones:.1f}")

        self._nutr_total_lbl.configure(
            text=(f"{total['kcal']:.0f} kcal  ·  {total['prot']:.1f}g prot  ·  "
                  f"{total['cho']:.1f}g CHO  ·  {total['fat']:.1f}g grasas  ·  "
                  f"{total['fib']:.1f}g fibra  "
                  f"(total para {porciones} porción{'es' if porciones != 1 else ''})")
        )

        # Actualizar referencia en tab Equivalencias
        kp = total["kcal"] / porciones
        pp = total["prot"] / porciones
        cp = total["cho"]  / porciones
        fp = total["fat"]  / porciones
        self._equiv_ref_lbl.configure(
            text=f"Receta: {kp:.0f} kcal | {pp:.1f}g prot | {cp:.1f}g CHO | {fp:.1f}g grasas  (por porción)"
        )

    # ── Tab Equivalencias ─────────────────────────────────────────────────────

    def _load_equivalencias(self, rid: int):
        for var in self._equiv_vars.values():
            var.set("0")
        for eq in db.get_receta_equivalencias(rid):
            grupo = eq["grupo"]
            if grupo in self._equiv_vars:
                self._equiv_vars[grupo].set(str(eq["porciones"]))
        self._update_equiv_totals()

    def _update_equiv_totals(self):
        total_kcal = total_prot = total_cho = total_fat = 0.0
        for grupo, var in self._equiv_vars.items():
            try:
                porciones = float(var.get() or 0)
            except ValueError:
                porciones = 0.0
            m = GRUPOS_MACROS[grupo]
            total_kcal += porciones * m["kcal"]
            total_prot += porciones * m["prot"]
            total_cho  += porciones * m["cho"]
            total_fat  += porciones * m["lip"]
        self._equiv_total_lbl.configure(
            text=(f"Desde equivalencias: {total_kcal:.0f} kcal | "
                  f"{total_prot:.1f}g prot | {total_cho:.1f}g CHO | {total_fat:.1f}g grasas")
        )

    def _save_equivalencias(self):
        if not self._selected_recipe_id:
            messagebox.showwarning(
                "Atención",
                "Guarda primero la información de la receta."
            )
            return
        equivalencias = {}
        for grupo, var in self._equiv_vars.items():
            try:
                porciones = float(var.get() or 0)
            except ValueError:
                porciones = 0.0
            if porciones > 0:
                equivalencias[grupo] = porciones
        db.save_receta_equivalencias(self._selected_recipe_id, equivalencias)
        self.app.show_toast("✓ Equivalencias guardadas")
