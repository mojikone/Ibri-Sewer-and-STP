"""LoadBuilder, TRex, the rational method, controls, SCS curve number, batch runs (2026-11-23 v4)."""
import io, json, math
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app
from sewerapp.engine import storm, tools_v4
from sewerapp.io import swmm_inp, demo_pond
from sewerapp.model.general import Project
from sewerapp.model import workspace as W

C = TestClient(app)


def _proj():
    pid = C.post("/api/g/projects/new", json=dict(name="t", crs=32640)).json()["id"]
    ed = lambda **e: C.post(f"/api/g/projects/{pid}/scenarios/base/edit", json=e)
    r = ed(op="batch", ops=[dict(op="add_node", id="A", x=500000, y=2600000, ground=110, invert=108), dict(op="add_node", id="B", x=500100, y=2600000, ground=109.5, invert=107.4),
                            dict(op="add_node", id="O", kind="outfall", x=500200, y=2600000, ground=109, invert=106.8),
                            dict(op="add_link", id="P1", from_node="A", to_node="B", dn_mm=250), dict(op="add_link", id="P2", from_node="B", to_node="O", dn_mm=250)])
    assert r.status_code == 200, r.text
    return pid, ed


def test_loadbuilder_points_to_the_nearest_structures(tmp_path):
    pid, ed = _proj()
    gj = dict(type="FeatureCollection", crs=dict(type="name", properties=dict(name="EPSG:32640")), features=[
        dict(type="Feature", properties=dict(pop=120), geometry=dict(type="Point", coordinates=[500010, 2600005])),
        dict(type="Feature", properties=dict(pop=80), geometry=dict(type="Point", coordinates=[500004, 2599990])),
        dict(type="Feature", properties=dict(pop=50), geometry=dict(type="Point", coordinates=[500095, 2600003]))])
    f = ("pts.geojson", json.dumps(gj).encode(), "application/geo+json")
    meta = C.post(f"/api/g/projects/{pid}/scenarios/base/loadbuilder", files=dict(file=f)).json()
    assert meta["fields"] == ["pop"] and meta["features"] == 3
    prev = C.post(f"/api/g/projects/{pid}/scenarios/base/loadbuilder?field=pop&scale=0.2", files=dict(file=f)).json()
    assert prev["report"]["structures"] == 2 and prev["report"]["total"] == pytest.approx(50.0) and "applied" not in prev["report"]
    C.post(f"/api/g/projects/{pid}/scenarios/base/loadbuilder?field=pop&scale=0.2&apply=true", files=dict(file=f))
    m = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()
    assert m["loads"]["design"] == {"A": pytest.approx(40.0), "B": pytest.approx(10.0)}
    C.post(f"/api/g/projects/{pid}/scenarios/base/undo")                       # one undo step
    assert not C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["loads"].get("design")


def test_trex_sets_ground_from_a_geotiff_and_keeps_depths(tmp_path):
    import rasterio
    from rasterio.transform import from_origin
    pid, ed = _proj(); tif = tmp_path / "dem.tif"
    z = np.fromfunction(lambda r, c: 120.0 - 0.01 * c, (50, 300))              # 1 m cells, falling 1 cm per metre eastwards
    with rasterio.open(tif, "w", driver="GTiff", height=50, width=300, count=1, dtype="float64", crs="EPSG:32640",
                       transform=from_origin(499950, 2600025, 1, 1), nodata=-9999) as w: w.write(z, 1)
    r = C.post(f"/api/g/projects/{pid}/scenarios/base/trex?keep_depth=true", files=dict(file=("dem.tif", tif.read_bytes(), "image/tiff"))).json()
    assert r["updated"] == 3
    n = {f["id"]: f["properties"] for f in C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["nodes"]["features"]}
    assert n["A"]["ground"] == pytest.approx(120.0 - 0.01 * 50, abs=0.011) and n["A"]["ground"] - n["A"]["invert"] == pytest.approx(2.0)


def test_rational_method_by_hand():
    p = Project("r", crs=32640)
    W.apply(p, dict(op="add_node", id="A", x=0, y=0, ground=10, invert=8)); W.apply(p, dict(op="add_node", id="O", kind="outfall", x=100, y=0, ground=9, invert=7))
    W.apply(p, dict(op="add_link", id="P", from_node="A", to_node="O", dn_mm=500))
    W.apply(p, dict(op="add_catchment", id="C1", outlet="A", area_ha=2.0, coords=[[0, 0], [100, 0], [100, 200], [0, 200]]))
    p.rain = dict(idf=dict(durations_min=[5, 10, 30, 60], intensities=[150.0, 120.0, 70.0, 45.0]))
    with pytest.raises(ValueError, match="runoff coefficient"): tools_v4.rational(p)
    W.apply(p, dict(op="set_hydrology", ids=["C1"], C=0.8, tc_min=10))
    rows, s = tools_v4.rational(p)
    assert rows["P"]["q_rational_ls"] == pytest.approx(0.8 * 120.0 * 2.0 / 360.0 * 1000.0, rel=1e-9)   # 533.3 L/s
    with pytest.raises(ValueError): W.apply(p, dict(op="set_hydrology", ids=["C1"], C=1.5))


