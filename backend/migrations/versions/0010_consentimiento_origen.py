"""Origen (profesional/portal) e IP del consentimiento del paciente.

Revision ID: 0010_consentimiento_origen
Revises: 0009_notas_evolucion
Create Date: 2026-10-23
"""
import sqlalchemy as sa
from alembic import op

revision = "0010_consentimiento_origen"
down_revision = "0009_notas_evolucion"
branch_labels = None
depends_on = None

_COLUMNS = [
    ("consent_source", sa.String(20)),
    ("consent_ip", sa.String(45)),
]


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("patients")}
    for name, type_ in _COLUMNS:
        if name not in existing:
            op.add_column("patients", sa.Column(name, type_, nullable=True))
    # Los consentimientos anteriores los registró el profesional
    op.execute("UPDATE patients SET consent_source = 'profesional' "
               "WHERE consent_at IS NOT NULL AND consent_source IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("patients") as batch:
        for name, _ in reversed(_COLUMNS):
            batch.drop_column(name)
