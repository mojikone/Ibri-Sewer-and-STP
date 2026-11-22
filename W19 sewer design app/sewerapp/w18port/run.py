"""Runs the ported W18 chain for chosen cases in a work root built from the fixtures, laid out as W18's folder so the
scripts read it unchanged. Mirrors W18's final_run_all.py: design + split, repeated until the lift stations stop
changing, then self-cleansing, naming and products. Never writes into W18."""
import filecmp, os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from sewerapp import fixtures

PORT = os.path.dirname(os.path.abspath(__file__))
W19 = os.path.dirname(os.path.dirname(PORT))
SUB = os.path.join("results", "final_0.75pc_SC1-SC4")
CASES = [f"{s}-{y}" for s in ("SC1", "SC2", "SC3", "SC4") for y in ("2051", "2056", "2061")]
LAYOUT = {                                          # fixture -> place in the work root
    "inputs/catalogue.csv": f"{SUB}/inputs/catalogue.csv",
    "inputs/conduits_network.csv": f"{SUB}/inputs/conduits_network.csv",
    "inputs/conduits_start_sizes.csv": f"{SUB}/inputs/conduits_start_sizes.csv",
    "inputs/manholes_network.csv": f"{SUB}/inputs/manholes_network.csv",
    "inputs/fixed_stations.json": f"{SUB}/fixed_stations.json",
    "inputs/manhole_loads.csv": "results/loads/manhole_loads.csv",
    "inputs/rising_mains.csv": "results/rising_mains.csv",
    "inputs/rising_mains.gpkg": "results/rising_mains.gpkg",
    "bridge/inv/rename_nodes.csv": "bridge/inv/rename_nodes.csv",
    "geo/S1.gpkg": "geo/S1.gpkg",
}


def build_workroot(root, cases, seed_cuts=True):
    root = os.path.abspath(root)                    # the scripts run with the port folder as cwd
    for rel, dst in LAYOUT.items():
        fixtures.materialize(rel, os.path.join(root, dst))
    for f in os.listdir(os.path.join(fixtures.FIX, "bridge", "f0")):
        fixtures.materialize(f"bridge/f0/{f}", os.path.join(root, "bridge", "f0", f))
    for c in cases:
        os.makedirs(os.path.join(root, SUB, c, "split"), exist_ok=True)
        if seed_cuts:
            fixtures.materialize(f"golden/{c}/split/cuts_{c}.csv", os.path.join(root, SUB, c, "split", f"cuts_{c}.csv"))
    return root


def _run(args, root, log, extra=None):
    env = dict(os.environ, W19_CASE_ROOT=root, PYTHONPATH=W19, **(extra or {}))
    with open(log, "a", encoding="utf-8") as f:
        r = subprocess.run([sys.executable] + args, cwd=PORT, env=env, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode:
        raise RuntimeError(f"{args} failed, see {log}")


def _design_and_split(root, case):
    s, y = case.split("-"); R = os.path.join(root, SUB, case); os.makedirs(R, exist_ok=True)
    log = os.path.join(R, "chain.log")
    cuts = os.path.join(R, "split", f"cuts_{case}.csv"); before = cuts + ".before"
    had = os.path.exists(cuts)
    if had: shutil.copy(cuts, before)
    _run(["final_design.py", s, y, "--lifts"], root, log)
    _run(["split_deep_subnetworks.py", case, os.path.join(R, "exports"), os.path.join(R, "split"), "0.0075",
          "--fixed=" + os.path.join(root, SUB, "fixed_stations.json")], root, log)
    same = had and filecmp.cmp(before, cuts, shallow=False)
    if had: os.remove(before)
    return same


def run_cases(root, cases, max_passes=4, workers=None):
    workers = workers or min(len(cases), os.cpu_count() or 4)
    t0 = time.perf_counter()
    todo = list(cases)
    for it in range(1, max_passes + 1):
        with ThreadPoolExecutor(workers) as ex:
            same = list(ex.map(lambda c: _design_and_split(root, c), todo))
        todo = [c for c, ok in zip(todo, same) if not ok]
        if not todo: break
    t1 = time.perf_counter()
    _run(["final_selfcleansing.py"], root, os.path.join(root, SUB, "chain.log"), {"W19_CASES": ",".join(cases)})
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda c: _run(["final_naming.py", c], root, os.path.join(root, SUB, c, "chain.log")), cases))
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda c: _run(["final_products.py", c], root, os.path.join(root, SUB, c, "chain.log")), cases))
    return dict(passes=it, unconverged=todo, seconds_design_split=round(t1 - t0, 1),
                seconds_total=round(time.perf_counter() - t0, 1))
