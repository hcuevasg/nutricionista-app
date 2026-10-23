"""Validación de entradas, límites de tamaño, archivos y headers de seguridad."""
import base64
import io

from PIL import Image

from tests.test_plantillas import _register


def _png(size=(300, 120)):
    b = io.BytesIO()
    Image.new("RGB", size, "green").save(b, "PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def test_request_body_size_limit(client):
    h = _register(client, "hard_size")
    big = "x" * (1024 * 1024 + 10)
    r = client.post("/patients", content=f'{{"name": "{big}", "sex": "F"}}',
                    headers={**h, "Content-Type": "application/json"})
    assert r.status_code == 413
    r = client.post("/patients", content=iter([b'{"name": "A", "sex": "F"}']),
                    headers={**h, "Content-Type": "application/json"})
    assert r.status_code == 411


def test_text_longer_than_column_is_rejected(client):
    h = _register(client, "hard_len")
    assert client.post("/patients", json={"name": "N" * 256, "sex": "F"}, headers=h).status_code == 422
    assert client.post("/patients", json={"name": "Ana", "sex": "F", "phone": "9" * 21}, headers=h).status_code == 422
    assert client.post("/patients", json={"name": "Ana", "sex": "F", "phone": "+56 9 1234 5678"}, headers=h).status_code == 200


def test_logo_is_validated_and_reencoded(client):
    h = _register(client, "hard_logo")
    ok = client.put("/auth/profile", json={"logo_base64": _png()}, headers=h)
    assert ok.status_code == 200 and ok.json()["logo_base64"].startswith("data:image/png;base64,")
    svg = "data:image/svg+xml;base64," + base64.b64encode(b"<svg onload='alert(1)'/>").decode()
    assert client.put("/auth/profile", json={"logo_base64": svg}, headers=h).status_code == 422
    fake = "data:image/png;base64," + base64.b64encode(b"<script>alert(1)</script>").decode()
    assert client.put("/auth/profile", json={"logo_base64": fake}, headers=h).status_code == 422
    # "" quita el logo
    assert client.put("/auth/profile", json={"logo_base64": ""}, headers=h).json()["logo_base64"] is None


def test_security_headers_and_cors(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["cache-control"] == "no-store"
    assert "default-src 'none'" in r.headers["content-security-policy"]
    evil = client.options("/patients", headers={"Origin": "https://evil.example",
                                                "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in evil.headers
    good = client.options("/patients", headers={"Origin": "https://nutricionista-app.vercel.app",
                                                "Access-Control-Request-Method": "GET"})
    assert good.headers["access-control-allow-origin"] == "https://nutricionista-app.vercel.app"


def test_unhandled_error_keeps_cors_headers(client):
    r = client.post("/patients", json={"name": "A" * 300, "sex": "F"},
                    headers={"Origin": "https://nutricionista-app.vercel.app"})
    assert r.headers.get("access-control-allow-origin") == "https://nutricionista-app.vercel.app"
