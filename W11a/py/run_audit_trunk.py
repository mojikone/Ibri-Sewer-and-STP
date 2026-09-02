"""Run the stage-0 auditor against the stage-3 trunk (W11a/shp/W11a_trunk.gpkg).

Separate from run_audit.py, which is pointed at W10's shapefiles by filename. This one goes
through contract.assert_audited_path() so a shapefile can never be handed to the auditor:
the DBF renames GRAD_BY to GRADIENT_B and audit G2 then fails a correct design.

    python run_audit_trunk.py
"""
import os, sys, warnings
warnings.filterwarnings("ignore")
import geopandas as gpd, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from w11a import audit, contract as K
from sewnet.criteria import DEFAULT as CRIT

BASE = os.path.dirname(os.path.dirname(K.REPO_ROOT))


def main(gpkg: str = "W11a_trunk.gpkg") -> int:
    p = K.gpkg_path(K.W11A_ROOT, gpkg)
    K.assert_audited_path(p, "reaches")
    pipes = gpd.read_file(p, layer="reaches")
    nodes = gpd.read_file(p, layer="nodes")
    roads = gpd.read_file(os.path.join(BASE, "Hydraulic", "SHP", "Road centerline 2",
                                       "Road_Centercline.shp")).set_crs(32640, allow_override=True)
    ctx = audit.Ctx(
        pipes=pipes, nodes=nodes, crit=CRIT,
        terrain=os.path.join(BASE, "Data", "Terrain", "Sat_0p5m", "IBRI_0p5_VRT2.vrt"),
        hazard=os.path.join(BASE, "Data", "04 Lekhuwair", "Hazard_T50y.tif"),
        roads=roads, plots=None,
        existing=gpd.read_file(os.path.join(K.REPO_ROOT, "W10", "shp",
                                            "W10_existing_built.shp")))
    print(f"auditing the W11a trunk: {len(pipes):,} reaches, {len(nodes):,} chambers\n")
    res = audit.run(ctx)
    print(audit.report(res))
    out = os.path.join(K.W11A_ROOT, "run", "audit_W11a_trunk.csv")
    pd.DataFrame([r.__dict__ for r in res]).to_csv(out, index=False)
    print(f"\nwritten to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
