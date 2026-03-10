"""
Backup manager — crea, lista, restaura y exporta copias de la base de datos.
"""
import os
import shutil
from datetime import datetime

# Rutas base
_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(_ROOT, "nutricionista.db")
BACKUPS_DIR = os.path.join(_ROOT, "backups")
MAX_BACKUPS = 30


def _ensure_dir():
    os.makedirs(BACKUPS_DIR, exist_ok=True)


# ── Crear backup ──────────────────────────────────────────────────────────────

def create_backup() -> str:
    """
    Copia la BD actual a /backups con nombre nutriapp_backup_YYYY-MM-DD_HH-MM.db.
    Elimina los backups más antiguos si superan MAX_BACKUPS.
    Devuelve la ruta del nuevo backup.
    """
    _ensure_dir()
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    dest = os.path.join(BACKUPS_DIR, f"nutriapp_backup_{ts}.db")
    shutil.copy2(DB_PATH, dest)
    _cleanup_old_backups()
    return dest


def _cleanup_old_backups():
    backups = _sorted_backups()
    while len(backups) > MAX_BACKUPS:
        oldest = backups.pop(0)
        try:
            os.remove(oldest["path"])
        except OSError:
            pass


# ── Listar backups ────────────────────────────────────────────────────────────

def _sorted_backups() -> list[dict]:
    """Devuelve lista de dicts ordenada de más antiguo a más reciente."""
    _ensure_dir()
    files = []
    for name in os.listdir(BACKUPS_DIR):
        if name.startswith("nutriapp_backup_") and name.endswith(".db"):
            path = os.path.join(BACKUPS_DIR, name)
            stat = os.stat(path)
            files.append({
                "name": name,
                "path": path,
                "size_kb": round(stat.st_size / 1024, 1),
                "mtime": stat.st_mtime,
            })
    files.sort(key=lambda x: x["mtime"])
    return files


def list_backups() -> list[dict]:
    """Devuelve lista de backups de más reciente a más antiguo."""
    return list(reversed(_sorted_backups()))


# ── Restaurar backup ──────────────────────────────────────────────────────────

def restore_backup(backup_path: str):
    """Reemplaza la BD actual con el backup indicado."""
    if not os.path.isfile(backup_path):
        raise FileNotFoundError(f"Backup no encontrado: {backup_path}")
    shutil.copy2(backup_path, DB_PATH)


# ── Exportar backup ───────────────────────────────────────────────────────────

def export_backup(backup_path: str, dest_path: str):
    """Copia un backup a una ubicación externa."""
    shutil.copy2(backup_path, dest_path)


# ── Importar backup externo ───────────────────────────────────────────────────

def import_and_restore(src_path: str) -> str:
    """
    Copia un .db externo a /backups, lo activa como BD actual y devuelve su ruta.
    """
    _ensure_dir()
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    dest = os.path.join(BACKUPS_DIR, f"nutriapp_backup_{ts}.db")
    shutil.copy2(src_path, dest)
    restore_backup(dest)
    _cleanup_old_backups()
    return dest
