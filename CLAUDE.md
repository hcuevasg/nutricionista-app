# NutriApp — Configuración de Claude Code

## 📌 Contexto del Proyecto

**NutriApp** es una aplicación de escritorio para nutricionistas que gestiona pacientes, evaluaciones antropométricas ISAK 1/2, planes alimenticios y genera reportes PDF profesionales.

- **Stack:** Python 3.10+ | CustomTkinter (UI) | SQLite (BD) | ReportLab (PDFs) | Matplotlib (gráficos)
- **Versión:** En desarrollo activo con releases macOS Intel + Apple Silicon
- **Punto de entrada:** `main.py` (inicializa DB + backup automático)

---

## 🏗️ Estructura y Patrones

### Directorios Principales
```
nutricionista-app/
├── database/        → CRUD SQLite, migrations automáticas (db_manager.py)
├── utils/          → Cálculos (ISAK 1/2, macros), PDFs, backups
├── views/          → CustomTkinter frames (patient, anthropometric, meal_plans, etc)
└── models/         → Vacío (datos en BD, no ORM)
```

### Patrones Clave
- **State management:** `App._selected_patient_id`, `_pending_plan_id` en main_window.py
- **DB access:** `get_connection()` + `row_factory = sqlite3.Row` (dict-like)
- **Frame switching:** `show_frame(key)` en App
- **PDFs:** ReportLab + Matplotlib para somatocarta

---

## 🛠️ Comandos Esenciales

```bash
# Ejecutar la app
python main.py

# Importar datos USDA
python import_usda.py

# Tests (si existen)
pytest
```

---

## ⚠️ Reglas Anti-Alucinación

1. **SIEMPRE leer archivos antes de modificar** — `Read()` primero, nunca especular
2. **Ser específico en prompts** — "Fix line 42 in patient_form.py" vs "arregla el formulario"
3. **Usar file:line references** — Facilita navegación: `views/patient_form.py:42`
4. **Verificar esquema BD antes de cambios** — Schema en `database/db_manager.py:16-200`
5. **No asumir funciones** — Si no sé si existe, busco con Grep primero

---

## 🚀 Workflow Recomendado

1. **Para bugs:** `/plan` → review → implementar → `/clear` → `/verify-work`
2. **Para features:** Usar plan mode, descomponer en tareas atómicas
3. **Para refactoring:** Leer primero, planificar, después modificar (nunca reescribir sin leer)
4. **Para PDFs:** Revisar `utils/pdf_generator.py` — ReportLab tiene quirks

---

## 🔒 Sensibilidades

- **Base de datos:** SQLite con foreign keys habilitadas — cascading deletes activos
- **PDFs:** KeepTogether para títulos de secciones (fix reciente: commit 2519c11)
- **macOS:** Matplotlib debe estar en bundle para releases (fix: ef7c513)
- **Alimentos DB:** COLLATE NOCASE para búsquedas case-insensitive

---

## 📊 Cálculos Críticos (no simplificar)

- **ISAK 1:** Durnin & Womersley (1974) — usar tabla exacta, 4 pliegues específicos
- **ISAK 2:** Heath & Carter (1990) somatotipo — 11 pliegues + perímetros + diámetros óseos
- **Macros:** Usar `utils/calculations.py:macro_distribution()` — no hacer cálculos inline

---

## 📝 Notas de Commits

- Prefijo: `feat:` (feature), `fix:` (bug), `refactor:` (código)
- Mensaje en presente: "add X" no "added X"
- Español cuando tenga sentido: "feat: sistema de plantillas"
- Una línea clara + detalles si aplica

---

## 🎯 Código de Conducta para Claude Code

- **Plan mode first** — Siempre para tareas >3 cambios
- **Atomic commits** — Un cambio lógico por commit
- **Read before write** — No asumir
- **Verify after edit** — Checks de lógica básica
- **Use /memory** — Para aprendizajes del proyecto

---

**Ver también:** `.claude/CLAUDE.md` (configuración global), `./utils/CLAUDE.md` (lógica específica)
