"""Búsqueda de alimentos: base local primero, USDA como respaldo."""
import pytest

from routers import alimentos


@pytest.fixture
def seeded(db, monkeypatch):
    alimentos.seed_alimentos(db)
    calls = []

    async def fake_usda(q, limit):
        calls.append((q, limit))
        return [{"fdcId": 1, "nombre": "USDA food", "fuente": "usda"}]
    monkeypatch.setattr(alimentos, "_search_usda", fake_usda)
    return calls


def test_seed_is_idempotent(db):
    alimentos.seed_alimentos(db)
    assert alimentos.seed_alimentos(db) == 0


def test_search_without_accents_finds_local(auth_client, seeded):
    res = auth_client.get("/alimentos/search", params={"q": "platano"}).json()
    assert any(r["nombre"].lower().startswith("plátano") for r in res)
    assert all(r["fuente"] in ("base", "chile", "usda") for r in res)


def test_chilean_foods_and_no_usda_when_enough(auth_client, seeded):
    res = auth_client.get("/alimentos/search", params={"q": "pan"}).json()
    assert len(res) >= 5
    assert not seeded  # suficientes resultados locales: no se consulta USDA
    assert any(r["fuente"] == "chile" for r in res)


def test_multiword_and_english_name(auth_client, seeded):
    res = auth_client.get("/alimentos/search", params={"q": "arroz cocido"}).json()
    assert res and all("arroz" in alimentos.normalize(r["nombre"]) for r in res if r["fuente"] != "usda")
    res_en = auth_client.get("/alimentos/search", params={"q": "chilean bread"}).json()
    assert any(r["fuente"] == "chile" for r in res_en)


def test_falls_back_to_usda(auth_client, seeded):
    res = auth_client.get("/alimentos/search", params={"q": "zzzz inexistente"}).json()
    assert seeded and res[-1]["fuente"] == "usda"
