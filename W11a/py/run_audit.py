"""Run the W11a auditor against a design. Stage 0.

Pointed at W10 by default, because the philosophy says to run it against the existing
layers on day one and let the failing table be the specification.

    python run_audit.py
"""
import os, sys, warnings
import geopandas as gpd
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "W8", "py"))

from w11a import audit
from sewnet.criteria import DEFAULT as CRIT

BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"

def load(p, **kw):
    try:
        return gpd.read_file(p, **kw)
    except Exception:
        return None

def main(target="W10"):
    d = os.path.join(ROOT, target, "shp")
    roads = load(BASE + r"\Hydraulic\SHP\Road centerline 2\Road_Centercline.shp")
    if roads is not None:
        roads = roads.set_crs(32640, allow_override=True)
    ctx = audit.Ctx(
        pipes=load(os.path.join(d, f"{target}_pipes.shp")),
        nodes=load(os.path.join(d, f"{target}_nodes_depth.shp")),
        crit=CRIT,
        hazard=BASE + r"\Data\04 Lekhuwair\Hazard_T50y.tif",
        roads=roads,
        existing=load(os.path.join(ROOT, "W10", "shp", "W10_existing_built.shp")),
    )
    if ctx.pipes is None:
        print(f"no pipe layer for {target}"); return
    print(f"auditing {target}: {len(ctx.pipes):,} pipes\n")
    res = audit.run(ctx)
    print(audit.report(res))
    import pandas as pd
    out = os.path.join(ROOT, "W11a", "run", f"audit_{target}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pd.DataFrame([r.__dict__ for r in res]).to_csv(out, index=False)
    print(f"\nwritten to {out}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "W10")
