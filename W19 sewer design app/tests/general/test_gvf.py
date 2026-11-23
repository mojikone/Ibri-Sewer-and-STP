"""The GVF water profile (engine/gvf.py, 2026-11-23 v4) against hand cases and an independent fine integration."""
import time
import numpy as np
import pytest
from sewerapp.engine import gvf, steady
from sewerapp.engine.hydraulics import section
from sewerapp.model.general import Project
from sewerapp.model import workspace as W


def _line(L=400.0, fall=0.8, dn=315, q_m3d=4320.0, tail=None, K=0.0):
    p = Project("g", crs=32640)
    W.apply(p, dict(op="add_node", id="A", x=0, y=0, ground=104, invert=100.0 + fall))
    W.apply(p, dict(op="add_node", id="O", kind="outfall", x=L, y=0, ground=103, invert=100.0))
    W.apply(p, dict(op="add_link", id="P", from_node="A", to_node="O", dn_mm=dn))
    p.load_sets["design"] = {"A": q_m3d}; p.settings["peaking"]["method"] = "constant"; p.settings["infiltration_m3d_per_km"] = 0.0
    p.settings["flow_profile"] = "gvf"; p.settings["structure_loss"]["K"] = K
    if tail is not None: W.apply(p, dict(op="set_tailwater", ids=["O"], level=tail))
    return p


def test_a_long_mild_pipe_with_a_free_outfall_reaches_normal_depth():
    r, s = steady.solve(_line(L=2000.0, fall=4.0, dn=400))                   # 0.2 %, 50 L/s in DN400 (353 mm bore), part full
    yn = r.d_over_D["P"] * 0.353
    assert r.y_dn_m["P"] == pytest.approx(float(gvf.critical_depth(0.05, 0.353)), rel=1e-6)   # free fall: critical at the end
    assert r.y_up_m["P"] == pytest.approx(yn, rel=0.01) and r.regime["P"] == "M2 drawdown"
    assert s["gvf"]["profile"] == "gvf"


def test_backwater_against_a_fine_integration():
    q0 = _line(L=300.0, fall=0.9, dn=400); q0.settings["flow_profile"] = "normal"                # DN400: 353 mm bore
    yn = steady.solve(q0)[0].d_over_D["P"] * 0.353
    y0 = yn + 0.6 * (0.353 - yn)                                             # above normal depth, below the crown: M1
    p = _line(L=300.0, fall=0.9, dn=400, tail=100.0 + y0); r, _ = steady.solve(p)
    fr = p.settings["friction"]; Q, D, S0 = 0.05, 0.353, 0.003
    y, x = y0, 0.0
    while x < 300.0:                                                         # 6,000 small steps upstream (Euler)
        A, _ = section(D, y); Sf = float(gvf.friction_slope(Q, D, y, fr)); T = 2 * np.sqrt(y * (D - y))
        dy = (S0 - Sf) / (1 - Q * Q * T / (9.81 * A ** 3)); h = 0.05; y -= dy * h; x += h
    assert r.regime["P"] == "M1 backwater" and r.y_up_m["P"] == pytest.approx(y, abs=0.002)
    assert yn < r.y_up_m["P"] < y0


def test_a_drowned_pipe_runs_full_by_its_friction_slope():
    p = _line(L=300.0, fall=0.3, tail=101.0); r, s = steady.solve(p)         # the outlet level over the crown
    sf = float(gvf.friction_slope(0.05, 0.278, 0.278, p.settings["friction"]))
    assert r.regime["P"] == "full" and r.hgl_up["P"] == pytest.approx(101.0 + sf * 300.0, rel=1e-6)
    assert bool(r.surcharged_gvf["P"]) and s["gvf"]["surcharged"] == 1


def test_the_structure_loss_raises_the_upstream_structure():
    p = _line(L=300.0, fall=0.3, tail=101.0, K=1.5); r, _ = steady.solve(p)
    v = 0.05 / (np.pi * 0.278 ** 2 / 4)
    assert r.attrs["node_hgl"]["A"] == pytest.approx(r.hgl_up["P"] + 1.5 * v * v / (2 * 9.81), rel=1e-6)


def test_normal_profile_is_unchanged_by_default():
    p = _line(); p.settings["flow_profile"] = "normal"; r, s = steady.solve(p)
    assert "hgl_up" not in r.columns and "gvf" not in s


