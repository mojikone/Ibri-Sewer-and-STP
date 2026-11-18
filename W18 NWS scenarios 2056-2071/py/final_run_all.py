"""W18 final design: the whole chain for the 12 cases (SC1-SC4 x 2051/2056/2061), repeated until the lift stations no
longer change: design with every lift pumping its peak as a transfer (final_design.py --lifts), the split with the
station sets of fixed_stations.json, then the self-cleansing check, the naming and the products.
Usage: python final_run_all.py      (parallel, one process per case)"""
import os, sys, subprocess, json, filecmp, shutil
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4")
CASES = [f"{s}-{y}" for s in ("SC1", "SC2", "SC3", "SC4") for y in ("2051", "2056", "2061")]
PY = sys.executable


def run(args, log):
    with open(log, "a", encoding="utf-8") as f:
        r = subprocess.run([PY] + args, cwd=HERE, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode: raise RuntimeError(f"{args} failed, see {log}")


def design_and_split(c):
    s, y = c.split("-"); log = os.path.join(R, c, "chain.log")
    cuts = os.path.join(R, c, "split", f"cuts_{c}.csv"); before = cuts + ".before"
    shutil.copy(cuts, before)
    run(["final_design.py", s, y, "--lifts"], log)
    run(["split_deep_subnetworks.py", c, os.path.join(R, c, "exports"), os.path.join(R, c, "split"), "0.0075",
         "--fixed=" + os.path.join(R, "fixed_stations.json")], log)
    same = filecmp.cmp(before, cuts, shallow=False); os.remove(before)
    return c, same


for it in range(1, 5):
    with ThreadPoolExecutor(12) as ex: res = list(ex.map(design_and_split, CASES))
    changed = [c for c, same in res if not same]
    print(f"pass {it}: lift stations changed in {changed or 'no case'}")
    if not changed: break
run(["final_selfcleansing.py"], os.path.join(R, "chain.log"))
with ThreadPoolExecutor(12) as ex: list(ex.map(lambda c: run(["final_naming.py", c], os.path.join(R, c, "chain.log")), CASES))
with ThreadPoolExecutor(12) as ex: list(ex.map(lambda c: run(["final_products.py", c], os.path.join(R, c, "chain.log")), CASES))
for c in CASES:
    S = json.load(open(os.path.join(R, c, "split", f"summary_{c}.json"))); Q = json.load(open(os.path.join(R, c, "products", "quantities.json")))
    print(f"{c}: stations {S['stations']} ({Q['pumps']} pumps, {Q['lifts']} lifts), above DN200 under 0.75 m/s 2031 {Q['km_big_under075_2031']:.1f} km, "
          f"2036 {Q['km_big_under075_2036']:.1f} km, deepest {Q['deepest']['depth']:.2f} m, kept deep: "
          + ", ".join(f"{o['name']} {o['depth_m']:.2f}" for o in S["outfalls_over12"]))
