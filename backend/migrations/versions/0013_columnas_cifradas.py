"""Columnas cifradas: pasan a TEXT porque el valor cifrado es más largo que el original.

El cifrado de los datos existentes lo hace el arranque (crypto_fields.encrypt_existing)
cuando DATA_ENCRYPTION_KEY está configurada. SQLite no impone largos: no requiere cambios.

Revision ID: 0013_columnas_cifradas
Revises: 0012_seguridad_cuentas
Create Date: 2026-10-23
"""
import sqlalchemy as sa
from alembic import op

revision = "0013_columnas_cifradas"
down_revision = "0012_seguridad_cuentas"
branch_labels = None
depends_on = None

_COLUMNS = [
    ("nutritionists", "totp_secret"),
    ("patients", "address"),
    ("patients", "occupation"),
    ("examenes_laboratorio", "notas"),
    ("notas_evolucion", "motivo"),
]


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for table, column in _COLUMNS:
        op.alter_column(table, column, type_=sa.Text(), existing_nullable=True)


def downgrade() -> None:
    pass  # volver a VARCHAR truncaría valores cifrados
