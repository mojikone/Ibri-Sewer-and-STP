"""The assistant's daily spending limit per client (2026-11-23 v5)."""
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app
from sewerapp.assistant import budget

C = TestClient(app)
WEB = {"cf-connecting-ip": "203.0.113.7"}


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setenv("W19_ASSISTANT_STUB", "1")
    monkeypatch.setattr(budget, "LIMITS_FILE", str(tmp_path / "limits.json")); monkeypatch.setattr(budget, "LEDGER_FILE", str(tmp_path / "ledger.json"))
    pid = C.post("/api/g/projects/new", json=dict(name="b", crs=32640)).json()["id"]
    return pid


def _ask(pid, headers=None):
    return C.post("/api/g/assistant", json=dict(project=pid, scenario="base", message="how many pipes?"), headers=headers or {})


def test_cost_at_list_prices():
    u = dict(input_tokens=1_000_000, output_tokens=100_000, cache_write_tokens=0, cache_read_tokens=1_000_000)
    assert budget.cost("claude-opus-5-5", u) == pytest.approx(4.0 + 2.0 + 0.2)
    assert budget.cost("claude-sonnet-5-5", u) == pytest.approx(2.0 + 1.0 + 0.1)


def test_each_answer_is_charged_and_the_limit_stops_the_next(files):
    pid = files
    r = _ask(pid, WEB).json()
    assert r["usage"]["usd"] > 0 and r["budget"]["client"] == "shared link visitor"
    s = C.get("/api/g/assistant/usage", headers=WEB).json()
    assert s["spent_today_usd"] == pytest.approx(r["usage"]["usd"], abs=1e-4) and s["limits"] is None      # a visitor does not see the limits
    assert C.post("/api/g/assistant/limits", json=dict(web_daily_usd=0.0), headers=WEB).status_code == 403
    assert C.post("/api/g/assistant/limits", json=dict(web_daily_usd=0.0)).status_code == 200           # from this computer
    assert _ask(pid, WEB).status_code == 429
    assert _ask(pid).status_code == 200                                                              # this computer has its own limit


def test_all_visitors_together_and_bad_limits(files):
    pid = files
    C.post("/api/g/assistant/limits", json=dict(web_daily_usd=5.0, web_all_daily_usd=0.0))
    assert _ask(pid, {"cf-connecting-ip": "198.51.100.9"}).status_code == 429
    assert C.post("/api/g/assistant/limits", json=dict(local_daily_usd=-1)).status_code == 400
