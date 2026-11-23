"""Dry-weather flow with an hourly pattern on SWMM, and the user notifications (2026-11-23 v3)."""
import numpy as np
import pytest
from sewerapp.engine import storm, validate
from sewerapp.io import swmm_inp
from sewerapp.model.general import Project
from sewerapp.model import workspace as W

PAT = [0.4] * 6 + [1.6] * 6 + [1.2] * 6 + [0.8] * 6                       # mean 1.0


def _line():
    p = Project("dwf", crs=32640)
    for i, (x, g) in enumerate([(0, 102.0), (100, 101.5)]): W.apply(p, dict(op="add_node", id=f"N{i}", x=x, y=0, ground=g, invert=g - 2))
    W.apply(p, dict(op="add_node", id="O", kind="outfall", x=200, y=0, ground=101.0, invert=99.0))
    W.apply(p, dict(op="add_link", id="A", from_node="N0", to_node="N1", dn_mm=200)); W.apply(p, dict(op="add_link", id="B", from_node="N1", to_node="O", dn_mm=200))
    p.load_sets["design"] = {"N0": 864.0}                                     # 10 L/s average
    p.settings["libraries"]["patterns"] = [dict(name="Diurnal", hourly=PAT)]
    W.apply(p, dict(op="set_setting", path="swmm_dwf", value=dict(on=True, load_set="design", pattern="Diurnal", hours=48)))
    return p


def test_dry_weather_follows_its_pattern_on_swmm():
    p = _line(); t = swmm_inp.from_project(p)
    assert "[DWF]" in t and "N0 FLOW 0.01" in t and "DW_Diurnal HOURLY" in t and "END_DATE 01/03/2026" in t
    r = storm.run(p)
    q = np.array([v for _, v in storm.series(r["out"], "link", "B", "flow_rate")])
    day2 = q[len(q) // 2:]                                                     # the second day, settled
    assert day2.max() == pytest.approx(0.016, rel=0.05) and day2.min() == pytest.approx(0.004, rel=0.1)


def test_notifications():
    p = _line(); W.apply(p, dict(op="add_node", id="LONE", x=500, y=500, ground=100, invert=98))
    W.apply(p, dict(op="add_node", id="UP", x=0, y=50, ground=100, invert=101))           # invert above ground
    W.apply(p, dict(op="add_link", id="C", from_node="N0", to_node="UP", dn_mm=200))      # N0 now has two leaving pipes
    items = validate.run(p)
    msg = {(i["id"], i["level"]): i["message"] for i in items}
    assert ("N0", "error") in msg and "tree" in msg[("N0", "error")]
    assert ("UP", "error") in msg and ("LONE", "warning") in msg
    assert items[0]["level"] == "error"
