"""A SewerGEMS model read directly from its database (io/sewergems_db.py, 2026-11-24) against SewerGEMS's own API export
of the same model: the Ibri SC1-2056 final model, its Base and its "SC1-2056 design" scenario. On this computer only
(the model and the export are not in the repository)."""
import os
import numpy as np, pandas as pd
import pytest
from sewerapp.io import sewergems_db, sewergems_export

DB = r"D:\VBOX\bridge\out\w18\final_models\IBRI_SC1-2056_final.stsw.sqlite"
API = r"D:\VBOX\bridge\out\w19\export\SC1-2056_final"
pytestmark = pytest.mark.skipif(not (os.path.exists(DB) and os.path.isdir(API)), reason="the Ibri model and its export are on the engineer's computer only")


def test_direct_reading_equals_sewergems_export(tmp_path):
    out = str(tmp_path / "m")
    sc = sewergems_db.export(DB, out, only={1, 279818})
    assert [s["label"] for s in sc] == ["Base", "SC1-2056 design"]
    api = pd.read_csv(os.path.join(API, "scenarios.csv")).set_index("id")
    for s in sc:
        f_api = api.file[s["id"]]
        for kind, cols in (("manholes", ["x", "y", "ground", "invert"]), ("conduits", ["start", "stop", "length_m", "diameter_mm", "start_inv", "stop_inv"])):
            A = pd.read_csv(os.path.join(API, f"{kind}_{f_api}.csv")).set_index("id"); B = pd.read_csv(os.path.join(out, f"{kind}_{s['file']}.csv")).set_index("id")
            assert set(A.index) == set(B.index), kind
            for c in cols: assert float((A[c] - B.loc[A.index, c]).abs().max()) < 1e-4, (kind, c)
            assert (A.active.astype(bool) == B.loc[A.index, "active"].astype(bool)).all()
        A = pd.read_csv(os.path.join(API, f"loads_{f_api}.csv")).set_index("element_id"); B = pd.read_csv(os.path.join(out, f"loads_{s['file']}.csv")).set_index("element_id")
        k = A.index.union(B.index)
        assert float((A.unit_m3d.reindex(k).fillna(0) - B.unit_m3d.reindex(k).fillna(0)).abs().max()) < 1e-6
    p, scen, res = sewergems_export.load(out, "direct", 32640)                  # and it opens as the export does
    assert len(p.nodes) == 19312 and (p.nodes.kind == "outfall").sum() == 32 and p.settings["peaking"]["method"] == "table"


POND = r"D:\VBOX\bridge\models\Pond_Mouj\Pond_Mouj.stsw.sqlite"
IB01 = r"C:\Users\mojtaba\Desktop\Win10 shared folder\IBRI Sewer\IBRI Sewer 01\IBRI Sewer 01.stsw.sqlite"


@pytest.mark.skipif(not os.path.exists(POND), reason="the engineer's Pond_Mouj model is on this computer only")
def test_a_pump_and_its_force_main_read_directly(tmp_path):
    """Pond_Mouj: SewerGEMS's pump node between pressure pipes becomes the app's pump from the pond outlet to a junction
    at the pump, and the force main's pressure pipe (141.35 m, 0.5 ft bore, C 130) follows it, at the positions
    SewerGEMS's own export gives."""
    out = str(tmp_path / "pond"); sewergems_db.export(POND, out)
    p, _, _ = sewergems_export.load(out, "pond", 32640)
    assert p.links.kind.to_dict() == {"PMP-1": "pump", "P-2": "pressure_pipe"}
    assert (p.links.from_node["PMP-1"], p.links.to_node["PMP-1"]) == ("POS-1", "PMP-1-out") and p.links.to_node["P-2"] == "J-1"
    assert abs(p.links.length_m["P-2"] - 141.3508) < 1e-3 and abs(p.links.inside_mm["P-2"] - 152.4) < 1e-6 and p.ppipes["P-2"]["C"] == 130.0
    assert abs(p.nodes.x["POS-1"] - 632717.810) < 1e-3 and abs(p.nodes.y["J-1"] - 2612167.670) < 1e-3


@pytest.mark.skipif(not os.path.exists(IB01), reason="the engineer's IBRI Sewer 01 model is on this computer only")
def test_a_pump_definition_and_a_station_switched_off(tmp_path):
    """IBRI Sewer 01: the wet well W-2, its pump PMP-1 with a three-point curve typed in metres (shutoff 14 m, design
    18.86 L/s at 10.85 m, maximum 75 m3/h at 9.5 m), the suction through J-1 left out; the station is switched off in
    every scenario, so, as in SewerGEMS, it is not part of the network that runs."""
    out = str(tmp_path / "ib01"); sewergems_db.export(IB01, out, only={1, 279726})
    t = pd.read_csv(os.path.join(out, "pressure_s002.csv")).set_index("label")
    assert t.kind["PMP-1"] == "pump" and t.definition["PMP-1"] == "Pump Definition - 1" and abs(t.q_ls["PMP-1"] - 18.858) < 1e-3
    assert "P-3" not in t.index and "P-4" not in t.index                         # the suction, inside the station
    d = pd.read_csv(os.path.join(out, "pump_definitions.csv")).iloc[0]
    assert d.type == "three_point" and abs(d.shutoff_h_m - 14.0) < 1e-6 and abs(d.h_m - 10.85) < 1e-6 and abs(d.max_q_ls - 75 / 3.6) < 1e-4 and abs(d.max_h_m - 9.5) < 1e-6
    p, _, _ = sewergems_export.load(out, "ib01", 32640)
    assert not (p.links.kind == "pump").any() and p.settings["libraries"]["pumps"][0]["name"] == "Pump Definition - 1"
