"""Pump stations and force mains (engine/pressure.py, 2026-11-23 v3), against numbers worked by hand."""
import math
import pytest
from sewerapp.engine import pressure as P, steady, storm
from sewerapp.model.general import Project
from sewerapp.model import workspace as W
from sewerapp.io import swmm_inp


def test_hazen_williams_by_hand():
    # 50 L/s in 1,000 m of 200 mm bore, C 130: 10.67 x 1000 x 0.05^1.852 / (130^1.852 x 0.2^4.8704) = 12.8 m
    assert P.headloss("hazen", 0.05, 0.2, 1000.0, C=130) == pytest.approx(12.83, rel=0.01)
    dw = P.headloss("darcy", 0.05, 0.2, 1000.0, e_mm=0.1)             # the same main by Darcy-Weisbach: the same order
    assert 0.8 < dw / 12.83 < 1.25
    v = 0.05 / (math.pi * 0.04 / 4)
    assert P.headloss("manning", 0.05, 0.2, 1000.0, n=0.012) == pytest.approx(1000 * (0.012 * v) ** 2 / 0.05 ** (4 / 3), rel=1e-9)


def test_pump_curves():
    H, qmax = P.curve(dict(type="design_point", q_ls=50, h_m=20))     # EPANET single point: 4/3 Hd at shutoff, 0 at 2 Qd
    assert float(H(0)) == pytest.approx(80 / 3) and float(H(0.05)) == pytest.approx(20) and qmax == pytest.approx(0.1) and float(H(0.1)) == pytest.approx(0, abs=1e-9)
    H3, _ = P.curve(dict(type="three_point", shutoff_h_m=30, q_ls=40, h_m=25, max_q_ls=80, max_h_m=10))   # C = ln(20/5)/ln 2 = 2, B = 3125
    assert float(H3(0.06)) == pytest.approx(30 - 3125 * 0.06 ** 2) and float(H3(0.04)) == pytest.approx(25)
    Hm, _ = P.curve(dict(type="multi_point", points=[[0, 30], [40, 25], [80, 10]]))
    assert float(Hm(0.06)) == pytest.approx(17.5)
    with pytest.raises(ValueError): P.curve(dict(type="three_point", shutoff_h_m=10, q_ls=40, h_m=25, max_q_ls=80, max_h_m=10))


def _station(definition=None):
    p = Project("ps", crs=32640)
    W.apply(p, dict(op="add_node", id="MH", x=0, y=0, ground=104, invert=101.0))
    W.apply(p, dict(op="add_node", id="WW", kind="wetwell", x=10, y=0, ground=104, invert=100.0))
    W.apply(p, dict(op="add_node", id="J", kind="pressure_junction", x=20, y=0, ground=104, invert=102.0))
    W.apply(p, dict(op="add_node", id="R", kind="manhole", x=1020, y=0, ground=117, invert=115.0))
    W.apply(p, dict(op="add_node", id="O", kind="outfall", x=1100, y=0, ground=116, invert=114.0))
    W.apply(p, dict(op="add_link", id="G1", from_node="MH", to_node="WW", dn_mm=200))
    W.apply(p, dict(op="add_link", id="PU", kind="pump", from_node="WW", to_node="J"))
    W.apply(p, dict(op="add_link", id="FM", kind="pressure_pipe", from_node="J", to_node="R", dn_mm=200, length_m=1000.0))
    W.apply(p, dict(op="add_link", id="G2", from_node="R", to_node="O", dn_mm=200))
    p.links.loc["FM", "inside_mm"] = 200.0                                 # a 200 mm bore for the hand numbers
    p.load_sets["design"] = {"MH": 4320.0}                                 # 50 L/s average; the peaking is off below
    p.settings["peaking"]["method"] = "constant"; p.settings["peaking"]["constant"] = 1.0
    p.settings["infiltration_m3d_per_km"] = 0.0
    if definition:
        p.settings["libraries"]["pumps"] = [dict(name="P1", **definition)]
        W.apply(p, dict(op="set_pump", ids=["PU"], definition="P1", on_m=1.5, off_m=0.5))
    else: W.apply(p, dict(op="set_pump", ids=["PU"], q_ls=50, on_m=1.5, off_m=0.5))
    return p


def test_the_station_by_hand():
    res, summ = steady.solve(_station(dict(type="design_point", q_ls=50, h_m=20)))
    # 50 L/s pumped; the main discharges full at R: 115.0 + 0.2; friction 12.83 m; the wet well at its stop level 100.5
    assert res.q_ls["PU"] == pytest.approx(50.0) and res.q_ls["FM"] == pytest.approx(50.0)
    assert res.hf_m["FM"] == pytest.approx(12.83, rel=0.01)
    assert res.tdh_m["PU"] == pytest.approx(115.2 + 12.83 - 100.5, rel=0.005)            # 27.5 m
    assert res.pump_head_m["PU"] == pytest.approx(20.0) and bool(res.short["PU"])          # a 50 L/s @ 20 m pump is short
    assert 0 < res.op_q_ls["PU"] < 50                                                      # and runs back on its curve
    H, _ = P.curve(dict(type="design_point", q_ls=50, h_m=20)); qo = res.op_q_ls["PU"] / 1000
    assert float(H(qo)) == pytest.approx(115.2 + P.headloss("hazen", qo, 0.2, 1000.0) - 100.5, abs=0.01)
    assert summ["pressure"]["pumps_short"] == 1 and summ["pressure"]["mains"] == 1
    ok, _ = steady.solve(_station(dict(type="design_point", q_ls=50, h_m=30)))
    assert not bool(ok.short["PU"]) and ok.op_q_ls["PU"] > 50
    assert ok.p_up_m["FM"] == pytest.approx(ok.hgl_up["FM"] - 102.0)                      # pressure head at the start


