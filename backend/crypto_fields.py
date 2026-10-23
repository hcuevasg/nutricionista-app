"""Cifrado de columnas con datos de salud (Fernet: AES-128-CBC + HMAC-SHA256).

Las columnas `EncryptedText` se guardan como "enc:v1:<token>" y se descifran al
leerlas, así un respaldo de la base o un acceso indebido a ella no expone el
contenido clínico. La clave vive solo en la variable DATA_ENCRYPTION_KEY
(genera una con `python backup_r2.py genkey`). Para rotarla se ponen varias
separadas por coma: la primera cifra y todas sirven para descifrar.

Los valores que aún están en texto plano (anteriores a activar el cifrado) se
leen tal cual y `encrypt_existing()` los cifra al arrancar el servidor.
"""
import logging
import os
from functools import lru_cache
from typing import Dict, List, Optional

from sqlalchemy import Text, select, text, update
from sqlalchemy.types import TypeDecorator

logger = logging.getLogger("nutriapp.crypto")
PREFIX = "enc:v1:"


@lru_cache(maxsize=1)
def _cipher(keys: str):
    from cryptography.fernet import Fernet, MultiFernet
    return MultiFernet([Fernet(k.strip().encode()) for k in keys.split(",") if k.strip()])


def cipher():
    keys = os.getenv("DATA_ENCRYPTION_KEY", "")
    return _cipher(keys) if keys else None


def enabled() -> bool:
    return cipher() is not None


class EncryptedText(TypeDecorator):
    """Texto cifrado en la base. `max_chars` es el largo máximo del texto en claro
    (lo usan los esquemas para validar, ya que el valor cifrado es más largo)."""
    impl = Text
    cache_ok = True

    def __init__(self, max_chars: Optional[int] = None):
        super().__init__()
        self.max_chars = max_chars

    def process_bind_param(self, value, dialect):
        c = cipher()
        if value is None or c is None or str(value).startswith(PREFIX):
            return value
        return PREFIX + c.encrypt(str(value).encode("utf-8")).decode("ascii")

    def process_result_value(self, value, dialect):
        if value is None or not value.startswith(PREFIX):
            return value
        c = cipher()
        if c is None:
            raise RuntimeError("Hay datos cifrados pero falta DATA_ENCRYPTION_KEY")
        return c.decrypt(value[len(PREFIX):].encode("ascii")).decode("utf-8")


def encrypted_columns(base) -> Dict[str, List[str]]:
    """{tabla: [columnas cifradas]} según los modelos."""
    out: Dict[str, List[str]] = {}
    for table in base.metadata.sorted_tables:
        cols = [c.name for c in table.columns if isinstance(c.type, EncryptedText)]
        if cols:
            out[table.name] = cols
    return out


def encrypt_existing(engine, base) -> int:
    """Cifra los valores que siguen en texto plano. Idempotente; devuelve cuántos cifró."""
    if not enabled():
        return 0
    total = 0
    with engine.begin() as conn:
        for table_name, cols in encrypted_columns(base).items():
            table = base.metadata.tables[table_name]
            for col in cols:
                # Lectura sin el TypeDecorator (texto crudo) para encontrar lo no cifrado
                rows = conn.execute(text(
                    f"SELECT id, {col} FROM {table_name} WHERE {col} IS NOT NULL AND {col} NOT LIKE :p"
                ), {"p": PREFIX + "%"}).fetchall()
                for row_id, raw in rows:
                    conn.execute(update(table).where(table.c.id == row_id).values({col: raw}))
                total += len(rows)
    if total:
        logger.info("Cifrados %s valores existentes", total)
    return total
