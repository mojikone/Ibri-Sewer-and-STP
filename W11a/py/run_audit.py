"""Run the W11a auditor against a design. Stage 0.

Pointed at W10 by default, because the philosophy says to run it against the existing
layers on day one and let the failing table be the specification.

    python run_audit.py            # W10, published as shapefiles
    python run_audit.py W11a       # the current design, published into W11a.gpkg

W10 published shapefiles under its own names; W11a publishes the contract's canonical layers
into a GeoPackage. This script read only the W10 shapefile names, so `run_audit.py W11a`
found nothing and reported a design that exists as though it did not - which is precisely the
failure the auditor exists to catch, committed by its own runner.
"""
import os
import sys
import warnings

import geopandas as gpd

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "W8", "py"))

from w11a import audit                            # noqa: E402
from sewnet.criteria import DEFAULT as CRIT       # noqa: E402

BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"
P_ROADS = os.path.join(BASE, "Hydraulic", "SHP", "Road centerline 2",
                       "Road_Centercline.shp")
P_HAZARD = os.path.join(BASE, "Data", "04 Lekhuwair", "Hazard_T50y.tif")


def load(p, **kw):
    try:
        return gpd.read_file(p, **kw)
    except Exception:
        return None


def gpkg_layers(path, want):
    """Read the named layers from a GeoPackage; None for any that is absent."""
    import fiona
    try:
        have = set(fiona.listlayers(path))
    except Exception:
        return {k: None for k in want}
    return {k: (gpd.read_file(path, layer=k) if k in have else None) for k in want}


def main(target="W10"):
    roads = load(P_ROADS)
    if roads is not None:
        roads = roads.set_crs(32640, allow_override=True)
    existing = load(os.path.join(ROOT, "W10", "shp", "W10_existing_built.shp"))

    gpkg = os.path.join(ROOT, target, "shp", target + ".gpkg")
    if os.path.exists(gpkg):
        lyr = gpkg_layers(gpkg, ("reaches", "nodes", "crossings"))
        pipes, nodes, crossings = lyr["reaches"], lyr["nodes"], lyr["crossings"]
        where = os.path.basename(gpkg) + " [reaches, nodes, crossings]"
    else:
        d = os.path.join(ROOT, target, "shp")
        pipes = load(os.path.join(d, target + "_pipes.shp"))
        nodes = load(os.path.join(d, target + "_nodes_depth.shp"))
        crossings = None
        where = target + "_pipes.shp / " + target + "_nodes_depth.shp"

    if pipes is None:
        print("no pipe layer for " + target + " - looked in " + where)
        return 1

    ctx = audit.Ctx(pipes=pipes, nodes=nodes, crit=CRIT, hazard=P_HAZARD, roads=roads,
                    crossings=crossings, existing=existing)

    bits = ["auditing {}: {:,} pipes".format(target, len(pipes))]
    if nodes is not None:
        bits.append("{:,} chambers".format(len(nodes)))
    # Say when the register is absent. Without it nothing counts as a scheduled crossing,
    # every wadi crossing reads as a breach, and the run looks far worse than the design is.
    bits.append("NO crossings register - nothing counts as scheduled" if crossings is None
                else "{:,} crossings registered".format(len(crossings)))
    print(", ".join(bits))
    print()

    res = audit.run(ctx)
    print(audit.report(res))

    import pandas as pd
    out = os.path.join(ROOT, "W11a", "run", "audit_{}.csv".format(target))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pd.DataFrame([r.__dict__ for r in res]).to_csv(out, index=False)
    print()
    print("written to " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "W10"))
