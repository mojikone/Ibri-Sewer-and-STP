"""The faults the final Fable 5.2 review found in v3 (2026-11-23), each as a test."""
import math
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app
from sewerapp.engine import pressure as P, steady, storm, validate
from sewerapp.io import swmm_inp
from sewerapp.model.general import Project
from sewerapp.model import workspace as W


def _two_stations():
    """Two wet wells (50 and 20 L/s) pump into one junction; one main on to a manhole."""
    p = Project("two", crs=32640)
    for nid, kind, x, g, inv in (("A", "manhole", 0, 104, 102), ("WA", "wetwell", 10, 104, 99), ("B", "manhole", 0, 104, 102), ("WB", "wetwell", 10, 104, 99),
                                 ("J", "pressure_junction", 20, 104, 102), ("R", "manhole", 1020, 117, 115), ("O", "outfall", 1100, 116, 114)):
        W.apply(p, dict(op="add_node", id=nid, kind=kind, x=x, y=0 if nid[-1] != "B" else 50, ground=g, invert=inv))
    for lid, k, a, b in (("GA", "conduit", "A", "WA"), ("GB", "conduit", "B", "WB"), ("PA", "pump", "WA", "J"), ("PB", "pump", "WB", "J"),
                         ("FM", "pressure_pipe", "J", "R"), ("G2", "conduit", "R", "O")):
        W.apply(p, dict(op="add_link", id=lid, kind=k, from_node=a, to_node=b, dn_mm=315))
    p.links.loc["FM", ["inside_mm", "length_m"]] = [300.0, 1000.0]
    p.load_sets["design"] = {"A": 4320.0, "B": 1728.0}                       # 50 and 20 L/s
    p.settings["peaking"]["method"] = "constant"; p.settings["infiltration_m3d_per_km"] = 0.0
    return p


def test_a_shared_force_main_carries_both_pumps():
    r, _ = steady.solve(_two_stations())
    assert r.q_ls["FM"] == pytest.approx(70.0)
    assert r.hf_m["FM"] == pytest.approx(P.headloss("hazen", 0.07, 0.3, 1000.0), rel=1e-6)
    hf70 = P.headloss("hazen", 0.07, 0.3, 1000.0)
    assert r.tdh_m["PA"] == pytest.approx(r.tdh_m["PB"]) and r.tdh_m["PA"] > 115.3 + hf70 - 99.0 - 0.01   # both see the 70 L/s loss


def test_manning_force_main_to_swmm_and_pump_count():
    p = _two_stations(); p.settings["pressure"] = dict(method="manning", n=0.011)
    p.settings["libraries"]["pumps"] = [dict(name="Q", type="multi_point", points=[[10, 30], [40, 25], [80, 10]])]   # starts off Q = 0
    W.apply(p, dict(op="set_pump", ids=["PA"], definition="Q", on_m=1.5, off_m=0.5, count=2))
    p.rain = dict(step_min=5, series=[[0, 0.0], [5, 0.0]])
    t = swmm_inp.from_project(p)
    fm = next(l for l in t.splitlines() if l.startswith("FM ") and ("CIRCULAR" in l or "FORCE_MAIN" in l)).split()
    assert fm[1] == "CIRCULAR" and any(l.startswith("FM ") and " 0.011 " in f" {l} " for l in t.splitlines())
    pc = [l.split() for l in t.splitlines() if l.startswith("PC_PA")]
    heads = [float(r[-2]) for r in pc]; flows = [float(r[-1]) for r in pc]
    assert heads == sorted(heads) and len(set(heads)) == len(heads)             # strictly rising head (SWMM error 171 otherwise)
    assert max(flows) == pytest.approx(2 * 0.08, rel=1e-6)                      # two pumps: twice the flow
    storm.run(p)                                                                 # SWMM takes it


def test_a_fixed_capacity_below_the_flow_is_short():
    p = _two_stations(); W.apply(p, dict(op="set_pump", ids=["PA"], q_ls=10.0))
    r, _ = steady.solve(p)
    assert bool(r.short["PA"]) and r.pump_q_ls["PA"] == pytest.approx(10.0)
    assert any(i["id"] == "PA" and "short" in i["message"] for i in validate.run(p, r))


