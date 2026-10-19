"""Elimina el módulo de planes alimenticios (reemplazado por las pautas).

Borra las tablas meal_items y meal_plans. Por seguridad solo lo hace si están
vacías: si quedara algún plan, la migración falla sin tocar nada y hay que
respaldarlo antes (en producción estaban vacías el 2026-10-19).

Revision ID: 0003_eliminar_planes
Revises: 0002_metas_evaluacion
Create Date: 2026-10-19
"""
import sqlalchemy as sa
from alembic import op

revision = "0003_eliminar_planes"
down_revision = "0002_metas_evaluacion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    for table in ("meal_items", "meal_plans"):
        if table in tables:
            n = bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar()
            if n:
                raise RuntimeError(f"{table} tiene {n} filas: respáldalas antes de eliminar la tabla")
    for table in ("meal_items", "meal_plans"):  # primero la que tiene la FK
        if table in tables:
            op.drop_table(table)


def downgrade() -> None:
    # Recrea las tablas vacías con el esquema que tenían (models.py antes de eliminarlas)
    op.create_table(
        "meal_plans",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), index=True),
        sa.Column("name", sa.String(255)),
        sa.Column("date", sa.String()),
        sa.Column("goal", sa.String(255), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("protein_g", sa.Float(), nullable=True),
        sa.Column("carbs_g", sa.Float(), nullable=True),
        sa.Column("fat_g", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "meal_items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("meal_plans.id"), index=True),
        sa.Column("meal_type", sa.String(50)),
        sa.Column("food_name", sa.String(255)),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("protein_g", sa.Float(), nullable=True),
        sa.Column("carbs_g", sa.Float(), nullable=True),
        sa.Column("fat_g", sa.Float(), nullable=True),
        sa.Column("fiber_g", sa.Float(), nullable=True),
    )
