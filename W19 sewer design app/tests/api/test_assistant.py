"""The assistant without spending tokens: tool schemas, every tool on real data, the loop with a stand-in client, and
the no-key message. The live test runs only when ANTHROPIC_API_KEY is set (pytest -m live)."""
import os
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app, P
from sewerapp.assistant import runner, tools as T

C = TestClient(app)


def test_every_tool_schema_is_strict_and_closed():
    for t in T.definitions():
        s = t["input_schema"]
        assert t["strict"] and s["additionalProperties"] is False and set(s["required"]) == set(s["properties"]), t["name"]


def test_explain_pipe_on_the_join_over_its_limit():
    e = T.call(P, "explain_pipe", dict(scenario="SC1-2056", label="P1-P151"))
    dd = next(c for c in e["checks"] if "Table 10" in c["source"])
    assert not dd["ok"] and dd["value"] > 0.5 and dd["limit"] == 0.5


def test_explain_cites_p26_for_self_cleansing():
    q = T.call(P, "query_pipes", dict(scenario="SC1-2056", flag="under075", min_dn=250, max_dn=3000, sort="v2031_ms", limit=1))
    lab = q["rows"][0]["label"]
    e = T.call(P, "explain_pipe", dict(scenario="SC1-2056", label=lab))
    sc = next(c for c in e["checks"] if "self-cleansing" in c["rule"])
    assert sc["source"] == "PAM-GUD-203 p26" and not sc["ok"] and sc["value"] < 0.75


def test_make_whatif_never_edits_an_existing_scenario():
    before = P.results("SC1-2056")[1]
    w = T.call(P, "make_whatif", dict(scenario="SC1-2056", name="join upsized", edits=[dict(label="P1-P151", field="dn_mm", value=1200)]))
    assert w["scenario"] not in ("SC1-2056",) and w["edited"][0]["dn_mm"] == 1200 and not w["edited"][0]["over_limit"]
    assert P.results("SC1-2056")[1] == before


def test_lookup_criterion_finds_the_register():
    assert T.call(P, "lookup_criterion", dict(query="0.75"))["hits"]


def test_loop_with_the_stand_in(monkeypatch):
    monkeypatch.setenv("W19_ASSISTANT_STUB", "1")
    r = C.post("/api/assistant", json=dict(sid="SC1-2056", message="How much pipe misses self-cleansing?")).json()
    assert "9.01 km" in r["reply"] and r["tool_calls"][0]["name"] == "get_summary" and r["tool_calls"][0]["ok"]


def test_without_a_key_the_endpoint_says_so(monkeypatch):
    monkeypatch.delenv("W19_ASSISTANT_STUB", raising=False); monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = C.post("/api/assistant", json=dict(sid="SC1-2056", message="hi"))
    assert r.status_code == 503 and "ANTHROPIC_API_KEY" in r.json()["detail"]


@pytest.mark.live
@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="needs ANTHROPIC_API_KEY")
def test_live_answer_cites_the_page():
    r = runner.ask(P, "SC1-2056", "Why does pipe P1-P151 fail? Give its d/D, the limit and the guideline page.")
    print(r["usage"])
    assert "p27" in r["reply"] and any(c["name"] in ("explain_pipe", "get_pipe") for c in r["tool_calls"])
