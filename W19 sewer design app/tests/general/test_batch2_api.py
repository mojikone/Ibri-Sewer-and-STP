"""Batch 2 on the server: scenarios renamed, deleted (with their copies) and compared; the project file brings every
scenario back; design with locked pipes, of a selection only, and as a preview that records nothing; quantities in the
team's BOQ structure; KMZ; storm frames and the storm level on the profile; saved routes; the assistant's map actions."""
import io, os, zipfile
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app
from sewerapp.engine import quantities as Q

C = TestClient(app)
W19 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def ed(pid, sid="base", code=200, **e):
    r = C.post(f"/api/g/projects/{pid}/scenarios/{sid}/edit", json=e); assert r.status_code == code, r.text; return r.json()


def links(pid, sid="base"):
    return {f["id"]: f["properties"] for f in C.get(f"/api/g/projects/{pid}/scenarios/{sid}/model").json()["links"]["features"]}


@pytest.fixture()
def net():
    pid = C.post("/api/g/projects/new", json=dict(name="Batch 2", crs=32640)).json()["id"]
    for i, (x, g) in enumerate([(444000, 330.0), (444100, 329.5), (444200, 329.0)]):
        ed(pid, op="add_node", id=f"MH{i+1}", kind="manhole", x=x, y=2563000, ground=g, invert=g - 2.0)
    ed(pid, op="add_node", id="OUT", kind="outfall", x=444300, y=2563000, ground=328.5, invert=326.5)
    for a, b in (("MH1", "MH2"), ("MH2", "MH3"), ("MH3", "OUT")): ed(pid, op="add_link", from_node=a, to_node=b, dn_mm=200)
    ed(pid, op="set_load", set="design", node="MH1", value=86.4)
    return pid


def test_scenarios_renamed_deleted_with_their_copies_and_compared(net):
    s1 = C.post(f"/api/g/projects/{net}/scenarios/base/copy", json=dict(name="a")).json()["created"]
    s2 = C.post(f"/api/g/projects/{net}/scenarios/{s1}/copy", json=dict(name="b")).json()["created"]
    info = C.post(f"/api/g/projects/{net}/scenarios/{s1}/rename", json=dict(name="bigger pipes")).json()
    assert [s["name"] for s in info["scenarios"]] == ["Base", "bigger pipes", "b"]
    ed(net, s1, op="set", table="links", ids=["P-2"], field="dn_mm", value=315)
    ed(net, s1, op="set", table="nodes", ids=["MH1"], field="invert", value=327.9)
    cmp = C.get(f"/api/g/projects/{net}/compare", params=dict(a="base", b=s1)).json()
    assert cmp["change"]["P-2"] == "size" and cmp["change"]["P-1"] == "levels" and "P-3" not in cmp["change"]
    assert cmp["counts"]["size"] == 1 and cmp["counts"]["levels"] == 1 and cmp["counts"]["same"] == 1
    row = next(r for r in cmp["rows"] if r["id"] == "P-2"); assert (row["dn_mm_a"], row["dn_mm_b"]) == (200, 315) and row["dv"] < 0
    assert C.post(f"/api/g/projects/{net}/scenarios/base/delete").status_code == 400
    d = C.post(f"/api/g/projects/{net}/scenarios/{s1}/delete").json()
    assert sorted(d["deleted"]) == sorted([s1, s2]) and [s["id"] for s in d["scenarios"]] == ["base"]


def test_the_project_file_brings_every_scenario_back(net):
    s1 = C.post(f"/api/g/projects/{net}/scenarios/base/copy", json=dict(name="bigger")).json()["created"]
    ed(net, s1, op="set", table="links", ids=["P-3"], field="dn_mm", value=250)
    C.post(f"/api/g/projects/{net}/routes", json=dict(name="main line", start="MH1", end="OUT", via=""))
    r0 = C.get(f"/api/g/projects/{net}/scenarios/{s1}/results").json()["links"]
    f = C.get(f"/api/g/projects/{net}/save", params=dict(sid=s1)).content
    o = C.post("/api/g/projects/open", files={"file": ("p.gpkg", f)}).json()
    assert [s["name"] for s in o["scenarios"]] == ["Base", "bigger"] and o["current"] == s1
    assert C.get(f"/api/g/projects/{o['id']}/scenarios/{s1}/results").json()["links"] == r0
    assert C.get(f"/api/g/projects/{o['id']}/scenarios/base/results").json()["links"]["P-3"]["dn_mm"] == 200
    assert C.get(f"/api/g/projects/{o['id']}/routes").json() == [dict(name="main line", start="MH1", end="OUT", via="")]
    C.post(f"/api/g/projects/{o['id']}/scenarios/{s1}/undo")                      # the history came back too
    assert links(o["id"], s1)["P-3"]["dn_mm"] == 200


