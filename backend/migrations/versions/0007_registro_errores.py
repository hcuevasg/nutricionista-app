"""Registro interno de errores.

`create_all()` del arranque ya crea la tabla en bases nuevas, por eso solo se
crea si falta.

Revision ID: 0007_registro_errores
Revises: 0006_consentimiento
Create Date: 2026-10-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0007_registro_errores"
down_revision = "0006_consentimiento"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "error_logs" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "error_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nutritionist_id", sa.Integer(), sa.ForeignKey("nutritionists.id", ondelete="CASCADE"),
                  nullable=True),
        sa.Column("source", sa.String(20)),
        sa.Column("method", sa.String(10), nullable=True),
        sa.Column("path", sa.String(500), nullable=True),
        sa.Column("error_type", sa.String(120), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("stack", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_error_logs_id", "error_logs", ["id"])
    op.create_index("ix_error_logs_nutritionist_id", "error_logs", ["nutritionist_id"])
    op.create_index("ix_error_logs_created_at", "error_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("error_logs")
