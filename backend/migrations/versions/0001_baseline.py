"""Línea base: esquema actual.

El esquema hasta aquí lo crean Base.metadata.create_all() y la lista de
migraciones heredadas de main.py (idempotentes). Esta revisión no cambia nada:
solo marca el punto desde el que los cambios de esquema se hacen con Alembic.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-19
"""

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
