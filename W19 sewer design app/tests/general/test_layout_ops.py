"""Edits behind the layout tool, morph, reconnect, prototypes and per-conduit infiltration (user trial F1-F9, 2026-11-23)."""
import math
import pytest
from fastapi.testclient import TestClient
from sewerapp.api import general_api
from sewerapp.api.app import app
from sewerapp.engine import steady
from sewerapp.model.general import Project
from sewerapp.model import workspace as W
from sewerapp.io import gpkg_project

C = TestClient(app)


def _p():
    p = Project("t", crs=32640)
    for i, (x, g) in enumerate([(0, 100.0), (100, 99.0), (200, 98.0)]): W.apply(p, dict(op="add_node", id=f"N{i}", x=x, y=0, ground=g, invert=g - 2))
    W.apply(p, dict(op="add_node", id="O", kind="outfall", x=300, y=0, ground=97.0, invert=95.0))
    for a, b in (("N0", "N1"), ("N1", "N2"), ("N2", "O")): W.apply(p, dict(op="add_link", from_node=a, to_node=b, dn_mm=200))
    p.load_sets["design"] = {"N0": 50.0, "N1": 50.0}
    return p


def test_infiltration_by_length_reproduces_the_old_rule():
    p = _p(); q = steady.flows(p, "design")
    pf = lambda x: float(steady.peaking_factor(p.settings, [x / 86.4])[0])
    assert q["P-3"] == pytest.approx(100 * pf(100) + 0.3 * 0.72)           # 300 m at 0.72 m3/d/km
    p.infil["P-1"] = 7.2                                                     # P-1's own rate, ten times the project's
    q2 = steady.flows(p, "design")
    assert q2["P-3"] - q["P-3"] == pytest.approx(0.1 * (7.2 - 0.72))


@pytest.mark.parametrize("meth,expect", [("count", 3 * 2.0), ("length_diameter", 0.3 * 0.1764 * 2.0),
                                         ("surface_area", math.pi * 0.1764 * 300 * 2.0)])
def test_infiltration_methods(meth, expect):
    p = _p(); p.load_sets["design"] = {}
    W.apply(p, dict(op="set_setting", path="infiltration.method", value=meth)); W.apply(p, dict(op="set_setting", path="infiltration.rate", value=2.0))
    assert steady.flows(p, "design")["P-3"] == pytest.approx(expect)


def test_settings_of_an_older_project_are_filled_in():
    p = _p(); del p.settings["infiltration"], p.settings["prototypes"]
    W.apply(p, dict(op="set_setting", path="infiltration.method", value="count"))
    W.apply(p, dict(op="set_prototype", kind="manhole", values=dict(ground=50.0, depth=3.0)))
    W.apply(p, dict(op="add_node", id="X", x=0, y=50))
    assert (p.nodes.ground["X"], p.nodes.invert["X"]) == (50.0, 47.0)


def test_prototypes_give_new_elements_their_values():
    p = _p()
    W.apply(p, dict(op="set_prototype", kind="conduit", values=dict(dn_mm=315)))
    W.apply(p, dict(op="add_node", id="A", x=0, y=100)); W.apply(p, dict(op="add_link", id="L", from_node="A", to_node="N0"))
    assert p.links.dn_mm["L"] == 315
    W.apply(p, dict(op="set_prototype", kind="conduit", values=dict(section=dict(shape="box", rise_m=1.0, span_m=2.0, n=0.013))))
    W.apply(p, dict(op="add_node", id="B", x=0, y=200)); W.apply(p, dict(op="add_link", id="L2", from_node="B", to_node="A"))
    assert p.sections["L2"]["shape"] == "box" and p.links.dn_mm["L2"] == 0
    with pytest.raises(ValueError): W.apply(p, dict(op="set_prototype", kind="pipe", values={}))
    with pytest.raises(ValueError): W.apply(p, dict(op="set_prototype", kind="manhole", values=dict(colour=1)))


def test_reconnect_keeps_the_link_and_moves_its_end():
    p = _p(); W.apply(p, dict(op="add_node", id="M", x=100, y=100, ground=99.5, invert=97.0))
    W.apply(p, dict(op="reconnect", id="P-1", end="to", node="M"))
    r = p.links.loc["P-1"]
    assert (r.to_node, r.dn_inv, round(r.length_m, 3)) == ("M", 97.0, round(math.hypot(100, 100), 3))
    with pytest.raises(ValueError, match="leaving link"): W.apply(p, dict(op="reconnect", id="P-2", end="from", node="N0"))
    with pytest.raises(ValueError, match="two different"): W.apply(p, dict(op="reconnect", id="P-3", end="from", node="O"))


def test_a_batch_is_one_undo_step_and_validates_as_a_whole():
    pid = C.post("/api/g/projects/new", json=dict(name="b", crs=32640)).json()["id"]
    ed = lambda **e: C.post(f"/api/g/projects/{pid}/scenarios/base/edit", json=e)
    ops = [dict(op="add_node", id="A", kind="manhole", lon=57.0, lat=23.0), dict(op="add_node", id="B", kind="outfall", lon=57.001, lat=23.0),
           dict(op="add_link", id="P", from_node="A", to_node="B")]
    r = ed(op="batch", ops=ops); assert r.status_code == 200, r.text
    m = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()
    assert len(m["nodes"]["features"]) == 2 and m["links"]["features"][0]["properties"]["length_m"] == pytest.approx(102.4, abs=1.0)
    assert ed(op="batch", ops=[dict(op="add_node", id="C", lon=57.002, lat=23.0), dict(op="add_link", from_node="C", to_node="nowhere")]).status_code == 400
    assert len(C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["nodes"]["features"]) == 2   # nothing of a failed batch kept
    C.post(f"/api/g/projects/{pid}/scenarios/base/undo")
    assert len(C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["nodes"]["features"]) == 0


