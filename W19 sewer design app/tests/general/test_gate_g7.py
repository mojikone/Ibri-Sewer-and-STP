"""Gate G7: a SewerGEMS model exported through the documented API (the format of bridge job 100) opens with all its
scenarios and SewerGEMS's own results. Tested on the frozen export of W18's referee run of SC1-2056 (design year and
the 2031 check), laid out as job 100 writes it."""
import os, shutil
import numpy as np, pandas as pd, pytest
from fastapi.testclient import TestClient
from sewerapp import fixtures
from sewerapp.api import general_api
from sewerapp.api.app import app

C = TestClient(app)


@pytest.fixture()
def export(tmp_path, monkeypatch):
    d = tmp_path / "SC1-2056_final"; d.mkdir()
    fixtures.materialize("sewergems/SC1-2056/conduits_SC1-2056.csv", str(d / "conduits_s001.csv"))
    fixtures.materialize("sewergems/SC1-2056/conduits_SC1-2056-at-2031.csv", str(d / "conduits_s002.csv"))
    for f in ("s001", "s002"): fixtures.materialize("sewergems/SC1-2056/manholes_SC1-2056.csv", str(d / f"manholes_{f}.csv"))
    fixtures.materialize("sewergems/SC1-2056/loads_design.csv", str(d / "loads_s001.csv"))
    fixtures.materialize("sewergems/SC1-2056/loads_at_2031.csv", str(d / "loads_s002.csv"))
    fixtures.materialize("sewergems/SC1-2056/support_loads.csv", str(d / "support_loads.csv"))
    (d / "scenarios.csv").write_text('id,label,parent,file\n1,"SC1-2056 design",0,s001\n2,"SC1-2056 design at the 2031 peak",1,s002\n')
    monkeypatch.setattr(general_api, "SG_EXPORTS", str(tmp_path))
    return d


@pytest.mark.gate_g7
def test_open_a_sewergems_export_with_all_scenarios(export):
    assert C.get("/api/g/sewergems/exports").json() == [dict(name="SC1-2056_final", scenarios=2)]
    info = C.post("/api/g/projects/open_sewergems/SC1-2056_final").json()
    assert [s["name"] for s in info["scenarios"]] == ["SC1-2056 design", "SC1-2056 design at the 2031 peak"]
    pid = info["id"]; sid2 = info["scenarios"][1]["id"]
    m = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()
    assert len(m["links"]["features"]) >= 19083 and len(m["nodes"]["features"]) >= 19000
    a = C.get(f"/api/g/projects/{pid}/scenarios/base/stored").json()["links"]
    b = C.get(f"/api/g/projects/{pid}/scenarios/{sid2}/stored").json()["links"]
    sg = fixtures.read_csv("sewergems/SC1-2056/conduits_SC1-2056.csv").set_index("label")
    lab = "P1-P1"
    assert abs(a[lab]["q_ls"] - sg.flow_m3d[lab] / 86.4) < 1e-3 and b[lab]["q_ls"] < a[lab]["q_ls"]     # 2031 below the design year
    assert not info["scenarios"][1]["can_undo"]              # the model's own scenario definition is not an undoable edit
    r = C.post(f"/api/g/projects/{pid}/scenarios/{sid2}/undo").json()
    assert not r["scenario"]["can_undo"] and r["scenario"]["edits"] == info["scenarios"][1]["edits"]
    dd = pd.Series({k: v["d_over_D"] for k, v in a.items()})
    assert dd.max() <= 0.655                                 # no pipe over its d/D limit in SewerGEMS's own run (W18's referee)


@pytest.mark.gate_g7
def test_the_job_file_is_intact():
    f = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "referee", "jobs", "100_w19_export_scenarios.ps1")
    t = open(f, encoding="utf-8").read()
    assert "\\\\VBOXSVR\\VBOX\\bridge\\lib\\load.ps1" in t and "\f" not in t and "\b" not in t and "SaveAs($work)" in t


@pytest.mark.gate_g7
def test_the_app_re_solves_the_sewergems_model_from_its_own_loads(export):
    """Loads (unit and pattern) and the peaking table exported by bridge job 103: the app's engine re-solves SewerGEMS's
    model and every pipe's flow equals SewerGEMS's stored flow within 0.1 %, in both scenarios."""
    info = C.post("/api/g/projects/open_sewergems/SC1-2056_final").json(); pid = info["id"]
    m = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()
    assert m["settings"]["peaking"]["table"][0] == [pytest.approx(0.1, rel=1e-6), 4.66]      # the model's own table
    for sc in info["scenarios"]:
        r = C.get(f"/api/g/projects/{pid}/scenarios/{sc['id']}/compare_stored").json()
        assert r["links"] >= 19083 and r["pc_flow_within_0_1"] == 100.0, (sc["name"], r)
