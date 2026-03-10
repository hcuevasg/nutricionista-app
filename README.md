# NutriApp

Aplicación de escritorio para nutricionistas. Gestiona pacientes, evaluaciones antropométricas **ISAK 1 e ISAK 2**, planes alimenticios y genera reportes PDF profesionales.

---

## Descarga

> **macOS (Intel x86_64)**
>
> Descarga el archivo `.zip` desde la sección [**Releases**](../../releases/latest), descomprime y arrastra `NutriApp.app` a tu carpeta de Aplicaciones.

---

## Características

- **Gestión de pacientes** — Registro completo con datos personales e historial clínico.
- **Evaluación antropométrica ISAK 1** — % grasa corporal con Durnin & Womersley (1974), Σ6 pliegues, composición corporal.
- **Evaluación antropométrica ISAK 2** — Perfil completo: 11 pliegues, perímetros adicionales, diámetros óseos, longitudes, **somatotipo Heath & Carter (1990)**, índice cintura/talla, área muscular del brazo.
- **Planes alimenticios** — Objetivos calóricos, macros y alimentos por tiempo de comida.
- **Reportes PDF** — Informe ISAK comparativo (multi-sesión), somatocarta, plan alimenticio y reporte completo del paciente.
- **Interfaz moderna** — Tema claro/oscuro con CustomTkinter.

---

## Capturas de pantalla

*(próximamente)*

---

## Instalación desde código fuente

### Requisitos
- Python 3.10 o superior
- Windows 10/11, macOS 12+ o Linux con Tcl/Tk

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/nutricionista-app.git
cd nutricionista-app

# 2. Crear entorno virtual
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
```

---

## Estructura del proyecto

```
nutricionista-app/
├── main.py                     # Punto de entrada
├── requirements.txt
├── database/
│   └── db_manager.py           # CRUD SQLite + migración automática de esquema
├── utils/
│   ├── calculations.py         # Cálculos antropométricos (ISAK 1 + ISAK 2)
│   └── pdf_generator.py        # Reportes PDF (ReportLab) + somatocarta
└── views/
    ├── main_window.py          # Ventana principal y sidebar
    ├── patient_list.py         # Lista y búsqueda de pacientes
    ├── patient_form.py         # Alta / edición de paciente
    ├── anthropometric_view.py  # Evaluación ISAK 1 e ISAK 2 + historial
    ├── meal_plan_view.py       # Planes alimenticios
    └── reports_view.py         # Exportación de reportes PDF
```

---

## Cálculos disponibles

| Módulo | Función | Descripción |
|---|---|---|
| ISAK 1 | `body_fat_durnin_womersley()` | % Grasa — Durnin & Womersley (1974) |
| ISAK 1 | `sum_6_skinfolds()` | Σ 6 pliegues ISAK |
| ISAK 2 | `somatotype_heath_carter()` | Somatotipo — Heath & Carter (1990) |
| ISAK 2 | `waist_height_ratio()` | Índice cintura/talla |
| ISAK 2 | `arm_muscle_area()` | Área muscular del brazo (AMB) |
| General | `bmi()`, `bmr_mifflin()`, `tdee()` | IMC, TMB, TDER |
| General | `ideal_weight_lorentz()` | Peso ideal Lorentz |
| General | `body_fat_navy()` | % Grasa método U.S. Navy |
| General | `macro_distribution()` | Distribución de macronutrientes |

---

## Base de datos

SQLite con migración automática al iniciar. Tablas principales:

| Tabla | Descripción |
|---|---|
| `patients` | Datos personales del paciente |
| `anthropometrics` | Historial ISAK 1 e ISAK 2 (50+ campos) |
| `meal_plans` | Planes alimenticios |
| `meal_items` | Alimentos por plan y tiempo de comida |

---

## Dependencias

```
customtkinter>=5.2.0   # UI moderna con soporte dark/light mode
reportlab>=4.0.0       # Generación de PDFs
Pillow>=10.0.0         # Imágenes (requerido por CustomTkinter)
```

---

## Licencia

MIT — libre para uso personal y profesional.
