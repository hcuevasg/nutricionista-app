"""Backups automáticos de toda la base, cifrados, a Cloudflare R2 (API compatible con S3).

Cada respaldo es un volcado JSON de todas las tablas (incluye cuentas y hashes
de contraseñas, para poder recuperar el servicio completo), comprimido con gzip
y cifrado con Fernet (AES-128-CBC + HMAC-SHA256). Sin la clave el archivo no
se puede leer: guárdala fuera de Railway (p. ej. en un gestor de contraseñas).

Variables de entorno (si falta alguna, los backups automáticos quedan apagados):
    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
    BACKUP_ENCRYPTION_KEY   clave Fernet (python backup_r2.py genkey)
Opcionales:
    BACKUP_INTERVAL_HOURS   cada cuánto respaldar (168 = semanal)
    BACKUP_KEEP             cuántos respaldos conservar (12)

Uso manual:
    python backup_r2.py genkey
    python backup_r2.py run                      # respalda ahora
    python backup_r2.py list
    python backup_r2.py download <key> <out.json>   # descarga y descifra
    python backup_r2.py restore <out.json>       # carga en una base VACÍA (DATABASE_URL)
"""
import asyncio
import gzip
import json
import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Date, DateTime, Engine, select, text

from database import Base, engine

logger = logging.getLogger("nutriapp.backup")

PREFIX = "nutriapp/"
DUMP_FORMAT = "nutriapp-db-dump"
_ENV = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "BACKUP_ENCRYPTION_KEY")


def configured() -> bool:
    return all(os.getenv(k) for k in _ENV)


# ── Volcado y restauración ───────────────────────────────────────────────────

def _jsonable(v: Any) -> Any:
    return v.isoformat() if isinstance(v, (datetime, date)) else v


def dump_database(eng: Engine = engine) -> Dict[str, Any]:
    tables: Dict[str, List[Dict[str, Any]]] = {}
    with eng.connect() as conn:
        for table in Base.metadata.sorted_tables:
            rows = conn.execute(select(table)).mappings().all()
            tables[table.name] = [{k: _jsonable(v) for k, v in r.items()} for r in rows]
    return {"format": DUMP_FORMAT, "version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(), "tables": tables}


def restore_database(data: Dict[str, Any], eng: Engine = engine) -> Dict[str, int]:
    """Carga un volcado en una base cuyas tablas estén vacías (nunca sobrescribe)."""
    if data.get("format") != DUMP_FORMAT:
        raise ValueError("El archivo no es un volcado de NutriApp")
    Base.metadata.create_all(bind=eng)
    counts: Dict[str, int] = {}
    with eng.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if conn.execute(select(table).limit(1)).first() is not None:
                raise ValueError(f"La tabla {table.name} no está vacía: restaura sobre una base nueva")
        for table in Base.metadata.sorted_tables:
            rows = data["tables"].get(table.name) or []
            for row in rows:
                values = {}
                for col in table.columns:
                    if col.name not in row:
                        continue
                    v = row[col.name]
                    if isinstance(v, str) and isinstance(col.type, DateTime):
                        v = datetime.fromisoformat(v)
                    elif isinstance(v, str) and isinstance(col.type, Date):
                        v = date.fromisoformat(v[:10])
                    values[col.name] = v
                conn.execute(table.insert().values(**values))
            counts[table.name] = len(rows)
            if eng.dialect.name == "postgresql" and rows and "id" in table.columns:
                conn.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                    f"(SELECT MAX(id) FROM {table.name}))"
                ))
    return counts


# ── Cifrado ──────────────────────────────────────────────────────────────────

def _fernet(key: Optional[str] = None):
    from cryptography.fernet import Fernet
    return Fernet((key or os.environ["BACKUP_ENCRYPTION_KEY"]).encode())


def encrypt(data: Dict[str, Any], key: Optional[str] = None) -> bytes:
    raw = gzip.compress(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    return _fernet(key).encrypt(raw)


def decrypt(blob: bytes, key: Optional[str] = None) -> Dict[str, Any]:
    return json.loads(gzip.decompress(_fernet(key).decrypt(blob)).decode("utf-8"))


# ── R2 ───────────────────────────────────────────────────────────────────────

def _client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def list_backups(client=None) -> List[Dict[str, Any]]:
    """Respaldos del bucket, del más reciente al más antiguo."""
    client = client or _client()
    items: List[Dict[str, Any]] = []
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=os.environ["R2_BUCKET"], Prefix=PREFIX):
        items.extend(page.get("Contents", []))
    return sorted(items, key=lambda o: o["LastModified"], reverse=True)


def run_backup(client=None) -> str:
    """Respalda la base completa y aplica la retención. Devuelve la key subida."""
    client = client or _client()
    bucket = os.environ["R2_BUCKET"]
    key = f"{PREFIX}backup_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json.gz.enc"
    client.put_object(Bucket=bucket, Key=key, Body=encrypt(dump_database()),
                      ContentType="application/octet-stream")
    keep = int(os.getenv("BACKUP_KEEP", "12"))
    for old in list_backups(client)[keep:]:
        client.delete_object(Bucket=bucket, Key=old["Key"])
    logger.info("Backup subido a R2: %s", key)
    return key


def backup_due(client=None) -> bool:
    backups = list_backups(client)
    if not backups:
        return True
    interval = timedelta(hours=float(os.getenv("BACKUP_INTERVAL_HOURS", "168")))
    return datetime.now(timezone.utc) - backups[0]["LastModified"] >= interval


async def scheduler(check_every: int = 3600) -> None:
    """Revisa cada hora si toca respaldar. El último backup vive en R2, así que
    los reinicios del servidor no reinician el plazo."""
    while True:
        try:
            if await asyncio.to_thread(backup_due):
                await asyncio.to_thread(run_backup)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Falló el backup automático a R2")
        await asyncio.sleep(check_every)


def _main(argv: List[str]) -> None:
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "genkey":
        from cryptography.fernet import Fernet
        print(Fernet.generate_key().decode())
    elif cmd == "run":
        print(run_backup())
    elif cmd == "list":
        for o in list_backups():
            print(f"{o['LastModified']:%Y-%m-%d %H:%M}  {o['Size'] / 1024:8.1f} KB  {o['Key']}")
    elif cmd == "download" and len(argv) == 4:
        body = _client().get_object(Bucket=os.environ["R2_BUCKET"], Key=argv[2])["Body"].read()
        with open(argv[3], "w", encoding="utf-8") as f:
            json.dump(decrypt(body), f, ensure_ascii=False)
        print(f"Descifrado en {argv[3]}")
    elif cmd == "restore" and len(argv) == 3:
        with open(argv[2], encoding="utf-8") as f:
            counts = restore_database(json.load(f))
        print(json.dumps(counts, indent=2))
        print("Luego marca el esquema: alembic stamp head")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    _main(sys.argv)
