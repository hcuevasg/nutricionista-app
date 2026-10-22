"""Plantillas reutilizables de pautas.

`create_all()` del arranque ya crea la tabla en bases nuevas, por eso solo se
crea si falta.

Revision ID: 0004_plantillas_pauta
Revises: 0003_eliminar_planes
Create Date: 2026-10-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0004_plantillas_pauta"
down_revision = "0003_eliminar_planes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "plantillas_pauta" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "plantillas_pauta",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nutritionist_id", sa.Integer(), sa.ForeignKey("nutritionists.id", ondelete="CASCADE")),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("tipo_pauta", sa.String(50)),
        sa.Column("fa_key", sa.String(50)),
        sa.Column("ajuste_kcal", sa.Float(), nullable=True),
        sa.Column("prot_pct", sa.Float()),
        sa.Column("lip_pct", sa.Float()),
        sa.Column("porciones_json", sa.Text()),
        sa.Column("distribucion_json", sa.Text()),
        sa.Column("menu_json", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_plantillas_pauta_id", "plantillas_pauta", ["id"])
    op.create_index("ix_plantillas_pauta_nutritionist_id", "plantillas_pauta", ["nutritionist_id"])


def downgrade() -> None:
    op.drop_table("plantillas_pauta")
