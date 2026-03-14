"""Tests for auth endpoints."""


def test_register(client):
    resp = client.post("/auth/register", json={
        "username": "nuevo",
        "email": "nuevo@test.com",
        "password": "pass1234",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "nuevo"


def test_register_duplicate(client):
    payload = {"username": "dup", "email": "dup@test.com", "password": "pass1234"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400


def test_login_ok(client):
    client.post("/auth/register", json={
        "username": "loginuser", "email": "login@test.com", "password": "pass1234"
    })
    resp = client.post("/auth/login", json={"username": "loginuser", "password": "pass1234"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "username": "wrongpass", "email": "wp@test.com", "password": "pass1234"
    })
    resp = client.post("/auth/login", json={"username": "wrongpass", "password": "wrong"})
    assert resp.status_code == 401


def test_me(auth_client):
    resp = auth_client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_me_no_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code in (401, 403)
