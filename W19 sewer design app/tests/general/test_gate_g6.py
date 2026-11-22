"""Gate G6 (the assistant on any project): every tool on a drawn project and on an imported model, schemas strict,
existing scenarios never changed, the loop end to end with the stand-in client; a live question when the key is set."""
import json, os
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app
from sewerapp.api.general_api import SESSIONS
from sewerapp.assistant import gtools, runner

C = TestClient(app)


@pytest.fixture()
def pid():
    p = C.post("/api/g/projects/new", json=dict(name="assistant test")).json()["id"]
    for i, (x, g) in enumerate([(0, 100.0), (100, 99.5), (200, 99.0)]):
        C.post(f"/api/g/projects/{p}/scenarios/base/edit", json=dict(op="add_node", id=f"MH{i+1}", kind="manhole" if i < 2 else "outfall", x=x, y=0, ground=g, invert=g - 2))
    for a, b in (("MH1", "MH2"), ("MH2", "MH3")):
        C.post(f"/api/g/projects/{p}/scenarios/base/edit", json=dict(op="add_link", from_node=a, to_node=b))
    C.post(f"/api/g/projects/{p}/scenarios/base/edit", json=dict(op="set_load", set="design", node="MH1", value=6000.0))
    return p


@pytest.mark.gate_g6
def test_tool_schemas_are_strict_and_closed():
    for t in gtools.definitions():
        s = t["input_schema"]; assert t["strict"] and s["additionalProperties"] is False and set(s["required"]) == set(s["properties"])


@pytest.mark.gate_g6
def test_every_tool_on_a_drawn_project(pid):
    call = lambda n, **a: gtools.call(None, n, a)
    assert any(p["id"] == pid for p in call("list_projects"))
    s = call("project_summary", project=pid, scenario="base"); assert s["summary"]["over_limit"] >= 1
    q = call("query_links", project=pid, scenario="base", flag="any_failing", min_dn=0, max_dn=5000, sort="d_over_D", limit=5)
    assert q["count"] >= 1
    e = call("explain_link", project=pid, scenario="base", id=q["rows"][0]["id"])
    assert any(c["source"].startswith("PAM-GUD-203 p27") and not c["ok"] for c in e["checks"])
    assert call("get_element", project=pid, scenario="base", table="links", id="P-1")["results"]["q_ls"] > 0
    m = call("make_scenario", project=pid, scenario="base", name="upsize",
             edits=[dict(op="set", args=json.dumps(dict(table="links", ids=["P-1", "P-2"], field="dn_mm", value=630)))])
    assert m["scenario"] != "base" and m["summary"]["over_limit"] < s["summary"]["over_limit"]
    d = call("design_scenario", project=pid, scenario="base", name="designed")
    assert d["summary"]["over_limit"] == 0 and d["report"]["sizes_changed"] >= 1
    assert call("project_summary", project=pid, scenario="base")["summary"]["over_limit"] == s["summary"]["over_limit"]   # base untouched
    assert call("lookup_criterion", query="Table 11 DN200")["current_values"]


@pytest.mark.gate_g6
def test_storm_tool_on_an_imported_model():
    f = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "swmm", "examples", "Example1.inp")
    p = C.post("/api/g/projects/import", files=dict(file=("Example1.inp", open(f, "rb").read()))).json()["id"]
    r = gtools.call(None, "storm_scenario", dict(project=p, scenario="base", top=3))
    assert len(r["links"]) == 3 and r["summary"]["subcatchments"] == 8


@pytest.mark.gate_g6
def test_loop_with_the_stand_in(pid, monkeypatch):
    monkeypatch.setenv("W19_ASSISTANT_STUB", "1")
    r = C.post("/api/g/assistant", json=dict(project=pid, scenario="base", message="What fails?")).json()
    assert r["tool_calls"][0]["name"] == "project_summary" and r["tool_calls"][0]["ok"] and "over the d/D limit" in r["reply"]


@pytest.mark.live
@pytest.mark.skipif(not runner._key(), reason="needs ANTHROPIC_API_KEY")
def test_live_on_a_drawn_project(pid):
    r = runner.ask(None, "base", "Which pipes fail and why? Then design it in a new scenario and say what changed.", toolset=gtools,
                   system=runner.SYSTEM_GENERAL, context=f"active project: {pid}, scenario: base", model="sonnet")
    print(r["usage"]); names = [c["name"] for c in r["tool_calls"]]
    assert "design_scenario" in names and "p27" in r["reply"]
    assert SESSIONS[pid].scenarios["base"].edits[-1]["op"] == "set_load"                  # base untouched
