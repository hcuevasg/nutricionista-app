"""IA de pautas: validación del menú y endpoints con Claude simulado."""
import json
from types import SimpleNamespace

import pytest

import ai_service

ITEM = {"nombre": "Avena cocida", "cantidad": 180, "unidad": "g",
        "kcal_100": 71, "prot_100": 2.5, "cho_100": 12.0, "lip_100": 1.4}
TIEMPO = {"opcion1": [ITEM], "opcion2": [ITEM]}

PAUTA = {
    "name": "Pauta IA", "date": "2026-03-01", "tipo_pauta": "omnivoro",
    "sexo": "F", "edad": 30, "peso": 60.0, "fa_key": "moderada",
    "tmb": 1300, "get_kcal": 2000, "kcal_objetivo": 2000,
    "prot_g_kg": 1.5, "prot_g": 90, "prot_kcal": 360, "prot_pct": 18,
    "lip_pct": 30, "lip_g": 67, "lip_kcal": 600,
    "cho_g": 260, "cho_kcal": 1040, "cho_pct": 52, "porciones_json": "{}",
    "distribucion_json": json.dumps({"desayuno": {"cereales": 2}, "cena": {"carnes_bg": 1}, "once": {}}),
}


# ── Validación ──────────────────────────────────────────────────────────────

def test_parse_menu_valid():
    menu = ai_service.parse_menu(json.dumps({"desayuno": TIEMPO, "cena": TIEMPO}), ["desayuno", "cena"])
    assert menu["cena"]["opcion1"][0]["nombre"] == "Avena cocida"


@pytest.mark.parametrize("data", [
    {"desayuno": TIEMPO},                                         # falta un tiempo
    {"desayuno": TIEMPO, "cena": TIEMPO, "almuerzo": TIEMPO},      # tiempo extra
    {"desayuno": TIEMPO, "cena": {"opcion1": [], "opcion2": [ITEM]}},           # opción vacía
    {"desayuno": TIEMPO, "cena": {"opcion1": [{**ITEM, "kcal_100": -5}], "opcion2": [ITEM]}},
    {"desayuno": TIEMPO, "cena": {"opcion1": [{**ITEM, "unidad": "taza"}], "opcion2": [ITEM]}},
])
def test_parse_menu_rejects_invalid(data):
    with pytest.raises(ValueError):  # pydantic.ValidationError hereda de ValueError
        ai_service.parse_menu(json.dumps(data), ["desayuno", "cena"])


def test_build_menu_request_uses_only_active_tiempos():
    pauta = SimpleNamespace(**PAUTA)
    req = ai_service.build_menu_request(pauta, json.dumps(["Maní"]))
    assert req.tiempos == ["desayuno", "cena"]
    assert "Maní" in req.prompt
    assert ai_service.menu_schema(req.tiempos)["required"] == ["desayuno", "cena"]


def test_build_menu_request_without_distribution():
    pauta = SimpleNamespace(**{**PAUTA, "distribucion_json": "{}"})
    with pytest.raises(ai_service.AIError) as exc:
        ai_service.build_menu_request(pauta, None)
    assert exc.value.status_code == 400


# ── Streaming contra un cliente simulado ────────────────────────────────────

class _FakeStream:
    def __init__(self, chunks, stop_reason="end_turn"):
        self._chunks = chunks
        self._stop = stop_reason

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @property
    def text_stream(self):
        async def gen():
            for c in self._chunks:
                yield c
        return gen()

    async def get_final_message(self):
        return SimpleNamespace(stop_reason=self._stop, stop_details=None)


def _fake_client(responses, calls):
    def stream(**kwargs):
        calls.append(kwargs)
        return responses.pop(0)
    return SimpleNamespace(messages=SimpleNamespace(stream=stream))


@pytest.fixture
def anthropic_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)


async def _collect(req):
    return [e async for e in ai_service.stream_menu(req)]


def _run(coro):
    import asyncio
    return asyncio.new_event_loop().run_until_complete(coro)


