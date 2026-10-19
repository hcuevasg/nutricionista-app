"""Metas y fecha de próxima evaluación en anthropometrics.

En Postgres (producción) ya las creó la migración heredada; en SQLite no,
porque SQLite no soporta `ADD COLUMN IF NOT EXISTS`. Por eso se agregan solo
si faltan.

Revision ID: 0002_metas_evaluacion
Revises: 0001_baseline
Create Date: 2026-10-19
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_metas_evaluacion"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

_COLUMNS = [("goals_text", sa.Text()), ("next_eval_date", sa.String())]


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("anthropometrics")}
    for name, type_ in _COLUMNS:
        if name not in existing:
            op.add_column("anthropometrics", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("anthropometrics") as batch:
        for name, _ in reversed(_COLUMNS):
            batch.drop_column(name)
