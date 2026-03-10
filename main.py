"""
NutriApp — Aplicación de gestión nutricional para profesionales.
Punto de entrada principal.
"""
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from database.db_manager import initialize_db
from views.main_window import App
import utils.backup_manager as bm


def main():
    initialize_db()
    # Backup automático al iniciar
    try:
        bm.create_backup()
        _auto_backup_ok = True
    except Exception:
        _auto_backup_ok = False

    app = App()

    if _auto_backup_ok:
        app.after(800, lambda: app.show_toast("Backup automático creado correctamente ✓"))

    app.mainloop()


if __name__ == "__main__":
    main()