def test_stream_menu_progress_schema_and_model(anthropic_key, monkeypatch):
    raw = json.dumps({"desayuno": TIEMPO, "cena": TIEMPO})
    calls = []
    monkeypatch.setattr(ai_service, "_client", lambda: _fake_client([_FakeStream([raw[:60], raw[60:]])], calls))
    req = ai_service.MenuRequest(prompt="p", tiempos=["desayuno", "cena"])
    events = _run(_collect(req))
    assert events[-1]["type"] == "menu"
    assert {"type": "progress", "done": 2, "total": 2} in events
    assert calls[0]["model"] == "claude-haiku-5-5"
    assert calls[0]["output_config"]["format"]["schema"]["required"] == ["desayuno", "cena"]


def test_stream_menu_retries_once_on_invalid_json(anthropic_key, monkeypatch):
    good = json.dumps({"desayuno": TIEMPO})
    calls = []
    monkeypatch.setattr(ai_service, "_client",
                        lambda: _fake_client([_FakeStream(['{"desayuno": {}}']), _FakeStream([good])], calls))
    events = _run(_collect(ai_service.MenuRequest(prompt="p", tiempos=["desayuno"])))
    assert len(calls) == 2
    assert events[-1]["menu"]["desayuno"]["opcion2"][0]["unidad"] == "g"


def test_stream_menu_refusal(anthropic_key, monkeypatch):
    monkeypatch.setattr(ai_service, "_client",
                        lambda: _fake_client([_FakeStream([""], stop_reason="refusal")], []))
    with pytest.raises(ai_service.AIError) as exc:
        _run(_collect(ai_service.MenuRequest(prompt="p", tiempos=["desayuno"])))
    assert exc.value.status_code == 422


def test_model_configurable(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    assert ai_service.model_name() == "claude-sonnet-5-5"


# ── Endpoints ───────────────────────────────────────────────────────────────

@pytest.fixture
def pauta_ids(auth_client):
    pid = auth_client.post("/patients", json={"name": "IA", "sex": "F"}).json()["id"]
    pauta_id = auth_client.post(f"/pautas?patient_id={pid}", json=PAUTA).json()["id"]
    return pid, pauta_id


def test_endpoints_without_key_return_503(auth_client, pauta_ids, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    pid, pauta_id = pauta_ids
    assert auth_client.get("/pautas/ai-status").json()["configured"] is False
    assert auth_client.post(f"/pautas/{pid}/{pauta_id}/generar-menu").status_code == 503
    assert auth_client.get(f"/pautas/{pid}/{pauta_id}/generar-menu-stream").status_code == 503


def test_generar_menu_persists(auth_client, pauta_ids, anthropic_key, monkeypatch):
    pid, pauta_id = pauta_ids
    menu = {"desayuno": TIEMPO, "cena": TIEMPO}

    async def fake_generate(req):
        assert req.tiempos == ["desayuno", "cena"]
        return menu
    monkeypatch.setattr(ai_service, "generate_menu", fake_generate)
    resp = auth_client.post(f"/pautas/{pid}/{pauta_id}/generar-menu")
    assert resp.status_code == 200
    assert json.loads(auth_client.get(f"/pautas/{pid}/{pauta_id}").json()["menu_json"]) == menu


def test_generar_menu_stream_events(auth_client, pauta_ids, anthropic_key, monkeypatch):
    pid, pauta_id = pauta_ids

    async def fake_stream(req):
        yield {"type": "progress", "done": 1, "total": 2}
        yield {"type": "menu", "menu": {"desayuno": TIEMPO, "cena": TIEMPO}}
    monkeypatch.setattr(ai_service, "stream_menu", fake_stream)
    body = auth_client.get(f"/pautas/{pid}/{pauta_id}/generar-menu-stream").text
    assert "1 de 2 tiempos" in body
    assert "event: result" in body


def test_ai_suggest_error_is_generic(auth_client, pauta_ids, anthropic_key, monkeypatch):
    pid, pauta_id = pauta_ids

    async def failing(pauta, evals):
        raise ai_service.AIError("Se alcanzó el límite de uso de la IA. Intenta en unos minutos.", 429)
    monkeypatch.setattr(ai_service, "suggest_adjustments", failing)
    resp = auth_client.post(f"/pautas/{pid}/{pauta_id}/ai-suggest")
    assert resp.status_code == 429
    assert "límite" in resp.json()["detail"]
