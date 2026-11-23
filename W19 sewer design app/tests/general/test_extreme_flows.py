"""Unit loads by type and the extreme-flow methods (2026-11-23 v3), against numbers worked by hand (Fable 5.2 review)."""
import numpy as np
import pytest
from sewerapp.engine import steady
from sewerapp.model.general import Project
from sewerapp.model import workspace as W

POPS = np.array([1000.0, 5000.0, 10000.0, 100000.0])


def pf(method, pop=None, q=None, **kw):
    s = dict(peaking=dict(method=method, **kw))
    return steady.peaking_factor(s, np.zeros(len(POPS)) if q is None else np.asarray(q, float), pop)


def test_harmon_and_ten_states_are_one_function():
    assert pf("harmon", POPS) == pytest.approx([3.800, 3.245, 2.955, 2.000], abs=0.001)
    assert pf("ten_states", POPS) == pytest.approx(pf("harmon", POPS), rel=1e-12)


def test_babbitt_and_its_cutoff():
    assert pf("babbitt", POPS) == pytest.approx([5.000, 3.624, 3.155, 1.991], abs=0.001)
    assert pf("babbitt", np.array([10.0]), q=[0.0], cutoff=5.0)[0] == pytest.approx(5.0)          # capped at small P


def test_federov_is_flow_based():
    assert pf("federov", q=[10.0, 100.0]) == pytest.approx([2.69 / 10 ** 0.121, 2.69 / 100 ** 0.121], rel=1e-9)
    assert pf("federov", q=[10.0])[0] == pytest.approx(2.036, abs=0.001)


def _tree(method="harmon"):
    """Two branches of 5,000 people each meet; the shared pipe carries 10,000."""
    p = Project("t", crs=32640)
    for i, (x, y, g) in enumerate([(0, 100, 110), (0, -100, 110), (100, 0, 109), (200, 0, 108)]):
        W.apply(p, dict(op="add_node", id=f"N{i}", x=x, y=y, ground=g, invert=g - 2))
    W.apply(p, dict(op="add_node", id="O", kind="outfall", x=300, y=0, ground=107, invert=105))
    for a, b in (("N0", "N2"), ("N1", "N2"), ("N2", "N3"), ("N3", "O")): W.apply(p, dict(op="add_link", id=f"{a}-{b}", from_node=a, to_node=b, dn_mm=315))
    p.settings["peaking"]["method"] = method; p.settings["infiltration_m3d_per_km"] = 0.0
    p.settings["libraries"]["unit_loads"] = [dict(name="Resident", type="population", rate_m3d=0.2, unit="person"),
                                             dict(name="School", type="count", rate_m3d=10.0, unit="school", pe=50)]
    W.apply(p, dict(op="set_unit_rows", set="design", ids=["N0", "N1"], rows=[["Resident", 5000]]))
    return p


def test_two_branches_peak_on_their_combined_population():
    q = steady.flows(_tree(), "design")
    one = 5000 * 0.2; both = 2 * one
    assert q["N0-N2"] == pytest.approx(one * 3.2453, rel=1e-3)                 # each branch alone: P = 5 thousand
    assert q["N2-N3"] == pytest.approx(both * 2.9545, rel=1e-3)                # together P = 10: 2.955, not 3.245
    assert q["N2-N3"] < 2 * q["N0-N2"]


def test_a_count_load_brings_its_population_equivalent():
    p = _tree(); W.apply(p, dict(op="set_unit_rows", set="design", ids=["N2"], rows=[["School", 2]]))   # 20 m3/d, 100 people
    q = steady.flows(p, "design")
    P = 10100 / 1000; f = 1 + 14 / (4 + P ** 0.5)
    assert q["N2-N3"] == pytest.approx((2000 + 20) * f, rel=1e-6)
    with pytest.raises(ValueError, match="no unit load"): W.apply(p, dict(op="set_unit_rows", set="design", ids=["N2"], rows=[["Hotel", 1]]))
    W.apply(p, dict(op="set_unit_rows", set="design", ids=["N2"], rows=[]))
    assert "N2" not in p.unit_rows["design"]


def test_the_default_method_is_unchanged():
    p = _tree("table")                                                         # the project's G201 table: flow-based, as before
    q = steady.flows(p, "design"); ql = 1000 / 86.4
    assert q["N0-N2"] == pytest.approx(1000 * float(steady.peaking_factor(p.settings, np.array([ql]))[0]), rel=1e-9)
