"""Alembic: la cadena de migraciones aplica y deja el esquema igual a los modelos."""
import os
import subprocess
import sys


def _alembic(db_path, *args):
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}"}
    return subprocess.run([sys.executable, "-m", "alembic", "-c", "alembic.ini", *args],
                          cwd=os.path.dirname(os.path.dirname(__file__)), env=env,
                          capture_output=True, text=True)


def test_upgrade_on_legacy_schema_without_new_columns(tmp_path):
    db = tmp_path / "legacy.db"
    # Base "antigua": tablas de los modelos pero sin las columnas de metas
    code = (
        "import models; from database import Base, engine; from sqlalchemy import text;"
        "Base.metadata.create_all(engine);"
        "c = engine.connect();"
        "c.execute(text('ALTER TABLE anthropometrics DROP COLUMN goals_text'));"
        "c.execute(text('ALTER TABLE anthropometrics DROP COLUMN next_eval_date'));"
        "c.commit()"
    )
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}"}
    subprocess.run([sys.executable, "-c", code], cwd=os.path.dirname(os.path.dirname(__file__)),
                   env=env, check=True, capture_output=True)
    up = _alembic(db, "upgrade", "head")
    assert up.returncode == 0, up.stderr
    check = _alembic(db, "check")
    assert check.returncode == 0, check.stdout + check.stderr
    assert "0002_metas_evaluacion" in _alembic(db, "current").stdout
