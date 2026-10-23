"""Entorno de Alembic: usa el engine y los modelos de la app."""
from alembic import context

import models  # noqa: F401  (registra todas las tablas en Base.metadata)
from database import Base, engine

target_metadata = Base.metadata


def _compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    """Una columna cifrada (EncryptedText) vive en cualquier columna de texto de la
    base: no es una diferencia de esquema. El resto usa la comparación por defecto."""
    from crypto_fields import EncryptedText
    from sqlalchemy import String
    if isinstance(metadata_type, EncryptedText):
        return not isinstance(inspected_type, String)
    return None


def run_migrations_offline() -> None:
    context.configure(url=str(engine.url), target_metadata=target_metadata,
                      literal_binds=True, render_as_batch=engine.dialect.name == "sqlite",
                      compare_type=_compare_type)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return
    with engine.connect() as conn:
        _run(conn)


def _run(connection) -> None:
    # render_as_batch: SQLite no soporta ALTER COLUMN; Alembic recrea la tabla
    context.configure(connection=connection, target_metadata=target_metadata,
                      render_as_batch=connection.dialect.name == "sqlite", compare_type=_compare_type)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