def test_design_keeps_locked_pipes_does_a_selection_and_previews(net):
    ed(net, op="set_load", set="design", node="MH1", value=5000.0)
    before = links(net)
    pv = C.post(f"/api/g/projects/{net}/scenarios/base/design", json=dict(preview=True)).json()
    assert pv["preview"] and pv["sizes_changed"] >= 1 and {r["id"] for r in pv["rows"]} >= {"P-1"}
    assert links(net) == before                                                  # a preview records nothing
    ed(net, op="lock", ids=["P-1"], locked=True)
    C.post(f"/api/g/projects/{net}/scenarios/base/design", json={})
    L = links(net)
    assert L["P-1"]["dn_mm"] == 200 and L["P-1"]["up_inv"] == before["P-1"]["up_inv"] and L["P-1"]["dn_inv"] == before["P-1"]["dn_inv"]
    assert L["P-2"]["dn_mm"] > 200                                                # the free pipes were designed
    C.post(f"/api/g/projects/{net}/scenarios/base/undo"); ed(net, op="lock", ids=["P-1"], locked=False)
    C.post(f"/api/g/projects/{net}/scenarios/base/design", json=dict(only=["P-3"]))
    L = links(net)
    assert (L["P-1"]["dn_mm"], L["P-2"]["dn_mm"]) == (200, 200) and L["P-3"]["dn_mm"] > 200
    assert L["P-2"]["dn_inv"] == before["P-2"]["dn_inv"]


def test_quantities_in_the_boq_structure_and_kmz(net, tmp_path):
    assert [Q.band(d) for d in (1.0, 1.5, 1.6, 2.0, 2.01, 15.0, 15.2)] == ["Up to 1.5", "Up to 1.5", "1.5 - 2.0", "1.5 - 2.0", "2.0 - 2.5", "14.5 - 15.0", "Over 15.0"]
    assert [Q.mh_type(d) for d in (200, 355, 400, 560, 630)] == ["Type 1 - 1200 mm", "Type 1 - 1200 mm", "Type 2 - 1500 mm", "Type 2 - 1500 mm", "Type 3 - 1800 mm"]
    q = C.get(f"/api/g/projects/{net}/scenarios/base/quantities").json()
    assert q["totals"]["pipes"] == 3 and q["totals"]["manholes"] == 3 and q["totals"]["outfalls"] == 1
    all200 = next(r for r in q["rows"] if r["item"] == "Pipe DN200" and r["band"] == "all")
    assert all200["qty"] == pytest.approx(300, abs=0.1) and all200["count"] == 3
    assert sum(r["qty"] for r in q["rows"] if r["item"] == "Pipe DN200" and r["band"] != "all") == pytest.approx(300, abs=0.1)
    assert sum(r["qty"] for r in q["rows"] if r["item"].startswith("Manhole")) == 3
    k = C.get(f"/api/g/projects/{net}/export.kmz").content
    kml = zipfile.ZipFile(io.BytesIO(k)).read("doc.kml").decode()
    assert kml.count("<LineString>") == 3 and "<Folder><name>Outfalls (1)</name>" in kml and "Manholes (switch on to see) (3)" in kml
    loc = C.post("/api/g/projects/new", json=dict(name="local")).json()["id"]
    assert C.get(f"/api/g/projects/{loc}/export.kmz").status_code == 400


def test_storm_frames_and_the_storm_level_on_the_profile():
    with open(os.path.join(W19, "tests", "fixtures", "swmm", "extran", "extran1.inp"), "rb") as f:
        pid = C.post("/api/g/projects/import", files={"file": ("extran1.inp", f)}).json()["id"]
    assert C.get(f"/api/g/projects/{pid}/scenarios/base/storm/frame", params=dict(period=0)).status_code == 400
    r = C.post(f"/api/g/projects/{pid}/scenarios/base/storm").json()
    n = r["summary"]["periods"]
    fr = C.get(f"/api/g/projects/{pid}/scenarios/base/storm/frame", params=dict(period=n // 2, attr="flow_rate")).json()
    assert fr["period"] == n // 2 and len(fr["links"]) == 9 and fr["t_s"] > 0
    peak = {k: v["q_peak"] for k, v in r["links"].items()}
    assert all(abs(v) <= peak[k] + 1e-6 for k, v in fr["links"].items())        # no value above the run's peak
    m = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()
    start = m["links"]["features"][0]["properties"]["from_node"]
    rows = C.get(f"/api/g/projects/{pid}/scenarios/base/profile", params=dict(start=start)).json()
    assert rows[0]["storm0"] == pytest.approx(r["nodes"][start]["head_peak"])


def test_routes_saved_and_the_assistants_map_actions(net):
    C.post(f"/api/g/projects/{net}/routes", json=dict(name="r1", start="MH1", end="MH3", via=""))
    C.post(f"/api/g/projects/{net}/routes", json=dict(name="r1", start="MH2", end="", via=""))     # same name replaces
    assert C.get(f"/api/g/projects/{net}/routes").json() == [dict(name="r1", start="MH2", end="", via="")]
    assert C.post(f"/api/g/projects/{net}/routes/delete", json=dict(name="r1")).json() == []
    from sewerapp.assistant import gtools
    gtools.ACTIONS.clear()
    assert gtools.call(None, "show_on_map", dict(project=net, table="links", ids=["P-1", "P-2"])) == dict(shown=2)
    gtools.call(None, "show_profile", dict(project=net, scenario="base", start="MH1", end="", via=""))
    assert gtools.ACTIONS == [dict(kind="select", table="links", ids=["P-1", "P-2"]), dict(kind="profile", start="MH1", end="", via="")]
    with pytest.raises(ValueError): gtools.call(None, "show_profile", dict(project=net, scenario="base", start="XX", end="", via=""))
    gtools.ACTIONS.clear()
