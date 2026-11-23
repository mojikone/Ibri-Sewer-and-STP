"""Alternatives (2026-11-23 v5, F14): per-category edit sets with parents, taken by scenarios, as SewerGEMS's."""
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app
from sewerapp.model import workspace as W

C = TestClient(app)


def _proj():
    pid = C.post("/api/g/projects/new", json=dict(name="alt", crs=32640)).json()["id"]
    ed = lambda sid="base", **e: C.post(f"/api/g/projects/{pid}/scenarios/{sid}/edit", json=e)
    r = ed(op="batch", ops=[dict(op="add_node", id="A", x=500000, y=2600000, ground=110, invert=108),
                            dict(op="add_node", id="O", kind="outfall", x=500100, y=2600000, ground=109, invert=107),
                            dict(op="add_link", id="P1", from_node="A", to_node="O", dn_mm=250)])
    assert r.status_code == 200, r.text
    return pid, ed


def _load(pid, sid):
    return C.get(f"/api/g/projects/{pid}/scenarios/{sid}/model").json()["loads"].get("design", {}).get("A")


def test_categories_split_a_mixed_batch():
    parts = W.split_by_category(dict(op="batch", ops=[dict(op="set_loads", set="design", values={"A": 1}), dict(op="move_node", id="A", x=0, y=0)]))
    assert [c for c, _ in parts] == ["physical", "loading"]
    assert W.category(dict(op="set_setting", path="x", value=1)) == "options"


def test_two_scenarios_share_a_loading_alternative_and_undo_takes_it_back():
    pid, ed = _proj()
    a = C.post(f"/api/g/projects/{pid}/alternatives/new", json=dict(cat="loading", name="Loads 2051")).json()["created"]
    sc = C.post(f"/api/g/projects/{pid}/scenarios/base/copy", json={}).json()["created"]
    for sid in ("base", sc):
        assert C.post(f"/api/g/projects/{pid}/scenarios/{sid}/alts", json=dict(cat="loading", aid=a)).status_code == 200
    assert ed(op="set_loads", set="design", values={"A": 500.0}).status_code == 200
    assert _load(pid, "base") == pytest.approx(500.0) and _load(pid, sc) == pytest.approx(500.0)   # shared
    info = C.get(f"/api/g/projects/{pid}/alternatives").json()
    row = [x for x in info["alternatives"]["loading"] if x["id"] == a][0]
    assert row["edits"] == 1 and set(row["used_by"]) == {"base", sc}
    C.post(f"/api/g/projects/{pid}/scenarios/base/undo")
    assert _load(pid, sc) is None and C.get(f"/api/g/projects/{pid}/alternatives").json()["alternatives"]["loading"][0]["edits"] == 0
    C.post(f"/api/g/projects/{pid}/scenarios/base/redo")
    assert _load(pid, sc) == pytest.approx(500.0)


def test_a_child_alternative_inherits_and_overrides():
    pid, ed = _proj()
    a = C.post(f"/api/g/projects/{pid}/alternatives/new", json=dict(cat="loading", name="Base loads")).json()["created"]
    C.post(f"/api/g/projects/{pid}/scenarios/base/alts", json=dict(cat="loading", aid=a))
    ed(op="set_loads", set="design", values={"A": 100.0})
    b = C.post(f"/api/g/projects/{pid}/alternatives/new", json=dict(cat="loading", name="Higher", parent=a)).json()["created"]
    sc = C.post(f"/api/g/projects/{pid}/scenarios/base/copy", json={}).json()["created"]
    C.post(f"/api/g/projects/{pid}/scenarios/{sc}/alts", json=dict(cat="loading", aid=b))
    assert _load(pid, sc) == pytest.approx(100.0)                       # inherited from the parent
    ed(sid=sc, op="set_loads", set="design", values={"A": 300.0})
    assert _load(pid, sc) == pytest.approx(300.0) and _load(pid, "base") == pytest.approx(100.0)
    r = C.post(f"/api/g/projects/{pid}/alternatives/delete", json=dict(cat="loading", id=a))
    assert r.status_code == 400                                         # in use, and has a child


def test_from_scenario_and_back_to_own_edits():
    pid, ed = _proj()
    ed(op="set_loads", set="design", values={"A": 40.0})
    a = C.post(f"/api/g/projects/{pid}/alternatives/new", json=dict(cat="loading", name="From base", from_scenario="base")).json()["created"]
    sc = C.post(f"/api/g/projects/{pid}/scenarios/base/copy", json={}).json()["created"]
    ed(sid=sc, op="set_loads", set="design", values={"A": 90.0})
    assert _load(pid, sc) == pytest.approx(90.0)
    C.post(f"/api/g/projects/{pid}/scenarios/{sc}/alts", json=dict(cat="loading", aid=a))
    assert _load(pid, sc) == pytest.approx(40.0)                        # its own loading edits set aside
    C.post(f"/api/g/projects/{pid}/scenarios/{sc}/alts", json=dict(cat="loading", aid=None))
    assert _load(pid, sc) == pytest.approx(90.0)                        # back to its own


