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


def test_split_names_the_new_node_and_takes_the_tools_kind():
    """Morph onto a pipe (2026-11-23): the editor names the new node; its kind is the tool's. Without node_id the old
    naming (the link's id) stays, so saved edits replay to the same ids."""
    p = _p(); lid = p.links.index[0]
    W.apply(p, dict(op="split_link", id=lid, node_id="WW-7", kind="wetwell", x=50, y=0))
    assert p.nodes.kind["WW-7"] == "wetwell" and {f"{lid}-a", f"{lid}-b"} <= set(p.links.index)
    q = _p(); W.apply(q, dict(op="split_link", id=lid, x=50, y=0)); assert lid in q.nodes.index and q.nodes.kind[lid] == "manhole"
    with pytest.raises(ValueError): W.apply(_p(), dict(op="split_link", id=lid, node_id="N1", x=50, y=0))
    with pytest.raises(ValueError): W.apply(_p(), dict(op="split_link", id=lid, node_id="X", kind="tank", x=50, y=0))


def test_terrain_levels_record_their_source_and_any_other_write_clears_it():
    """TRex from the browser (2026-11-23): the structures in the terrain's CRS out, levels in, one undo step, the source
    kept with each structure and cleared by a hand edit or a move; Copernicus levels give one Validate warning."""
    from sewerapp.engine import validate, terrain
    p = _p(); W.apply(p, dict(op="set_values", table="nodes", field="ground", values={"N0": 101.0, "N1": 100.5}, source="file dem.tif"))
    assert p.ground_src == {"N0": "file dem.tif", "N1": "file dem.tif"}
    W.apply(p, dict(op="set", table="nodes", ids=["N0"], field="ground", value=102.0)); assert "N0" not in p.ground_src
    W.apply(p, dict(op="move_node", id="N1", x=110, y=0)); assert p.ground_src == {}
    W.apply(p, dict(op="set_values", table="nodes", field="ground", values={"N0": 101.0, "N2": 99.0}, source=terrain.COPERNICUS_SRC))
    w = [x for x in validate.run(p) if "Copernicus" in x["message"]]; assert len(w) == 1 and w[0]["message"].startswith("2 structures")
    W.apply(p, dict(op="delete", table="nodes", ids=["N2"])); assert list(p.ground_src) == ["N0"]
    p.crs = 32640; ids, x, y = terrain.points_in(p, "EPSG:4326")
    assert len(ids) == 3 and 50 < x[0] < 60 and 0 <= y[0] < 1                       # UTM 40N near the equator, in lon/lat
    with pytest.raises(ValueError): terrain.points_in(p, "EPSG:999999")


def test_trex_endpoints_points_levels_and_copernicus(monkeypatch):
    """The endpoints: points in the terrain's CRS, levels back with the file's name as the source, Copernicus read through
    a stand-in tile (no network in tests) and refused for a local-metre project."""
    import numpy as np, rasterio
    from rasterio.transform import from_origin
    from sewerapp.engine import terrain
    p = _p(); p.crs = 32640
    for i, (x, y) in enumerate([(445000, 2565000), (445100, 2565000), (445200, 2565000)]): p.nodes.loc[f"N{i}", ["x", "y"]] = [x, y]
    p.nodes.loc["O", ["x", "y"]] = [445300, 2565000]
    pid = general_api._open(p); B = f"/api/g/projects/{pid}/scenarios/base"
    r = C.post(B + "/trex/points", json=dict(crs="EPSG:32640")).json(); assert r["x"][0] == 445000
    r = C.post(B + "/trex/levels", json=dict(levels={"N0": 330.0, "N1": None, "ZZ": 5.0}, name="..\dem.tif", res_m=0.5)).json()
    assert r["updated"] == 1 and r["source"] == "file dem.tif, 0.5 m cells" and r["no_data_count"] == 1
    m = C.get(B + "/model").json(); n0 = next(f for f in m["nodes"]["features"] if f["id"] == "N0")["properties"]
    assert n0["ground"] == 330.0 and n0["ground_src"] == "file dem.tif, 0.5 m cells"
    import tempfile, os
    f = os.path.join(tempfile.mkdtemp(), "tile.tif")                        # a stand-in GLO-30 tile: 1 degree, 1/3600 cells
    a = np.fromfunction(lambda r, c: 300.0 + c * 0.01, (3600, 3600), dtype=float).astype("float32")
    with rasterio.open(f, "w", driver="GTiff", width=3600, height=3600, count=1, dtype="float32", crs="EPSG:4326",
                       transform=from_origin(56 - 0.5 / 3600, 24 + 0.5 / 3600, 1 / 3600, 1 / 3600)) as d: d.write(a, 1)
    seen = []
    def opener(url):
        seen.append(url)
        if "N23_00_E056" not in url: raise rasterio.errors.RasterioIOError("404")
        return rasterio.open(f)
    real = terrain.copernicus
    monkeypatch.setattr(terrain, "copernicus", lambda q, ids=None: real(q, ids, opener=opener))
    r = C.post(B + "/trex/copernicus", json=dict(keep_depth=True)).json()
    assert r["updated"] == 4 and r["tiles"] and "DLR" in r["notice"] and all(u.startswith(terrain.BUCKET) for u in seen)
    m = C.get(B + "/model").json(); g = {f["id"]: f["properties"] for f in m["nodes"]["features"]}
    assert g["N0"]["ground_src"].startswith("Copernicus") and 300 < g["N0"]["ground"] < 340
    q = _p(); pid2 = general_api._open(q)
    assert C.post(f"/api/g/projects/{pid2}/scenarios/base/trex/copernicus", json={}).status_code == 400   # local metres


