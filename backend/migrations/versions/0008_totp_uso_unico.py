"""Códigos TOTP de un solo uso: guarda el paso del último código aceptado.

Revision ID: 0008_totp_uso_unico
Revises: 0007_registro_errores
Create Date: 2026-10-23
"""
import sqlalchemy as sa
from alembic import op

revision = "0008_totp_uso_unico"
down_revision = "0007_registro_errores"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("nutritionists")}
    if "totp_last_step" not in existing:
        op.add_column("nutritionists", sa.Column("totp_last_step", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("nutritionists") as batch:
        batch.drop_column("totp_last_step")
