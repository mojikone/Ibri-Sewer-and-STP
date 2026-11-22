"""The tools menu: every tested script reachable from the UI (rule: a script with no UI place is not done; the register
docs/SCRIPT_REGISTER.md lists the same entries). Each tool takes the project and a scenario and returns a table."""
import os, tempfile, time
import numpy as np, pandas as pd
from sewerapp.referee import golden, sewergems
from sewerapp.w18port import run as port

REGISTER = [
    dict(name="checks", menu="Checks", label="Failing pipes (d/D over Table 10, over 3 m/s, under 0.75 m/s at 2031)",
         script="engine/analysis.py", seconds="<1"),
    dict(name="selfcleansing", menu="Checks", label="Self-cleansing list: above DN200 under 0.75 m/s at the 2031 peak",
         script="engine/analysis.py (rule of w18port/final_selfcleansing.py)", seconds="<1"),
    dict(name="design_year_check", menu="Checks", label="Design-year check: the 2051 and 2061 designs at the 2056 peak",
         script="engine/design_year.py (port of W18 py/design_year_check.py)", seconds="<2"),
    dict(name="stations", menu="Stations", label="Pumping and lift stations: duty, force main, head, kW, MWh",
         script="w18port/final_products.py", seconds="<1"),
    dict(name="quantities", menu="Stations", label="Quantities of the design (km, stations, energy, deepest)",
         script="w18port/final_products.py", seconds="<1"),
    dict(name="design_chain", menu="Design", label="Re-run the W18 design chain on this base case and check it against W18 (a what-if's edits are not carried into the chain yet)",
         script="w18port/run.py (final_design, split, self-cleansing, naming, products)", seconds="about 40"),
    dict(name="compare_sewergems", menu="Referee", label="Compare with SewerGEMS's saved run (SC1-2056)",
         script="referee/sewergems.py", seconds="<2"),
    dict(name="swmm_examples", menu="Stormwater", label="Run EPA's SWMM examples and compare with EPA's reference results",
         script="engine/swmm.py", seconds="about 2"),
]


def _swmm_examples():
    import os, tempfile
    from sewerapp.engine import swmm
    w19 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fix, ref = os.path.join(w19, "tests", "fixtures", "swmm"), os.path.join(w19, "work", "swmm_ref")
    rows = []
    for folder, names in (("examples", [f"Example{i}" for i in range(1, 6)]),
                          ("extran", [f"extran{i}" for i in ("1", "2", "3", "4", "5", "6", "7", "8a", "9", "10")])):
        for n in names:
            r = swmm.run(os.path.join(fix, folder, n + ".inp"), tempfile.mkdtemp())
            row = dict(model=n, links=r["summary"]["links"], nodes=r["summary"]["nodes"], periods=r["summary"]["periods"],
                       seconds=r["seconds"])
            refdir = os.path.join(ref, n.replace("Example", "Example_") if n.startswith("Example") else n.replace("extran", "extran_"))
            if os.path.isdir(refdir):
                c = swmm.compare(r["out"], os.path.join(refdir, n + ".out"))
                row.update(matches_epa=c["ok"], worst_rel=max((s.get("worst_rel", 0) for s in c["series"]), default=0))
            rows.append(row)
    return dict(rows=rows)


def run(name, project, scenario):
    if name not in {t["name"] for t in REGISTER}: raise KeyError(name)
    if name == "swmm_examples": return _swmm_examples()
    if name == "design_year_check":
        from sewerapp.engine import design_year
        sc = scenario.case.case.split("-")[0]
        return dict(rows=[dict(design=f"{sc}-{y}", at_peak_of=f"{sc}-2056", **design_year.check(f"{sc}-{y}", f"{sc}-2056"))
                          for y in ("2051", "2061")])
    res, summ = project.results(scenario.id)
    if name == "checks":
        bad = res[res.over_limit | res.over_3ms | res.under075]
        return dict(summary=summ, rows=bad[["label", "dn_mm", "q_ls", "v_ms", "d_over_D", "limit", "v2031_ms",
                                            "over_limit", "over_3ms", "under075"]].round(4).to_dict("records"))
    if name == "selfcleansing":
        sc = res[res.under075]
        return dict(km=round(float(sc.length_m.sum() / 1000), 2), pipes=int(len(sc)),
                    rows=sc[["label", "dn_mm", "length_m", "s_pc", "q2031_ls", "v2031_ms"]].round(4).to_dict("records"))
    if name == "stations":
        return dict(rows=scenario.case.stations.round(3).to_dict("records"))
    if name == "quantities":
        return dict(rows=[dict(item=k, value=v) for k, v in scenario.case.quantities.items()])
    if name == "design_chain":
        case = scenario.case.case; t0 = time.perf_counter()
        root = port.build_workroot(tempfile.mkdtemp(prefix="w19chain_"), [case], seed_cuts=False)
        info = port.run_cases(root, [case])
        diffs = golden.engineering_differences(os.path.join(root, port.SUB, case), case)
        return dict(case=case, passes=info["passes"], seconds=round(time.perf_counter() - t0, 1),
                    equal_to_w18=not diffs, differences=diffs[:20])
    if name == "compare_sewergems":
        if scenario.case.case != "SC1-2056": return dict(error="SewerGEMS's saved run exists for SC1-2056 only")
        from sewerapp import fixtures
        d = tempfile.mkdtemp()
        for rel in ("named/links.csv", "exports/conduits_SC1-2056a.csv"):
            fixtures.materialize(f"golden/SC1-2056/{rel}", os.path.join(d, rel))
        return sewergems.compare(d)