def test_contours_and_spot_levels_give_tin_levels(tmp_path):
    """F28 contours and points: a DXF (contours as elevations, spot levels as points and as text), a zipped shapefile
    with an elevation field, and a DWG refused with what to do when the ODA converter is absent."""
    import ezdxf, zipfile, geopandas as gpd
    from shapely.geometry import LineString
    from sewerapp.engine import terrain
    p = _p(); p.crs = 32640
    for i, (x, y) in enumerate([(445020, 2565025), (445050, 2565025), (445080, 2565075)]): p.nodes.loc[f"N{i}", ["x", "y"]] = [x, y]
    p.nodes.loc["O", ["x", "y"]] = [446000, 2569000]                                 # outside the data: no value
    pid = general_api._open(p); B = f"/api/g/projects/{pid}/scenarios/base/trex/vector"
    doc = ezdxf.new(); m = doc.modelspace()
    for k, z in enumerate((10, 12, 14)):                                              # contours every 50 m, 2 m apart
        m.add_lwpolyline([(445000, 2565000 + 50 * k), (445100, 2565000 + 50 * k)], dxfattribs={"elevation": z, "layer": "CONT"})
    m.add_text("99.5", dxfattribs={"layer": "TXT", "insert": (445000, 2565000)})
    f = tmp_path / "survey.dxf"; doc.saveas(f)
    r = C.post(B + "/inspect", files=[("files", ("survey.dxf", f.read_bytes(), "application/dxf"))]).json()
    assert r["has_z"] and r["fields"][0] == terrain.Z_FIELD and terrain.TEXT_FIELD in r["fields"] and r["dxf_layers"] == ["CONT", "TXT"]
    out = C.post(B, json=dict(token=r["token"], field=terrain.Z_FIELD, dxf_layer="CONT")).json()
    m0 = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json(); g = {x["id"]: x["properties"] for x in m0["nodes"]["features"]}
    assert abs(g["N0"]["ground"] - 11.0) < 1e-6 and abs(g["N2"]["ground"] - 13.0) < 1e-6 and out["no_data_count"] == 1   # 25 m up a 2 m / 50 m slope
    assert g["N0"]["ground_src"].startswith("contours or spot levels survey.dxf, layer CONT, TIN of")
    # a zipped shapefile of contours with a level field (no Z)
    gdf = gpd.GeoDataFrame(dict(ELEV=[20.0, 30.0]), geometry=[LineString([(445000, 2565000), (445100, 2565000)]), LineString([(445000, 2565100), (445100, 2565100)])], crs="EPSG:32640")
    gdf.to_file(tmp_path / "cont.shp"); z = tmp_path / "cont.zip"
    with zipfile.ZipFile(z, "w") as zz:
        for ext in ("shp", "shx", "dbf", "prj", "cpg"):
            if (tmp_path / f"cont.{ext}").exists(): zz.write(tmp_path / f"cont.{ext}", f"cont.{ext}")
    r = C.post(B + "/inspect", files=[("files", ("cont.zip", z.read_bytes(), "application/zip"))]).json()
    assert "ELEV" in r["fields"] and not r["has_z"] and "32640" in r["crs"]
    C.post(B, json=dict(token=r["token"], field="ELEV"))
    m0 = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json(); g = {x["id"]: x["properties"] for x in m0["nodes"]["features"]}
    assert abs(g["N0"]["ground"] - 22.5) < 1e-6 and "field ELEV" in g["N0"]["ground_src"]
    from ezdxf.addons import odafc
    if not odafc.is_installed():
        r = C.post(B + "/inspect", files=[("files", ("plan.dwg", b"AC1032", "application/acad"))])
        assert r.status_code == 400 and "ODA File Converter" in r.json()["detail"] and "DXF" in r.json()["detail"]
    assert C.post(B, json=dict(token="nope", field="ELEV")).status_code == 400