def test_controls_and_curve_number_on_swmm():
    p = demo_pond.build()
    W.apply(p, dict(op="set_controls", rules=[dict(link="PMP-1", **{"if": "node"}, node="WW-1", op=">", value=1.2, then="ON", **{"else": "OFF"})]))
    W.apply(p, dict(op="set_hydrology", ids=["CM-1"], cn=85))
    p.settings["storm_infiltration"] = "curve_number"
    t = swmm_inp.from_project(p)
    assert "[CONTROLS]" in t and "IF NODE WW-1 DEPTH > 1.2" in t and "THEN PUMP PMP-1 STATUS = ON" in t
    assert "INFILTRATION CURVE_NUMBER" in t and "CM-1 85 0.5 7" in t
    r = storm.run(p); assert r["links"]["PMP-1"]["q_peak"] > 0
    with pytest.raises(ValueError, match="not a pump"): W.apply(p, dict(op="set_controls", rules=[dict(link="POS-1", **{"if": "time"}, op=">", value=1, then="ON")]))


def test_batch_run_and_calculation_option_sets():
    pid, ed = _proj()
    sc = C.post(f"/api/g/projects/{pid}/scenarios/base/copy", json={}).json()["created"]
    r = C.post(f"/api/g/projects/{pid}/batch", json=dict(sids=["base", sc])).json()["rows"]
    assert [x["id"] for x in r] == ["base", sc] and r[0]["conduits"] == 2
    assert ed(op="set_setting", path="calc_option_sets", value={"GVF with losses": {"flow_profile": "gvf", "structure_loss.K": 0.5}}).status_code == 200


# ---- the Fable 5.2 review of v4
def test_pumped_flows_keep_the_short_flag():
    import importlib, os, sys
    sys.path.insert(0, os.path.dirname(__file__)); tp = importlib.import_module("test_pressure")
    from sewerapp.engine import steady
    p = tp._station(dict(type="design_point", q_ls=50, h_m=20)); p.settings["pressure"]["use_pumped_flows"] = True
    r, s = steady.solve(p)
    assert bool(r.short["PU"]) and s["pressure"]["pumps_short"] == 1 and s["pumped_flows"]
    assert r.q_ls["G2"] == pytest.approx(r.op_q_ls["PU"], rel=1e-6) and r.q_ls["G2"] < 50      # downstream: what it pumps


def test_trex_off_the_raster_and_by_path(tmp_path):
    import rasterio
    from rasterio.transform import from_origin
    pid, ed = _proj(); tif = tmp_path / "small.tif"
    with rasterio.open(tif, "w", driver="GTiff", height=10, width=60, count=1, dtype="float64", crs="EPSG:32640",
                       transform=from_origin(499990, 2600005, 1, 1)) as w: w.write(np.full((10, 60), 115.0), 1)   # covers A only; no nodata tag
    r = C.post(f"/api/g/projects/{pid}/scenarios/base/trex?keep_depth=true&path={tif}").json()
    assert r["updated"] == 1 and r["no_data_count"] == 2
    n = {f["id"]: f["properties"] for f in C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["nodes"]["features"]}
    assert n["A"]["ground"] == 115.0 and n["B"]["ground"] == 109.5                            # B off the raster: kept


def test_controls_are_checked_and_pruned():
    p = demo_pond.build()
    with pytest.raises(ValueError, match="ON or OFF"): W.apply(p, dict(op="set_controls", rules=[dict(link="PMP-1", **{"if": "time"}, op=">", value=1, then="1")]))
    W.apply(p, dict(op="set_controls", rules=[dict(link="PMP-1", **{"if": "time"}, op=">", value=1, then="on")]))
    assert p.controls[0]["then"] == "ON"
    W.apply(p, dict(op="delete", table="links", ids=["PMP-1"])); assert p.controls == []


def test_set_inverts_moves_the_pipe_ends_with_them():
    p = Project("i", crs=32640)
    for i, x in enumerate((0, 100, 200)): W.apply(p, dict(op="add_node", id=f"N{i}", x=x, y=0, ground=10, invert=8 - i * 0.5))
    W.apply(p, dict(op="add_link", id="A", from_node="N0", to_node="N1")); W.apply(p, dict(op="add_link", id="B", from_node="N1", to_node="N2"))
    W.apply(p, dict(op="set_inverts", values={"N1": 7.0}))
    assert (p.links.dn_inv["A"], p.links.up_inv["B"], p.nodes.invert["N1"]) == (7.0, 7.0, 7.0)


def test_rational_on_a_pond_with_several_outlets():
    p = demo_pond.build()
    for o, x in (("O2", 632760.0), ("O3", 632770.0)): W.apply(p, dict(op="add_node", id=o, kind="outfall", x=x, y=2612000.0, ground=101.0, invert=99.0))
    W.apply(p, dict(op="add_link", id="OR-1", kind="orifice", from_node="BO-1", to_node="O2")); W.apply(p, dict(op="add_link", id="WR-1", kind="weir", from_node="BO-1", to_node="O3"))
    W.apply(p, dict(op="set_hydrology", ids=["CM-1"], C=0.9, tc_min=10))
    rows, s = tools_v4.rational(p)
    assert rows["POS-1"]["q_rational_ls"] > 0 and "OR-1" not in rows
