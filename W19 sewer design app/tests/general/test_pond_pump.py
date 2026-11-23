"""A pond that takes rain, fills, and a pump that starts at its depth and empties it (the engineer's pond model, built in
the app, 2026-11-23): storage area or depth-area table and the pump's capacity and start/stop depths reach SWMM 5."""
import numpy as np
import pytest
from sewerapp.model.general import Project
from sewerapp.model import workspace as W
from sewerapp.io import swmm_inp, gpkg_project
from sewerapp.engine import storm


def _pond(curve=False):
    p = Project("pond", crs=32640)
    W.apply(p, dict(op="add_node", id="POND", kind="storage", x=0, y=0, ground=103.0, invert=100.0))
    W.apply(p, dict(op="add_node", id="OUT", kind="outfall", x=60, y=0, ground=104.0, invert=103.0))
    W.apply(p, dict(op="add_link", id="PMP", kind="pump", from_node="POND", to_node="OUT"))
    W.apply(p, dict(op="add_catchment", id="C1", outlet="POND", area_ha=2.0, imperv_pc=100, width_m=140, slope_pc=0.5,
                    coords=[[0, 0], [140, 0], [140, 140], [0, 140]]))
    if curve: W.apply(p, dict(op="set_storage", ids=["POND"], curve=[[0, 900], [1, 1100], [3, 1500]]))
    else: W.apply(p, dict(op="set_storage", ids=["POND"], area_m2=1000.0))
    W.apply(p, dict(op="set_pump", ids=["PMP"], q_ls=80.0, on_m=1.0, off_m=0.3))
    p.rain = dict(step_min=5, series=[[0, 120.0], [5, 120.0], [10, 120.0], [15, 120.0], [20, 120.0], [25, 120.0], [30, 0.0]])   # 60 mm on 2 ha: 1,200 m3
    return p


def test_the_pond_and_the_pump_are_written_to_swmm():
    t = swmm_inp.from_project(_pond(curve=True))
    assert "POND" in t and "TABULAR" in t and "ST_POND" in t and "PC_PMP" in t and "Pump2" in t
    row = next(l for l in t.splitlines() if l.startswith("PMP "))
    assert row.split()[3:] == ["PC_PMP", "ON", "1", "0.3"]
    t2 = swmm_inp.from_project(_pond(curve=False))
    srow = next(l for l in t2.splitlines() if l.startswith("POND ") and "FUNCTIONAL" in l)
    assert srow.split()[4:8] == ["FUNCTIONAL", "0", "0", "1000"]


def test_rain_fills_the_pond_and_the_pump_starts_at_its_depth():
    r = storm.run(_pond())
    d = storm.series(r["out"], "node", "POND", "invert_depth"); q = storm.series(r["out"], "link", "PMP", "flow_rate")
    depth = np.array([v for _, v in d]); flow = np.array([v for _, v in q])
    on = np.argmax(flow > 1e-6)
    assert depth[:on].max() < 1.0 + 0.05 and depth[on] >= 1.0 - 0.05            # nothing pumped until the start depth
    assert flow.max() == pytest.approx(0.080, rel=0.01)                           # its capacity, m3/s
    assert depth.max() > 1.0 and r["nodes"]["POND"]["depth_peak"] > 1.0
    assert depth[-1] < 1.0                                                        # drained down after the rain


def test_pond_and_pump_survive_the_file(tmp_path):
    p = _pond(curve=True); f = tmp_path / "p.gpkg"; gpkg_project.save(p, str(f)); q = gpkg_project.load(str(f))[0]
    assert q.storage == p.storage and q.pumps == p.pumps
    with pytest.raises(ValueError, match="lower depth"): W.apply(p, dict(op="set_pump", ids=["PMP"], q_ls=10, on_m=0.5, off_m=0.8))
    with pytest.raises(ValueError, match="not a pump"): W.apply(p, dict(op="set_pump", ids=["POND"], q_ls=10))


def test_the_pond_demo_sample_opens_and_its_pump_starts():
    from fastapi.testclient import TestClient
    from sewerapp.api.app import app
    from sewerapp.io import demo_pond
    C = TestClient(app)
    assert any(s["id"] == "pond" for s in C.get("/api/g/samples").json())
    pid = C.post("/api/g/projects/sample/pond").json()["id"]
    m = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()
    kinds = {f["id"]: f["properties"]["kind"] for f in m["nodes"]["features"]}
    assert kinds == {"BO-1": "storage", "WW-1": "wetwell", "J-1": "outfall"}
    assert next(f for f in m["links"]["features"] if f["id"] == "PMP-1")["properties"]["pump"]["on_m"] == 1.0
    r = storm.run(demo_pond.build())
    assert r["links"]["PMP-1"]["q_peak"] == pytest.approx(0.120, rel=0.01) and r["nodes"]["WW-1"]["depth_peak"] >= 1.0
