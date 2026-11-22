"""Gate G4 (stormwater): every EPA SWMM example imported into the app's model, exported and run gives the original
file's results at every step of every series (same engine, worst difference 0); an edited conduit size is carried into
the written file and moves the result; a network drawn from blank with catchments and an IDF design storm runs end to
end with small continuity errors."""
import os, tempfile
import pytest
from sewerapp.engine import storm, swmm
from sewerapp.io import swmm_inp
from sewerapp.model.general import Project
from sewerapp.model.workspace import apply

W19 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(W19, "tests", "fixtures", "swmm")
MODELS = [("examples", f"Example{i}") for i in range(1, 6)] + [("extran", f"extran{i}") for i in ("1", "2", "3", "4", "5", "6", "7", "8a", "9", "10")]


def _load(folder, name):
    return swmm_inp.to_project(open(os.path.join(F, folder, name + ".inp"), encoding="utf-8", errors="ignore").read(), name)


@pytest.mark.gate_g4
@pytest.mark.parametrize("folder,name", MODELS)
def test_import_export_run_equals_the_original(folder, name):
    p = _load(folder, name)
    r = storm.run(p, support_dir=os.path.join(F, folder))
    o = swmm.run(os.path.join(F, folder, name + ".inp"), tempfile.mkdtemp())
    c = swmm.compare(r["out"], o["out"])
    assert c["ok"] and max((s.get("worst_rel", 0) for s in c["series"]), default=0) == 0.0, c["series"]


@pytest.mark.gate_g4
def test_an_edited_size_is_written_and_moves_the_result():
    p = _load("extran", "extran1"); lid = p.links.index[0]; before = storm.run(p)
    apply(p, dict(op="set", table="links", ids=[lid], field="dn_mm", value=float(p.links.inside_mm[lid] * 0.6)))
    text = swmm_inp.from_project(p)
    row = next(l for l in text.split("[XSECTIONS]")[1].splitlines() if l.split() and l.split()[0] == lid)
    assert abs(float(row.split()[2]) - p.links.inside_mm[lid] / 304.8) < 1e-9          # US model: feet
    after = storm.run(p)
    assert after["links"][lid]["q_peak"] != before["links"][lid]["q_peak"]


@pytest.mark.gate_g4
def test_drawn_storm_network_runs_end_to_end():
    p = Project(name="drawn storm"); p.load_sets = {"design": {}}
    for i, (x, g) in enumerate([(0, 10.0), (120, 9.6), (240, 9.2)]):
        apply(p, dict(op="add_node", id=f"J{i}", kind="manhole", x=x, y=0, ground=g, invert=g - 1.8))
    apply(p, dict(op="add_node", id="OUT", kind="outfall", x=360, y=0, ground=8.8, invert=7.0))
    for a, b in (("J0", "J1"), ("J1", "J2"), ("J2", "OUT")): apply(p, dict(op="add_link", from_node=a, to_node=b, dn_mm=630))
    apply(p, dict(op="add_catchment", id="C1", outlet="J0", area_ha=4.0, imperv_pc=65, width_m=200, slope_pc=1.0,
                  coords=[[0, 20], [100, 20], [100, 120], [0, 120], [0, 20]]))
    apply(p, dict(op="add_catchment", id="C2", outlet="J1", area_ha=3.0, imperv_pc=50, width_m=150, slope_pc=1.5))
    p.rain = dict(step_min=5, duration_min=60, idf=dict(durations_min=[5, 10, 15, 30, 60, 120],
                                                        intensities=[150, 115, 95, 65, 42, 26]))   # a test curve, mm/h
    r = storm.run(p)
    assert r["subcatchments"]["C1"]["runoff_peak"] > 0 and r["links"]["P-3"]["q_peak"] > r["links"]["P-1"]["q_peak"] > 0
    ce = r["summary"]["continuity_error_pc"]
    assert abs(ce["Runoff Quantity Continuity"]) < 1.0 and abs(ce["Flow Routing Continuity"]) < 1.0, ce
    hy = swmm_inp.design_storm(p.rain["idf"], 60, 5)
    assert len(hy) == 12 and max(v for _, v in hy) == pytest.approx(150, rel=1e-9)     # peak block = the 5-min intensity
    assert sum(v * 5 / 60 for _, v in hy) == pytest.approx(42, rel=1e-9)                # total depth = 60-min depth
