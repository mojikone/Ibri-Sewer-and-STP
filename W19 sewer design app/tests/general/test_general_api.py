"""The general app through its API: a network built from a blank project, solved and checked by hand; every edit op;
undo/redo; scenarios inherit; save and open; the Ibri sample opens and re-solves after an edit."""
import io, math
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app

C = TestClient(app)
G, NU, KS = 9.81, 1.141e-6, 1.5e-3


def _v_cw(Q, D, S):   # independent scalar normal-depth velocity (Colebrook-White), the hand calculation
    def sec(y):
        th = 2 * math.acos(1 - 2 * y / D); A = D * D / 8 * (th - math.sin(th)); return A, A / (D * th / 2)
    lo, hi = 1e-6 * D, 0.999 * D
    for _ in range(60):
        y = (lo + hi) / 2; A, R = sec(y); a = math.sqrt(8 * G * R * S)
        v = -2 * a * math.log10(KS / (14.8 * R) + 2.51 * NU / (4 * R * a))
        hi, lo = (y, lo) if A * v > Q else (hi, y)
    A, _ = sec((lo + hi) / 2); return Q / A


def ed(pid, sid, **e):
    r = C.post(f"/api/g/projects/{pid}/scenarios/{sid}/edit", json=e); assert r.status_code == 200, r.text; return r.json()


@pytest.fixture()
def built():
    pid = C.post("/api/g/projects/new", json=dict(name="Hand check")).json()["id"]
    for i, (x, g) in enumerate([(0, 100.0), (100, 99.5), (200, 99.0)]):
        ed(pid, "base", op="add_node", id=f"MH{i+1}", kind="manhole", x=x, y=0, ground=g, invert=g - 2.0)
    ed(pid, "base", op="add_node", id="OUT", kind="outfall", x=300, y=0, ground=98.5, invert=96.5)
    for a, b in (("MH1", "MH2"), ("MH2", "MH3"), ("MH3", "OUT")):
        ed(pid, "base", op="add_link", from_node=a, to_node=b, dn_mm=200)
    ed(pid, "base", op="set_setting", path="peaking.method", value="constant")
    ed(pid, "base", op="set_setting", path="peaking.constant", value=2.5)
    ed(pid, "base", op="set_load", set="design", node="MH1", value=86.4)
    ed(pid, "base", op="set_load", set="design", node="MH2", value=172.8)
    return pid


def test_blank_project_network_against_hand_calculation(built):
    r = C.get(f"/api/g/projects/{built}/scenarios/base/results").json()
    L = r["links"]; assert r["summary"]["problems"] == [] and len(L) == 3
    # flow = 2.5 x cumulative load + 0.72 m3/d/km x cumulative length (G201 p72)
    q = {"P-1": 2.5 * 86.4 + 0.072, "P-2": 2.5 * 259.2 + 0.144, "P-3": 2.5 * 259.2 + 0.216}
    for lid, qq in q.items():
        assert abs(L[lid]["q_ls"] - qq / 86.4) < 1e-4, (lid, L[lid]["q_ls"], qq / 86.4)
        v = _v_cw(qq / 86400, 0.1764, 0.005)                      # 0.5 m fall in 100 m, DN200 inside 176.4 mm
        assert abs(L[lid]["v_ms"] - v) < 1e-3, (lid, L[lid]["v_ms"], v)


def test_edit_ops_undo_redo_and_scenarios(built):
    base = C.get(f"/api/g/projects/{built}/scenarios/base/results").json()["links"]["P-2"]["v_ms"]
    sc = C.post(f"/api/g/projects/{built}/scenarios/base/copy", json=dict(name="upsize")).json()["created"]
    ed(built, sc, op="set", table="links", ids=["P-2"], field="dn_mm", value=315)
    r = C.get(f"/api/g/projects/{built}/scenarios/{sc}/results").json()["links"]["P-2"]
    assert r["dn_mm"] == 315 and r["v_ms"] != base
    assert C.get(f"/api/g/projects/{built}/scenarios/base/results").json()["links"]["P-2"]["dn_mm"] == 200   # base untouched
    C.post(f"/api/g/projects/{built}/scenarios/{sc}/undo")
    assert C.get(f"/api/g/projects/{built}/scenarios/{sc}/results").json()["links"]["P-2"]["dn_mm"] == 200
    C.post(f"/api/g/projects/{built}/scenarios/{sc}/redo")
    assert C.get(f"/api/g/projects/{built}/scenarios/{sc}/results").json()["links"]["P-2"]["dn_mm"] == 315
    ed(built, sc, op="move_node", id="MH2", x=100, y=50)            # moving a node re-lengths its links
    m = C.get(f"/api/g/projects/{built}/scenarios/{sc}/model").json()
    p1 = next(f for f in m["links"]["features"] if f["id"] == "P-1")["properties"]
    assert abs(p1["length_m"] - math.hypot(100, 50)) < 1e-6
    ed(built, sc, op="split_link", id="P-3", x=250, y=0)
    m = C.get(f"/api/g/projects/{built}/scenarios/{sc}/model").json()
    ids = {f["id"] for f in m["links"]["features"]}; assert {"P-3-a", "P-3-b"} <= ids and "P-3" not in ids
    ed(built, sc, op="delete", table="nodes", ids=["MH1"])           # deletes its link too
    m = C.get(f"/api/g/projects/{built}/scenarios/{sc}/model").json()
    assert "P-1" not in {f["id"] for f in m["links"]["features"]}
    assert C.post(f"/api/g/projects/{built}/scenarios/{sc}/edit", json=dict(op="add_link", from_node="X", to_node="OUT")).status_code == 400


def test_drawing_in_lon_lat_on_a_local_project(built):
    ed(built, "base", op="add_node", id="MH9", lon=500 / 111319.49, lat=0.0, ground=97.0)
    m = C.get(f"/api/g/projects/{built}/scenarios/base/model").json()
    f = next(f for f in m["nodes"]["features"] if f["id"] == "MH9")
    assert abs(f["properties"]["x"] - 500) < 1e-6 and f["properties"]["invert"] == 95.5   # ground - 1.5 m by default


def test_save_and_open(built, tmp_path):
    g = C.get(f"/api/g/projects/{built}/save"); assert g.status_code == 200
    o = C.post("/api/g/projects/open", files=dict(file=("x.gpkg", g.content))).json()
    a = C.get(f"/api/g/projects/{built}/scenarios/base/results").json()["links"]
    b = C.get(f"/api/g/projects/{o['id']}/scenarios/base/results").json()["links"]
    assert a == b


def test_ibri_sample_opens_edits_and_profiles():
    pid = C.post("/api/g/projects/sample/SC1-2056").json()["id"]
    r = C.get(f"/api/g/projects/{pid}/scenarios/base/results").json()
    assert r["summary"]["conduits"] >= 19083 and r["summary"]["problems"] == []
    sc = C.post(f"/api/g/projects/{pid}/scenarios/base/copy", json={}).json()["created"]
    s = ed(pid, sc, op="set", table="links", ids=["P1-P151"], field="dn_mm", value=1200)
    assert s["summary"]["seconds"] < 2.0
    assert not C.get(f"/api/g/projects/{pid}/scenarios/{sc}/results").json()["links"]["P1-P151"]["over_limit"]
    p = C.get(f"/api/g/projects/{pid}/scenarios/base/profile", params=dict(start="P4L8-M38")).json()
    assert len(p) > 3 and all(x["inv0"] < x["ground0"] for x in p)
