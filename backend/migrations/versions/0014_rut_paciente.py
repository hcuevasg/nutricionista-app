"""RUT del paciente, único dentro de la cuenta de cada profesional.

Revision ID: 0014_rut_paciente
Revises: 0013_columnas_cifradas
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op

revision = "0014_rut_paciente"
down_revision = "0013_columnas_cifradas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "rut" not in {c["name"] for c in inspector.get_columns("patients")}:
        op.add_column("patients", sa.Column("rut", sa.String(12), nullable=True))
    if "uq_patients_nutritionist_rut" not in {i["name"] for i in inspector.get_indexes("patients")}:
        op.create_index("uq_patients_nutritionist_rut", "patients", ["nutritionist_id", "rut"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_patients_nutritionist_rut", table_name="patients")
    with op.batch_alter_table("patients") as batch:
        batch.drop_column("rut")
