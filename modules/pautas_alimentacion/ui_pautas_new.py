"""
Módulo de Pautas de Alimentación — Interfaz CustomTkinter.

PautasFrame
  ├── Panel superior: selector de pauta + gestión
  └── CTkTabview
        ├── Tab 1: Requerimientos (TMB/GET/macros)
        ├── Tab 2: Porciones + distribución
        ├── Tab 3: Ejemplos de Menú (USDA search)
        ├── Tab 4: Tabla de Equivalencias
        └── Tab 5: Exportar PDF
"""
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional
import customtkinter as ctk
from datetime import datetime

import database.db_manager as db
from modules.pautas_alimentacion.grupos_alimentos import (
    GRUPOS_MACROS, GRUPOS_POR_PAUTA, NOMBRES_GRUPOS,
    NOMBRES_TIPOS_PAUTA, TIEMPOS_COMIDA
)
from modules.pautas_alimentacion.calculadora_requerimientos import (
    FACTORES_ACTIVIDAD, calcular_tmb, calcular_get, calcular_macros,
    get_fa_valor
)
from modules.pautas_alimentacion.distribucion_porciones import (
    calcular_aporte_grupo, calcular_adecuacion, validar_porciones_totales,
    calcular_aporte_total
)
from modules.pautas_alimentacion.tablas_equivalencias import (
    TABLAS_EQUIVALENCIAS, NOMBRES_GRUPOS_EQUIV, ABREVIATURAS
)

