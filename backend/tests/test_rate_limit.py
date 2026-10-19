"""Rate limiting por IP en rutas sensibles."""
import main


def test_portal_rate_limit(client, monkeypatch):
    monkeypatch.setattr(main, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(main, "_rate_store", main.defaultdict(list))
    headers = {"X-Forwarded-For": "1.1.1.1, 203.0.113.7"}
    codes = [client.get("/portal/token-inexistente", headers=headers).status_code for _ in range(61)]
    assert codes[:60] == [404] * 60
    assert codes[60] == 429


def test_spoofed_forwarded_prefix_does_not_bypass_limit(client, monkeypatch):
    monkeypatch.setattr(main, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(main, "_rate_store", main.defaultdict(list))
    codes = [
        client.post("/auth/login", json={"username": "x", "password": "y"},
                    headers={"X-Forwarded-For": f"10.0.0.{i}, 203.0.113.9"}).status_code
        for i in range(11)
    ]
    assert codes[-1] == 429


def test_authenticated_routes_not_limited(auth_client, monkeypatch):
    monkeypatch.setattr(main, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(main, "_rate_store", main.defaultdict(list))
    assert all(auth_client.get("/patients").status_code == 200 for _ in range(15))
