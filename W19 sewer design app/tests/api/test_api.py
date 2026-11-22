"""The API end to end through FastAPI's test client: load, edit a what-if, instant re-run, undo/redo, compare,
profile, exports, tools."""
import io, json
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app

C = TestClient(app)


def test_scenarios_and_results():
    s = C.get("/api/scenarios").json(); assert len(s) == 12 and all(x["read_only"] for x in s)
    r = C.get("/api/scenarios/SC1-2056/results").json()
    assert r["summary"]["pipes"] == 19083 and r["summary"]["km_under075_2031"] == 9.01
    assert len(r["columns"]["v_ms"]) == 19083


def test_geometry():
    g = C.get("/api/geometry/SC1-2056").json()
    assert len(g["pipes"]["features"]) == 19083 and 56 < g["bounds"][0] < 58   # WGS84, Oman


def test_base_case_is_read_only():
    assert C.post("/api/scenarios/SC1-2056/edits", json=dict(target="pipe", ids=[0], field="dn_mm", value=250)).status_code == 400


def test_edit_rerun_undo_redo_compare():
    w = C.post("/api/scenarios/SC1-2056/copy", json={}).json()["id"]
    before = C.get(f"/api/scenarios/{w}/pipes/100").json()
    s = C.post(f"/api/scenarios/{w}/edits", json=dict(target="pipe", ids=[100], field="dn_mm", value=250)).json()
    assert s["needs_relay"] > 0 and s["seconds"] < 1.0                      # instant re-run
    after = C.get(f"/api/scenarios/{w}/pipes/100").json()
    assert after["dn_mm"] == 250 and after["v_ms"] != before["v_ms"] and after["needs_relay"]
    cmp = C.get(f"/api/compare?a=SC1-2056&b={w}").json(); assert cmp["changed"] >= 1
    assert C.post(f"/api/scenarios/{w}/undo").json()["needs_relay"] == 0
    assert C.post(f"/api/scenarios/{w}/redo").json()["needs_relay"] > 0
    s = C.post(f"/api/scenarios/{w}/edits", json=dict(target="node", ids=[35], field="load_factor", value=2.0)).json()
    assert s["pipes"] == 19083


def test_profile_runs_to_the_outfall():
    p = C.get("/api/scenarios/SC1-2056/profile", params=dict(start="P4L8-M38")).json()
    assert len(p) > 3 and p[0]["ch0"] == 0 and all(r["inv0"] < r["ground0"] for r in p)


def test_exports():
    import geopandas as gpd, ezdxf, tempfile, os
    g = C.get("/api/scenarios/SC1-2056/export.gpkg"); assert g.status_code == 200
    f = os.path.join(tempfile.mkdtemp(), "x.gpkg"); open(f, "wb").write(g.content)
    assert len(gpd.read_file(f, layer="pipes")) == 19083
    d = C.get("/api/scenarios/SC1-2056/export.dxf"); assert ezdxf.read(io.StringIO(d.text)).modelspace()
    assert C.get("/api/scenarios/SC1-2056/export.csv").text.startswith("label,")


@pytest.mark.parametrize("tool", ["checks", "selfcleansing", "stations", "quantities", "compare_sewergems", "swmm_examples"])
def test_quick_tools(tool):
    r = C.post(f"/api/tools/{tool}", params=dict(sid="SC1-2056")); assert r.status_code == 200, r.text
    if tool == "compare_sewergems": assert r.json()["pc_within_0_1"] == 100.0
