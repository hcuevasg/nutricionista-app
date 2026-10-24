"""Backups cifrados a R2: volcado, cifrado, restauración y retención."""
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import create_engine

import backup_r2
import models
from tests.conftest import engine_test
from tests.test_plantillas import _register
from tests.conftest import next_rut

KEY = Fernet.generate_key().decode()


class FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body, **_):
        # Fechas crecientes para que el orden no dependa de la resolución del reloj
        self.objects[Key] = {"Key": Key, "Body": Body, "Size": len(Body),
                             "LastModified": datetime.now(timezone.utc) + timedelta(seconds=len(self.objects))}

    def delete_object(self, Bucket, Key):
        del self.objects[Key]

    def get_paginator(self, _name):
        objects = self.objects

        class _P:
            def paginate(self, Bucket, Prefix):
                return [{"Contents": [o for k, o in objects.items() if k.startswith(Prefix)]}]
        return _P()


@pytest.fixture
def r2_env(monkeypatch):
    for k in backup_r2._ENV:
        monkeypatch.setenv(k, "x")
    monkeypatch.setenv("BACKUP_ENCRYPTION_KEY", KEY)
    monkeypatch.setattr(backup_r2.dump_database, "__defaults__", (engine_test,))


def test_dump_encrypt_restore_roundtrip(client, tmp_path):
    h = _register(client, "bk_user")
    pid = client.post("/patients", json={"rut": next_rut(), "name": "Ñandú Pérez", "sex": "F", "birth_date": "1990-01-02"},
                      headers=h).json()["id"]
    data = backup_r2.dump_database(engine_test)
    blob = backup_r2.encrypt(data, KEY)
    assert "Pérez".encode() not in blob
    with pytest.raises(InvalidToken):
        backup_r2.decrypt(blob, Fernet.generate_key().decode())

    target = create_engine(f"sqlite:///{tmp_path / 'restored.db'}")
    counts = backup_r2.restore_database(backup_r2.decrypt(blob, KEY), target)
    assert counts["patients"] >= 1
    from sqlalchemy.orm import Session
    with Session(target) as s:
        p = s.get(models.Patient, pid)
        assert p.name == "Ñandú Pérez" and isinstance(p.created_at, datetime)
        assert s.query(models.Nutritionist).filter_by(username="bk_user").one().password_hash
    with pytest.raises(ValueError, match="no está vacía"):
        backup_r2.restore_database(data, target)


def test_run_backup_retention_and_due(r2_env, monkeypatch):
    monkeypatch.setenv("BACKUP_KEEP", "2")
    s3 = FakeS3()
    assert backup_r2.configured()
    assert backup_r2.backup_due(s3)
    keys = []
    for i in range(3):
        monkeypatch.setattr(backup_r2, "datetime", _FixedDatetime(i))
        keys.append(backup_r2.run_backup(s3))
    monkeypatch.setattr(backup_r2, "datetime", datetime)
    assert sorted(s3.objects) == sorted(keys[1:])
    data = backup_r2.decrypt(s3.objects[keys[-1]]["Body"], KEY)
    assert data["format"] == backup_r2.DUMP_FORMAT
    assert not backup_r2.backup_due(s3)


def _FixedDatetime(i):
    class D(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 1, 0, 0, i, tzinfo=tz)
    return D
