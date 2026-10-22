"""Verificación en dos pasos (TOTP) para nutricionistas.

Revision ID: 0005_dos_pasos
Revises: 0004_plantillas_pauta
Create Date: 2026-10-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0005_dos_pasos"
down_revision = "0004_plantillas_pauta"
branch_labels = None
depends_on = None

_COLUMNS = [
    ("totp_secret", sa.String(64), {}),
    ("totp_enabled", sa.Boolean(), {"nullable": False, "server_default": sa.false()}),
    ("totp_recovery_codes", sa.Text(), {}),
]


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("nutritionists")}
    for name, type_, kw in _COLUMNS:
        if name not in existing:
            op.add_column("nutritionists", sa.Column(name, type_, **({"nullable": True} | kw)))


def downgrade() -> None:
    with op.batch_alter_table("nutritionists") as batch:
        for name, _, _ in reversed(_COLUMNS):
            batch.drop_column(name)