def test_infiltration_and_prototypes_survive_the_file(tmp_path):
    p = _p(); W.apply(p, dict(op="set_infiltration", ids=["P-1"], rate=3.0)); W.apply(p, dict(op="set_prototype", kind="manhole", values=dict(depth=2.5)))
    f = tmp_path / "p.gpkg"; gpkg_project.save(p, str(f))
    q = gpkg_project.load(str(f))[0]
    assert q.infil == {"P-1": 3.0} and q.prototype("manhole")["depth"] == 2.5
    W.apply(p, dict(op="set_infiltration", ids=["P-1"], rate=None)); assert p.infil == {}


# ---- the layout tool's run and the spacing rule (ported from W13, the engineer's rule of 2026-08-18)
from sewerapp.engine import spacing


@pytest.mark.parametrize("L,expect", [(330.0, [80.0, 80.0, 80.0, 90.0]), (250.0, [80.0, 80.0, 90.0]), (180.0, [90.0, 90.0]),
                                      (95.0, [95.0]), (160.0, [80.0, 80.0]), (230.0, [80.0, 80.0, 70.0])])
def test_spacing_rule_as_in_W13_and_the_engineers_examples(L, expect):
    assert sorted(spacing.split_lengths(L, 100.0)) == sorted(expect)


def test_spacing_never_exceeds_the_maximum():
    for L in (37.0, 101.0, 205.0, 333.0, 499.0, 1000.0):
        lens = spacing.split_lengths(L, 100.0)
        assert sum(lens) == pytest.approx(L) and max(lens) <= 100.0 + 1e-6 and min(lens) > 0


def test_table12():
    assert [spacing.table12(d) for d in (200, 315, 400, 900, 1000, 1400, 1600)] == [100, 100, 120, 120, 150, 150, 200]


def test_a_run_puts_manholes_at_the_spacing_and_replays_the_same_ids():
    p = Project("r", crs=32640); W.apply(p, dict(op="add_node", id="A", x=0, y=0, ground=10.0))
    e = dict(op="add_run", from_node="A", x=230.0, y=0.0, kind="outfall", max_spacing=100)
    W.apply(p, e)
    L = p.links.sort_values("length_m")
    assert sorted(round(v, 6) for v in p.links.length_m) == [70.0, 80.0, 80.0] and len(p.nodes) == 4
    assert p.nodes.kind[e["end_id"]] == "outfall" and len(e["mid_ids"]) == 2 and len(e["link_ids"]) == 3
    q = Project("r", crs=32640); W.apply(q, dict(op="add_node", id="A", x=0, y=0, ground=10.0)); W.apply(q, dict(e))
    assert list(q.links.index) == list(p.links.index) and list(q.nodes.index) == list(p.nodes.index)


def test_a_run_from_a_manhole_that_drains_becomes_a_branch_into_it():
    p = _p()                                                                  # N0 -> N1 -> N2 -> O
    e = dict(op="add_run", from_node="N1", x=100.0, y=150.0, max_spacing="table12")
    W.apply(p, e)
    lid = e["link_ids"][-1]
    assert (p.links.from_node[e["link_ids"][0]], p.links.to_node[lid]) == (e["end_id"], "N1") and not p.check()


def test_reverse_turns_a_link_round():
    p = _p(); W.apply(p, dict(op="reverse", ids=["P-3"]))
    r = p.links.loc["P-3"]; assert (r.from_node, r.to_node, r.up_inv, r.dn_inv) == ("O", "N2", 95.0, 96.0)


def test_a_line_drawn_from_the_downstream_end_is_turned_to_run_with_the_flow():
    """Flow arrows follow the stored line: a line digitised downstream-first is turned on entry (2026-11-23)."""
    from sewerapp.model.general import Project
    from sewerapp.model import workspace as W
    from sewerapp.engine import validate
    p = Project("o", crs=32640)
    W.apply(p, dict(op="add_node", id="A", x=0, y=0, ground=10, invert=8)); W.apply(p, dict(op="add_node", id="B", kind="outfall", x=100, y=0, ground=9, invert=7))
    W.apply(p, dict(op="add_link", id="P", from_node="A", to_node="B", coords=[[100, 0], [50, 5], [0, 0]]))
    assert p.links.coords["P"][0] == [0, 0] and p.links.coords["P"][-1] == [100, 0]
    p.links.at["P", "coords"] = [[100, 0], [0, 0]]; assert p.orient_lines() == 1 and p.links.coords["P"][0] == [0, 0]
    assert not [x for x in validate.run(p) if "drawn line" in x["message"]]
    p.links.at["P", "coords"] = [[0, 0], [40, 0]]                                      # a line that stops short of B
    assert [x for x in validate.run(p) if "drawn line" in x["message"]][0]["id"] == "P"


def test_a_restored_autosave_has_its_lines_turned_too():
    """The engineer's phone, 2026-11-23: a project reopened from the server's autosave kept the lines it was saved with."""
    p = _p(); p.links.at[p.links.index[0], "coords"] = [[100, 0], [0, 0]]
    s = W.Session("pX", p); st = s.state(); st["base"].links.at[p.links.index[0], "coords"] = [[100, 0], [0, 0]]
    r = W.Session.from_state(st)
    assert r.model("base").links.coords.iloc[0][0] == [0, 0]