def test_alternatives_survive_save_and_open(tmp_path):
    pid, ed = _proj()
    a = C.post(f"/api/g/projects/{pid}/alternatives/new", json=dict(cat="loading", name="Kept")).json()["created"]
    C.post(f"/api/g/projects/{pid}/scenarios/base/alts", json=dict(cat="loading", aid=a))
    ed(op="set_loads", set="design", values={"A": 77.0})
    r = C.get(f"/api/g/projects/{pid}/save")
    assert r.status_code == 200, r.text
    f = tmp_path / "m.gpkg"; f.write_bytes(r.content)
    pid2 = C.post("/api/g/projects/open", files=dict(file=("m.gpkg", f.read_bytes(), "application/geopackage+sqlite3"))).json()["id"]
    assert _load(pid2, "base") == pytest.approx(77.0)
    info = C.get(f"/api/g/projects/{pid2}/alternatives").json()
    assert info["scenarios"]["base"]["alts"] == {"loading": a}


# ---- the Fable 5.2 review of v5: history order, the right edit undone, one step, opting out, ids, the agent's copies
def _alt(pid, cat, **kw):
    return C.post(f"/api/g/projects/{pid}/alternatives/new", json=dict(cat=cat, **kw)).json()["created"]


def _take(pid, sid, cat, aid):
    r = C.post(f"/api/g/projects/{pid}/scenarios/{sid}/alts", json=dict(cat=cat, aid=aid)); assert r.status_code == 200, r.text


def _dn(pid, sid, lid="P1"):
    return {f["id"]: f["properties"]["dn_mm"] for f in C.get(f"/api/g/projects/{pid}/scenarios/{sid}/model").json()["links"]["features"]}[lid]


def test_an_empty_alternative_changes_nothing_and_the_design_keeps_its_loads():
    pid, ed = _proj()
    ed(op="set_loads", set="design", values={"A": 40000.0}); ed(op="design")
    big = _dn(pid, "base"); assert big > 250
    _take(pid, "base", "options", _alt(pid, "options", name="empty"))
    assert _dn(pid, "base") == big                                       # replayed in the order it was done


def test_delete_and_re_add_stays_deleted_with_an_alternative_taken():
    pid, ed = _proj()
    _take(pid, "base", "hydrology", _alt(pid, "hydrology", name="unrelated"))
    ed(op="batch", ops=[dict(op="add_node", id="B", x=500050, y=2600010, ground=110, invert=108)])
    ed(op="set_loads", set="design", values={"B": 50.0}); ed(op="delete", table="nodes", ids=["B"])
    ed(op="add_node", id="B", x=500050, y=2600010, ground=110, invert=108)
    assert _load(pid, "base") is None and C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["loads"].get("design", {}).get("B") is None


def test_undo_takes_out_its_own_edit_not_the_other_scenarios():
    pid, ed = _proj(); a = _alt(pid, "loading", name="shared")
    s2 = C.post(f"/api/g/projects/{pid}/scenarios/base/copy", json={}).json()["created"]
    for sid in ("base", s2): _take(pid, sid, "loading", a)
    ed(op="set_loads", set="design", values={"A": 10.0}); ed(sid=s2, op="set_loads", set="design", values={"A": 20.0})
    C.post(f"/api/g/projects/{pid}/scenarios/base/undo")
    assert _load(pid, s2) == pytest.approx(20.0)                         # S2's edit kept
    C.post(f"/api/g/projects/{pid}/scenarios/base/redo")
    assert _load(pid, s2) == pytest.approx(20.0)                         # back in its place in time: S2's later edit still wins


def test_a_mixed_batch_is_one_undo_step_and_a_child_can_opt_out():
    pid, ed = _proj(); a = _alt(pid, "loading", name="L")
    _take(pid, "base", "loading", a)
    ed(op="batch", ops=[dict(op="set", table="links", ids=["P1"], field="dn_mm", value=300), dict(op="set_loads", set="design", values={"A": 5.0})])
    assert _dn(pid, "base") == 300 and _load(pid, "base") == pytest.approx(5.0)
    C.post(f"/api/g/projects/{pid}/scenarios/base/undo")
    assert _dn(pid, "base") == 250 and _load(pid, "base") is None
    C.post(f"/api/g/projects/{pid}/scenarios/base/redo")
    ch = C.post(f"/api/g/projects/{pid}/scenarios/base/copy", json={}).json()["created"]
    assert _load(pid, ch) == pytest.approx(5.0)
    _take(pid, ch, "loading", None); assert _load(pid, ch) is None       # its own edits, not the parent's alternative


def test_ids_are_not_reused_and_redo_survives_a_deleted_alternative():
    pid, ed = _proj(); a = _alt(pid, "loading", name="gone")
    _take(pid, "base", "loading", a); ed(op="set_loads", set="design", values={"A": 7.0})
    C.post(f"/api/g/projects/{pid}/scenarios/base/undo"); _take(pid, "base", "loading", None)
    assert C.post(f"/api/g/projects/{pid}/alternatives/delete", json=dict(cat="loading", id=a)).status_code == 200
    assert _alt(pid, "loading", name="new") != a
    assert C.post(f"/api/g/projects/{pid}/scenarios/base/redo").status_code == 200
    assert _load(pid, "base") == pytest.approx(7.0)                      # kept by the scenario itself


def test_the_agents_copy_gets_private_alternatives():
    import json as _j
    from sewerapp.assistant import gtools
    pid, ed = _proj(); a = _alt(pid, "loading", name="engineer's")
    _take(pid, "base", "loading", a); ed(op="set_loads", set="design", values={"A": 5.0})
    r = gtools.call(None, "make_scenario", dict(project=pid, scenario="base", name="agent", edits=[dict(op="set_loads", args=_j.dumps(dict(set="design", values={"A": 999.0})))]))
    assert _load(pid, "base") == pytest.approx(5.0) and _load(pid, r["scenario"]) == pytest.approx(999.0)