def test_gvf_on_the_ibri_network_is_fast():
    from sewerapp.io import ibri_sample
    p = ibri_sample.build("SC1-2056"); p.settings["flow_profile"] = "gvf"
    t0 = time.perf_counter(); r, s = steady.solve(p); dt = time.perf_counter() - t0
    assert r.hgl_up.notna().sum() > 18000 and dt < 8.0, dt


# ---- the Fable 5.2 review of v4: short pipes show the profile, overloaded and drowned pipes, force mains kept
def _euler(Q, D, S0, y, L, fr, h=0.005):
    x = 0.0
    while x < L:
        A, _ = section(D, y); Sf = float(gvf.friction_slope(Q, D, y, fr)); T = 2 * np.sqrt(y * (D - y))
        y -= (S0 - Sf) / (1 - Q * Q * T / (9.81 * A ** 3)) * h; x += h
    return y


def _fine_step(Q, D, S0, y0, yn, L, fr, n=20000):
    """An independent direct step in depth with many steps (valid from critical depth, where Euler in x is singular)."""
    ys = np.linspace(y0, yn * 0.99999 if yn > y0 else yn * 1.00001, n); A, _ = section(D, ys); E = ys + (Q / A) ** 2 / 19.62
    Sf = np.array([float(gvf.friction_slope(Q, D, y, fr)) for y in ys[:: max(1, n // 2000)]]); Sf = np.interp(ys, ys[:: max(1, n // 2000)], Sf)
    dx = (E[:-1] - E[1:]) / (S0 - (Sf[1:] + Sf[:-1]) / 2); x = np.r_[0.0, np.cumsum(dx)]
    return float(np.interp(L, x, ys))


def test_short_pipes_show_the_backwater_and_the_drawdown():
    # M1: DN400 (353 mm) at 0.3 %, 50 L/s, tailwater depth 0.30 m, 10 m long (the review's case: 0.2789 m)
    p = _line(L=10.0, fall=0.03, dn=400, tail=100.30); r, _ = steady.solve(p)
    assert r.regime["P"] == "M1 backwater" and r.y_up_m["P"] == pytest.approx(_euler(0.05, 0.353, 0.003, 0.30, 10.0, p.settings["friction"]), abs=0.002)
    # M2: the same pipe, free outfall, 5 m long (the review's case: 0.1882 m)
    p = _line(L=5.0, fall=0.015, dn=400); r, _ = steady.solve(p)
    yc = float(gvf.critical_depth(0.05, 0.353))
    assert r.regime["P"] == "M2 drawdown" and r.y_up_m["P"] == pytest.approx(_fine_step(0.05, 0.353, 0.003, yc, r.d_over_D["P"] * 0.353, 5.0, p.settings["friction"]), abs=0.002)


def test_an_overloaded_pipe_is_surcharged_by_its_friction():
    p = _line(L=2000.0, fall=2.0); r, _ = steady.solve(p)                     # DN315 at 0.1 % with 50 L/s: full at normal flow
    sf = float(gvf.friction_slope(0.05, 0.278, 0.278, p.settings["friction"]))
    assert bool(r.surcharged_gvf["P"]) and r.hgl_up["P"] == pytest.approx(100.0 + 0.278 + sf * 2000.0, rel=1e-6)


def test_a_drowned_steep_pipe_never_has_a_negative_depth():
    p = _line(L=300.0, fall=3.0, tail=100.0 + 0.278 + 0.12, K=1.0); r, _ = steady.solve(p)   # 1 %: the outlet 0.12 m over the crown
    assert r.y_up_m["P"] > 0 and r.attrs["node_hgl"]["A"] < 110.0
    q = _line(L=100.0, fall=1.0); r2, _ = steady.solve(q)                    # steep, free: ends at normal depth, not at the invert
    assert r2.y_dn_m["P"] > 0.01


def test_force_main_grades_survive_the_gvf_profile():
    import importlib, sys
    sys.path.insert(0, __import__("os").path.dirname(__file__)); tp = importlib.import_module("test_pressure")
    p = tp._station(dict(type="design_point", q_ls=50, h_m=30)); p.settings["flow_profile"] = "gvf"
    r, _ = steady.solve(p)
    assert np.isfinite(r.hgl_up["FM"]) and r.hgl_up["FM"] > r.hgl_dn["FM"]
