"""Registro interno de errores."""
import pytest

import error_log
from main import app
from tests.conftest import TestingSessionLocal
from tests.test_plantillas import _register


async def _boom():
    raise RuntimeError("fallo de prueba [parameters: ('Juan Pérez', '12.345.678-9')]")

app.add_api_route("/__test_boom", _boom, methods=["GET"])


@pytest.fixture(autouse=True)
def _error_log_db(monkeypatch):
    monkeypatch.setattr(error_log, "SessionLocal", TestingSessionLocal)


def test_unhandled_error_is_logged_without_sensitive_params(client):
    a, b = _register(client, "err_a"), _register(client, "err_b")
    r = client.get("/__test_boom?search=Juan", headers=a)
    assert r.status_code == 500
    assert r.json()["detail"].startswith("Error interno del servidor (ref.")
    logs = client.get("/settings/error-logs", headers=a).json()["errors"]
    assert logs[0]["source"] == "backend" and logs[0]["error_type"] == "RuntimeError"
    assert logs[0]["path"] == "/__test_boom"
    assert "Juan" not in logs[0]["message"] and "omitidos" in logs[0]["message"]
    assert "Traceback" in logs[0]["stack"]
    assert client.get("/settings/error-logs", headers=b).json()["errors"] == []


def test_frontend_error_report(client):
    a = _register(client, "err_front")
    r = client.post("/errors/report", json={"message": "TypeError: x is undefined", "stack": "at Foo",
                                            "path": "/patients/3?tab=1"}, headers=a)
    assert r.status_code == 204
    e = client.get("/settings/error-logs", headers=a).json()["errors"][0]
    assert e["source"] == "frontend" and e["path"] == "/patients/3"
    # Sin sesión también se acepta (errores en el login), sin asociarlo a nadie
    assert client.post("/errors/report", json={"message": "anon"}).status_code == 204
