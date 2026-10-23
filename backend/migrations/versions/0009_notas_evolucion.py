"""Notas de evolución por consulta (SOAP).

`create_all()` del arranque ya crea la tabla en bases nuevas, por eso solo se
crea si falta.

Revision ID: 0009_notas_evolucion
Revises: 0008_totp_uso_unico
Create Date: 2026-10-23
"""
import sqlalchemy as sa
from alembic import op

revision = "0009_notas_evolucion"
down_revision = "0008_totp_uso_unico"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "notas_evolucion" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "notas_evolucion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fecha", sa.String(10), nullable=False),
        sa.Column("motivo", sa.String(255)),
        sa.Column("subjetivo", sa.Text()),
        sa.Column("objetivo", sa.Text()),
        sa.Column("analisis", sa.Text()),
        sa.Column("plan", sa.Text()),
        sa.Column("proximo_control", sa.String(10)),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_notas_evolucion_id", "notas_evolucion", ["id"])
    op.create_index("ix_notas_evolucion_patient_id", "notas_evolucion", ["patient_id"])


def downgrade() -> None:
    op.drop_table("notas_evolucion")
