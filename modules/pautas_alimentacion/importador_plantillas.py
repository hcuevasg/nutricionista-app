"""
Importador de plantillas de menú desde Excel.
Estructura a definir cuando se adjunten los archivos reales.
"""
from typing import List, Dict, Optional


def importar_desde_excel(ruta_archivo: str, tipo_pauta: str,
                          kcal_objetivo: float, prot_objetivo: float,
                          descripcion: str) -> int:
    """
    Lee un Excel de plantilla de menú.
    Estructura del Excel: a definir en siguiente iteración.
    Retorna el id de la plantilla creada en BD.
    """
    raise NotImplementedError("Implementar cuando se adjunten los archivos Excel.")


def listar_plantillas_importadas() -> List[Dict]:
    import database.db_manager as db
    return db.get_plantillas_ref()


def eliminar_plantilla_importada(plantilla_id: int):
    import database.db_manager as db
    db.delete_plantilla_ref(plantilla_id)