def test_the_cutoff_caps_every_method():
    s = dict(peaking=dict(method="table", table=[[0.1, 4.66], [1000, 1.54]], cutoff=3.0))
    assert steady.peaking_factor(s, np.array([0.1]))[0] == pytest.approx(3.0)


def test_unit_rows_for_every_load_set():
    p = _two_stations(); p.settings["libraries"]["unit_loads"] = [dict(name="R", type="population", rate_m3d=0.2)]
    p.load_sets["check"] = {}
    W.apply(p, dict(op="set_unit_rows", set="*", ids=["A"], rows=[["R", 1000]]))
    assert steady.flows(p, "check")["GA"] == pytest.approx(200.0)                # the check set sees the rows too
    W.apply(p, dict(op="set_unit_rows", set="check", ids=["A"], rows=[["R", 10]]))
    assert steady.flows(p, "check")["GA"] == pytest.approx(2.0)                  # a set's own rows win


def test_split_a_force_main_and_delete_leave_nothing_stale():
    p = _two_stations(); W.apply(p, dict(op="set_ppipe", ids=["FM"], C=100, K=3))
    W.apply(p, dict(op="split_link", id="FM", x=520.0, y=0.0))
    new = [n for n in p.nodes.index if n not in ("A", "WA", "B", "WB", "J", "R", "O")][0]
    assert p.nodes.kind[new] == "pressure_junction" and p.ppipes["FM-a"]["C"] == 100 and p.ppipes["FM-b"]["K"] == 3 and "FM" not in p.ppipes
    W.apply(p, dict(op="set_pump", ids=["PB"], q_ls=30)); W.apply(p, dict(op="delete", table="nodes", ids=["WB"]))
    assert "PB" not in p.pumps


def test_bad_inputs_are_refused_or_taken_back():
    with pytest.raises(ValueError, match="above 0"): W.apply(_two_stations(), dict(op="set_ppipe", ids=["FM"], C=0))
    p = _two_stations(); p.settings["libraries"]["pumps"] = [dict(name="Q", type="design_point", q_ls=50, h_m=30)]
    W.apply(p, dict(op="set_pump", ids=["PA"], definition="Q"))
    with pytest.raises(ValueError, match="used by a pump"): W.apply(p, dict(op="set_setting", path="libraries.pumps", value=[]))
    with pytest.raises(ValueError): W.apply(p, dict(op="set_setting", path="libraries.pumps", value=[dict(name="Q", type="three_point", shutoff_h_m=30, q_ls=40, h_m=25, max_q_ls=80, max_h_m=28)]))
    with pytest.raises(ValueError, match="lower depth"): W.apply(p, dict(op="set_pump", ids=["PA"], q_ls=10, on_m=0.0, off_m=1.0))
    C = TestClient(app)                                                         # an edit the solve cannot take is undone
    pid = C.post("/api/g/projects/new", json=dict(name="x", crs=32640)).json()["id"]
    ed = lambda **e: C.post(f"/api/g/projects/{pid}/scenarios/base/edit", json=e)
    ed(op="batch", ops=[dict(op="add_node", id="W1", kind="wetwell", x=0, y=0, ground=10, invert=5), dict(op="add_node", id="J", kind="pressure_junction", x=1, y=0, ground=10, invert=8),
                        dict(op="add_node", id="O", kind="outfall", x=50, y=0, ground=10, invert=9), dict(op="add_link", id="PU", kind="pump", from_node="W1", to_node="J"),
                        dict(op="add_link", id="FM", kind="pressure_pipe", from_node="J", to_node="O")])
    n0 = C.get(f"/api/g/projects/{pid}").json()["scenarios"][0]["edits"]
    assert C.get(f"/api/g/projects/{pid}/scenarios/base/results").status_code == 200
    assert C.get(f"/api/g/projects/{pid}").json()["scenarios"][0]["edits"] == n0


def test_two_pumps_on_one_wet_well_are_explained():
    p = _two_stations(); W.apply(p, dict(op="add_node", id="J2", kind="pressure_junction", x=30, y=0, ground=104, invert=102))
    W.apply(p, dict(op="add_link", id="PA2", kind="pump", from_node="WA", to_node="J2"))
    msg = [i["message"] for i in validate.run(p) if i["id"] == "WA"]
    assert msg and "Pumps running" in msg[0]