def test_force_main_and_pump_curve_reach_swmm_and_run():
    p = _station(dict(type="three_point", shutoff_h_m=40, q_ls=50, h_m=30, max_q_ls=90, max_h_m=10))
    p.rain = dict(step_min=5, series=[[0, 0.0], [5, 0.0]])
    t = swmm_inp.from_project(p)
    assert "FORCE_MAIN" in t and "FORCE_MAIN_EQUATION H-W" in t and "Pump3" in t
    fm = next(l for l in t.splitlines() if l.startswith("FM ") and "FORCE_MAIN" in l).split()
    assert fm[1:4] == ["FORCE_MAIN", "0.2", "130"]
    r = storm.run(p)                                                          # it runs (no inflow, the pump stays off)
    assert "PU" in r["links"] and "FM" in r["links"]


def test_kinds_and_edits():
    p = _station()
    with pytest.raises(ValueError, match="not a pressure pipe"): W.apply(p, dict(op="set_ppipe", ids=["G1"], C=120))
    W.apply(p, dict(op="set_ppipe", ids=["FM"], C=100, K=2.5))
    r, _ = steady.solve(p)
    assert r.hf_m["FM"] == pytest.approx(P.headloss("hazen", 0.05, 0.2, 1000.0, C=100), rel=1e-6)
    assert r.hm_m["FM"] == pytest.approx(2.5 * (0.05 / (math.pi * 0.01)) ** 2 / (2 * 9.80665), rel=1e-6)
    with pytest.raises(ValueError, match="no pump definition"): W.apply(p, dict(op="set_pump", ids=["PU"], definition="nope"))


# ---- the Fable 5.2 review's acceptance numbers (2026-11-23), worked by hand
def test_review_friction_numbers():
    assert P.headloss("hazen", 0.05, 0.3, 1000.0, C=130) == pytest.approx(1.781, abs=0.002)
    assert P.headloss("darcy", 0.05, 0.3, 1000.0, e_mm=0.15, nu=1.0e-6) == pytest.approx(1.591, abs=0.005)
    assert P.headloss("manning", 0.05, 0.3, 1000.0, n=0.013) == pytest.approx(2.674, abs=0.002)


def test_review_three_point_fit():
    H, qmax = P.curve(dict(type="three_point", shutoff_h_m=40, q_ls=50, h_m=30, max_q_ls=80, max_h_m=15))
    C = math.log(25 / 10) / math.log(80 / 50); assert C == pytest.approx(1.9495, abs=1e-4)
    assert qmax * 1000 == pytest.approx(101.8, abs=0.1)


def _lift(L_m, count=1, static=20.0):
    p = Project("op", crs=32640)
    W.apply(p, dict(op="add_node", id="WW", kind="wetwell", x=0, y=0, ground=105, invert=100.0))
    W.apply(p, dict(op="add_node", id="J", kind="pressure_junction", x=1, y=0, ground=105, invert=100.0))
    W.apply(p, dict(op="add_node", id="E", kind="outfall", x=2, y=0, ground=130, invert=100.0 + static - 0.3))
    W.apply(p, dict(op="add_link", id="PU", kind="pump", from_node="WW", to_node="J"))
    W.apply(p, dict(op="add_link", id="FM", kind="pressure_pipe", from_node="J", to_node="E", length_m=L_m))
    p.links.loc["FM", ["inside_mm", "dn_inv"]] = [300.0, 100.0 + static - 0.3]          # the main ends full at 100 + static
    p.settings["libraries"]["pumps"] = [dict(name="P", type="design_point", q_ls=50, h_m=30)]
    p.settings["friction"]["nu"] = 1.0e-6
    W.apply(p, dict(op="set_pump", ids=["PU"], definition="P", on_m=0.0001, off_m=0.0, count=count)); p.pumps["PU"]["off_m"] = 0.0
    return P.solve(p, {"PU": 0.0})[0]["PU"]


def test_review_operating_points():
    assert _lift(1e-6)["op_q_ls"] == pytest.approx(70.71, abs=0.05)                       # no friction: 40 - 10 (Q/50)^2 = 20
    r = _lift(5615.96); assert (r["op_q_ls"], r["op_h_m"]) == (pytest.approx(50.0, abs=0.05), pytest.approx(30.0, abs=0.02))
    r = _lift(2000.0); assert (r["op_q_ls"], r["op_h_m"]) == (pytest.approx(60.95, abs=0.05), pytest.approx(25.14, abs=0.02))
    r = _lift(2000.0, count=2); assert (r["op_q_ls"], r["op_h_m"]) == (pytest.approx(93.27, abs=0.1), pytest.approx(31.30, abs=0.03))
    r = _lift(100.0, static=45.0); assert r["op_q_ls"] == 0.0 and r["cannot_lift"] and r["short"]   # shutoff 40 m below a 45 m lift
