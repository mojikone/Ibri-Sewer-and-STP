"""Phase 0.1 - turn the draftsman's DXF into a corridor layer we can design on.

The file carries two layers and BOTH are design input (user 2026-09-01):
  "piping center line"          - treated centre lines on existing roads
  "piping center line-propo-01" - roads missing from the road layer, and roads in future
                                  developments. Every plot must be served, so these are
                                  corridors, not proposals.

Polyline bulges are flattened through ezdxf.path so arcs do not become chords, and the
result is written with SRC='draft' so that anything we generate ourselves later stays
distinguishable and his next delivery can be re-merged without overwriting.

What this script reports, because each one changes the design:
  * how much of each layer sits on a dual carriageway, where no pipe may be laid at all
  * how much the two layers duplicate each other
  * how many plots have no corridor within reach, which is the work still to do

Run:  python p0_dxf.py
"""
import os
import sys
import warnings

import ezdxf
from ezdxf import path as ezpath
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

warnings.filterwarnings("ignore")

FLATTEN_M = 0.5     # arc chord tolerance

# Distance bands from a dual-carriageway centre line. A corridor within a few metres is
# ON the carriageway and may not be built; one 10-20 m away is in the verge or the
# service road beside it, which is normal and correct. Reporting a single tolerance
# turns the second into a false violation, so both bands are printed.
DUAL_BANDS_M = (4.0, 6.0, 8.0, 12.0, 20.0)
DUAL_VIOLATION_M = 6.0


def read_dxf(path):
    """Every LWPOLYLINE / LINE / POLYLINE in modelspace as a GeoDataFrame.

    ezdxf.path handles bulges, splines and 3D polylines alike, so arcs survive as arcs
    rather than being cut across.
    """
    doc = ezdxf.readfile(path)
    rows = []
    for e in doc.modelspace():
        if e.dxftype() not in ("LWPOLYLINE", "LINE", "POLYLINE", "SPLINE", "ARC"):
            continue
        try:
            pts = [(p.x, p.y) for p in ezpath.make_path(e).flattening(FLATTEN_M)]
        except Exception:
            continue
        # drop repeated vertices, which a CAD file collects freely
        clean = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - clean[-1][0]) > 1e-6 or abs(p[1] - clean[-1][1]) > 1e-6:
                clean.append(p)
        if len(clean) < 2:
            continue
        rows.append({"LAYER": e.dxf.layer, "DXFTYPE": e.dxftype(),
                     "geometry": LineString(clean)})
    return gpd.GeoDataFrame(rows, crs=C.EPSG)


def main():
    os.makedirs(C.OUT_SHP, exist_ok=True)
    os.makedirs(C.OUT_DOCS, exist_ok=True)

    g = read_dxf(C.DXF_TREATED)
    g["SRC"] = "draft"
    g["TIER_SRC"] = np.where(g.LAYER == C.DXF_LAYER_EXISTING, "existing_road",
                             np.where(g.LAYER == C.DXF_LAYER_FUTURE, "future_road", "other"))
    g["LEN_M"] = g.length

    print(f"read {len(g):,} lines, {g.LEN_M.sum()/1000:,.1f} km")
    print(g.groupby(["LAYER", "DXFTYPE"]).agg(n=("LEN_M", "size"),
                                              km=("LEN_M", lambda s: round(s.sum() / 1000, 1))))

    boundary = gpd.read_file(C.BOUNDARY).to_crs(C.EPSG).geometry.iloc[0]
    inside = g.intersects(boundary)
    print(f"\ninside the boundary: {inside.sum():,} of {len(g):,} lines, "
          f"{gpd.clip(g, boundary).length.sum()/1000:,.1f} km")

    # ---- defect 1: corridors sitting on a dual carriageway -------------------
    roads = gpd.read_file(C.ROADS).set_crs(C.EPSG, allow_override=True)
    dual = roads[roads["dual"].astype(str) == "1"]
    print(f"\ndual carriageways: {len(dual):,} lines, {dual.length.sum()/1000:,.1f} km")
    for tol in DUAL_BANDS_M:
        L = g.geometry.intersection(unary_union(dual.geometry.buffer(tol))).length
        mark = "  <- violation band" if tol == DUAL_VIOLATION_M else ""
        print(f"   within {tol:5.1f} m of a dual centre line: {(L > 5).sum():4d} lines, "
              f"{L.sum()/1000:6.2f} km{mark}")
        if tol == DUAL_VIOLATION_M:
            on_dual = L
    g["ON_DUAL_M"] = on_dual.values
    for lay, sub in g.groupby("TIER_SRC"):
        print(f"   {lay:<14s} {sub.ON_DUAL_M.sum()/1000:6.2f} km in the violation band")

    # ---- defect 2: the two layers duplicating each other ---------------------
    a = g[g.TIER_SRC == "existing_road"]
    b = g[g.TIER_SRC == "future_road"]
    dup_b = b.geometry.intersection(unary_union(a.geometry.buffer(10))).length.sum()
    dup_a = a.geometry.intersection(unary_union(b.geometry.buffer(10))).length.sum()
    print(f"\noverlap between the layers (10 m): future on existing "
          f"{dup_b/1000:.1f} km ({100*dup_b/b.LEN_M.sum():.1f} %), "
          f"existing on future {dup_a/1000:.1f} km ({100*dup_a/a.LEN_M.sum():.1f} %)")

    # ---- the gap: plots with no corridor within reach ------------------------
    # Measured from the plot POLYGON, not its centre point. A farm plot runs to 9 ha, so a
    # centre-point measure calls it unserved while its frontage is on the street; that
    # error alone moved 1,903 plots when it was corrected.
    plots = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)
    near = gpd.sjoin_nearest(plots[["geometry"]], g[["geometry"]], how="left",
                             max_distance=C.PLOT_SERVED_M, distance_col="D")
    near = near[~near.index.duplicated(keep="first")]
    served = near["D"].notna().values
    print(f"\nplots: {len(plots):,}   served by a drafted corridor within "
          f"{C.PLOT_SERVED_M:.0f} m: {served.sum():,} ({100*served.mean():.1f} %)   "
          f"UNSERVED: {(~served).sum():,}")

    plots_out = plots[["geometry"]].copy()
    plots_out["SERVED"] = served.astype(int)
    plots_out["D_CORR_M"] = near["D"].values
    plots_out.to_file(os.path.join(C.OUT_SHP, "W10_plots_served.shp"))

    g.to_file(os.path.join(C.OUT_SHP, "W10_corridors_drafted.shp"))
    print(f"\nwrote {os.path.join(C.OUT_SHP, 'W10_corridors_drafted.shp')}")
    print(f"wrote {os.path.join(C.OUT_SHP, 'W10_plots_served.shp')}")

    # a compact record of the run, so the numbers in the report trace to something
    rec = pd.DataFrame([
        ("lines read", len(g)),
        ("length drafted km", round(g.LEN_M.sum() / 1000, 1)),
        ("length inside boundary km", round(gpd.clip(g, boundary).length.sum() / 1000, 1)),
        ("existing_road km", round(a.LEN_M.sum() / 1000, 1)),
        ("future_road km", round(b.LEN_M.sum() / 1000, 1)),
        ("on dual carriageway km", round(on_dual.sum() / 1000, 2)),
        ("plots total", len(plots)),
        ("plots served", int(served.sum())),
        ("plots unserved", int((~served).sum())),
    ], columns=["item", "value"])
    rec.to_csv(os.path.join(C.OUT_RUN, "p0_dxf.csv"), index=False)


if __name__ == "__main__":
    main()
