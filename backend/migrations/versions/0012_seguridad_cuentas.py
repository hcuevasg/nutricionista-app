"""Seguridad de cuentas: bloqueo por intentos fallidos y versión de sesión.

Revision ID: 0012_seguridad_cuentas
Revises: 0011_examenes_laboratorio
Create Date: 2026-10-23
"""
import sqlalchemy as sa
from alembic import op

revision = "0012_seguridad_cuentas"
down_revision = "0011_examenes_laboratorio"
branch_labels = None
depends_on = None

_COLUMNS = [
    ("failed_logins", sa.Integer(), {"nullable": False, "server_default": "0"}),
    ("locked_until", sa.DateTime(), {"nullable": True}),
    ("token_version", sa.Integer(), {"nullable": False, "server_default": "0"}),
]


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("nutritionists")}
    for name, type_, kw in _COLUMNS:
        if name not in existing:
            op.add_column("nutritionists", sa.Column(name, type_, **kw))


def downgrade() -> None:
    with op.batch_alter_table("nutritionists") as batch:
        for name, _, _ in reversed(_COLUMNS):
            batch.drop_column(name)
