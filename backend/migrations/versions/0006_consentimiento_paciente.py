"""Consentimiento informado del paciente para tratar datos de salud.

Revision ID: 0006_consentimiento
Revises: 0005_dos_pasos
Create Date: 2026-10-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0006_consentimiento"
down_revision = "0005_dos_pasos"
branch_labels = None
depends_on = None

_COLUMNS = [
    ("consent_at", sa.DateTime()),
    ("consent_version", sa.String(20)),
]


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("patients")}
    for name, type_ in _COLUMNS:
        if name not in existing:
            op.add_column("patients", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("patients") as batch:
        for name, _ in reversed(_COLUMNS):
            batch.drop_column(name)
