# utils/ — Lógica de Cálculos y Utilidades

## 📊 Módulo: calculations.py

**Responsabilidad:** Cálculos antropométricos, macronutrientes, índices de salud

### ISAK 1 Functions
- `body_fat_durnin_womersley(age, sex, skinfolds)` — % grasa usando tabla Durnin & Womersley (1974)
  - **Entrada:** 4 pliegues específicos (triceps, subscapular, biceps, iliac crest)
  - **Crítico:** Tabla es exacta, no interpolar

- `sum_6_skinfolds(dict)` — Suma de 6 pliegues ISAK
  - Retorna `sum_6_skinfolds` (valor almacenado en BD)

### ISAK 2 Functions
- `somatotype_heath_carter(...)` — Heath & Carter (1990)
  - **Entrada:** endomorphy, mesomorphy, ectomorphy scores
  - **Output:** Categorización (balanced, ecto-mesomorph, etc.)
  - **BD storage:** `somatotype_endo`, `somatotype_meso`, `somatotype_ecto`

- `waist_height_ratio(waist_cm, height_cm)` — Índice cintura/talla (WHtR)
- `arm_muscle_area(arm_relaxed_cm, triceps_mm)` — Área muscular del brazo (AMB)

### General Functions
- `bmi(weight_kg, height_cm)`, `bmr_mifflin()`, `tdee()`
- `ideal_weight_lorentz(height_cm, sex)`
- `macro_distribution(calories, diet_type)` — Distribución de macros

**⚠️ REGLA:** Nunca simplificar fórmulas — usar referencias exactas de papers

---

## 🎨 Módulo: pdf_generator.py (1295 líneas)

**Responsabilidad:** Reportes PDF profesionales usando ReportLab + Matplotlib

### Clases Principales
- `GeneradorReportesISAK` — Maneja generación de PDFs
  - Importa matplotlib para somatocarta (gráfico 3D Heath-Carter)
  - **Crítico:** matplotlib debe estar en bundle macOS (fix: ef7c513)

### Métodos Clave
- Informe ISAK comparativo (multi-sesión)
- Somatocarta (necesita Matplotlib)
- Plan alimenticio con tabla de macros
- Reporte completo del paciente

**⚠️ QUIRKS:**
- KeepTogether para títulos de secciones (fix: 2519c11)
- ReportLab requiere Pillow para imágenes
- Matplotlib 3.5-3.8 (constraints en requirements.txt)

---

## 🖼️ Módulo: image_helpers.py

- `get_initials(name)` — Extrae iniciales de nombre
- `make_circle_image(initials, size, color)` — Avatar circular para pacientes

**Dependencia:** Pillow (requerida por CustomTkinter)

---

## 💾 Módulo: backup_manager.py

- `create_backup()` — Backup automático de BD
- Llamado en `main.py:19-20` al iniciar app
- **No modificar lógica** sin testear backup/restore

---

## 🗄️ import_usda.py (Script standalone)

**Responsabilidad:** Importar datos nutricionales USDA a `alimentos_db`

- **Crítico:** Siempre inicializa BD antes de insertar (fix: af81afe)
- Usa búsqueda case-insensitive con COLLATE NOCASE
- Ejecutar: `python import_usda.py`

---

## 📌 Patrones de Código

- Preferir `dict.get('key', default)` vs `dict['key']`
- Manejo de `None` explícito en cálculos
- Logs para debugging: `print()` está OK para desarrollo
- BD: Siempre usar `get_connection()` + context manager si aplica

---

**Nota:** Para modificaciones en cálculos, siempre revisar referencias científicas primero.
