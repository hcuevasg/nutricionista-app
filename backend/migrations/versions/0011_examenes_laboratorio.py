"""Exámenes de laboratorio del paciente.

`create_all()` del arranque ya crea la tabla en bases nuevas, por eso solo se
crea si falta.

Revision ID: 0011_examenes_laboratorio
Revises: 0010_consentimiento_origen
Create Date: 2026-10-23
"""
import sqlalchemy as sa
from alembic import op

revision = "0011_examenes_laboratorio"
down_revision = "0010_consentimiento_origen"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "examenes_laboratorio" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "examenes_laboratorio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fecha", sa.String(10), nullable=False),
        sa.Column("analito", sa.String(50), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("unidad", sa.String(20)),
        sa.Column("ref_min", sa.Float()),
        sa.Column("ref_max", sa.Float()),
        sa.Column("notas", sa.String(255)),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_examenes_laboratorio_id", "examenes_laboratorio", ["id"])
    op.create_index("ix_examenes_laboratorio_patient_id", "examenes_laboratorio", ["patient_id"])


def downgrade() -> None:
    op.drop_table("examenes_laboratorio")
