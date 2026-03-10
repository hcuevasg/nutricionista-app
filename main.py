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


def main():
    initialize_db()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
