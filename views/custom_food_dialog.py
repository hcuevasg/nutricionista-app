"""Dialog to add a custom food to alimentos_db."""
import customtkinter as ctk
from tkinter import messagebox
import database.db_manager as db


class CustomFoodDialog(ctk.CTkToplevel):
    """Modal form to create a new custom food entry (per 100 g)."""

    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("Agregar alimento personalizado")
        self.geometry("460x420")
        self.resizable(False, False)
        self.grab_set()
        self._on_save = on_save
        self._build_ui()
        self.after(50, self._center)

    def _center(self):
        self.update_idletasks()
        pw, ph = self.master.winfo_width(), self.master.winfo_height()
        px, py = self.master.winfo_rootx(), self.master.winfo_rooty()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w)//2}+{py + (ph - h)//2}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Nuevo alimento personalizado",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="w")

        ctk.CTkLabel(
            self, text="Valores nutricionales por 100 g",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=2, column=0, sticky="ew", padx=20)
        form.grid_columnconfigure((0, 1), weight=1)

        self._vars = {}
        fields = [
            ("Nombre (español) *", "nombre_es", 0, 0, 2),
            ("Nombre en inglés (opcional)", "nombre_en", 1, 0, 2),
            ("Calorías (kcal) *", "calorias", 2, 0, 1),
            ("Proteínas (g) *", "proteinas_g", 2, 1, 1),
            ("Carbohidratos (g) *", "carbohidratos_g", 3, 0, 1),
            ("Grasas (g) *", "grasas_g", 3, 1, 1),
            ("Fibra (g)", "fibra_g", 4, 0, 1),
            ("Azúcares (g)", "azucares_g", 4, 1, 1),
            ("Sodio (mg)", "sodio_mg", 5, 0, 1),
        ]

        for label, key, row, col, span in fields:
            ctk.CTkLabel(form, text=label, text_color="gray",
                         font=ctk.CTkFont(size=11)).grid(
                row=row * 2, column=col, columnspan=span,
                padx=(0 if col == 0 else 8, 0), pady=(6, 0), sticky="w")
            v = ctk.StringVar()
            self._vars[key] = v
            ctk.CTkEntry(form, textvariable=v, height=34).grid(
                row=row * 2 + 1, column=col, columnspan=span,
                padx=(0 if col == 0 else 8, 0), pady=(0, 0), sticky="ew")

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=20, pady=(16, 20))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_row, text="Cancelar", height=38,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            command=self.destroy
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            btn_row, text="Guardar alimento", height=38,
            command=self._save
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _save(self):
        nombre = self._vars["nombre_es"].get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio.", parent=self)
            return

        def _f(key, required=False):
            s = self._vars[key].get().strip()
            if not s:
                return None
            try:
                return float(s)
            except ValueError:
                messagebox.showerror("Error", f"Valor inválido en «{key}».", parent=self)
                return None

        calorias = _f("calorias")
        proteinas = _f("proteinas_g")
        carbohidratos = _f("carbohidratos_g")
        grasas = _f("grasas_g")
        if any(v is None for v in [calorias, proteinas, carbohidratos, grasas]):
            messagebox.showerror(
                "Error", "Calorías, proteínas, carbohidratos y grasas son obligatorios.",
                parent=self)
            return

        data = {
            "nombre_es":       nombre,
            "nombre_en":       self._vars["nombre_en"].get().strip() or None,
            "calorias":        calorias,
            "proteinas_g":     proteinas,
            "carbohidratos_g": carbohidratos,
            "grasas_g":        grasas,
            "fibra_g":         _f("fibra_g") or 0.0,
            "azucares_g":      _f("azucares_g"),
            "sodio_mg":        _f("sodio_mg"),
            "fuente":          "personalizado",
            "es_personalizado": 1,
        }

        food_id = db.insert_food(data)
        data["id"] = food_id
        if self._on_save:
            self._on_save(data)
        self.destroy()
